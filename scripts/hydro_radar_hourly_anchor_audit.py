"""Audit a declared exact-hour anchor on raw 2018 Muçum records; no models."""
from __future__ import annotations

import bisect
import csv
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'outputs/pesquisa-janelas-ineditas-20260922'
OUT = ROOT / 'outputs/diagnostico-ancora-horaria-2018-20260922'
PROTOCOL = ROOT / 'docs/radar-2018-hourly-anchor-protocol.json'
LAGS = (0.5, 1, 2, 4, 8)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def save(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run():
    OUT.mkdir(exist_ok=False)
    protocol = json.loads(PROTOCOL.read_text())
    paths = [PROTOCOL, Path(__file__), SOURCE / 'manifest.json']
    paths += sorted((SOURCE / 'raw').glob('ana-*.xml'))
    source_hashes = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    dump(OUT / 'preparation-plan.json', {
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'protocol': protocol, 'source_sha256': source_hashes,
    })
    features, targets, metrics, traces = [], [], [], []
    checks = 0
    for path, (start, end) in zip(paths[3:], protocol['windows'], strict=True):
        raw = {}
        for el in ET.fromstring(path.read_bytes()).iter():
            if el.tag.split('}')[-1] != 'DadosHidrometereologicos':
                continue
            row = {c.tag.split('}')[-1]: c.text for c in el}
            assert row['CodEstacao'] == '86510000'
            at = datetime.fromisoformat(row['DataHora'])
            assert at.tzinfo is None and at not in raw
            value = float(row['NivelFinal']) / 100
            raw[at] = value if math.isfinite(value) and value >= 0 and row.get('CQ_NivelFinal') == 'Dado aprovado' else None
            checks += 2
        times = sorted(raw)
        first = datetime.fromisoformat(start)
        stop = datetime.fromisoformat(end) + timedelta(days=1)
        assert times == [first + timedelta(hours=i) for i in range(168)]
        checks += 1
        window = start
        local = []
        for origin in times:
            anchor = origin - timedelta(hours=1)
            base = raw.get(anchor)
            query = origin - timedelta(minutes=15)
            old_index = bisect.bisect_right(times, query) - 1
            old_at = times[old_index] if old_index >= 0 else None
            age = (query - old_at).total_seconds() / 60 if old_at is not None else None
            old_base = raw[old_at] if old_at is not None and age <= 15 else None
            f = {'window': window, 'origin_literal': origin.isoformat(),
                 'anchor_literal': anchor.isoformat(), 'level_m': base}
            for lag in LAGS:
                endpoint = anchor - timedelta(hours=lag)
                past = raw.get(endpoint)
                elapsed = (anchor - endpoint).total_seconds() / 3600
                assert endpoint < anchor < origin and elapsed == lag
                value = (base - past) / elapsed if base is not None and past is not None else None
                f[f'dH{lag}_m_per_h'] = value
                traces.append({'window': window, 'origin_literal': origin.isoformat(),
                               'anchor_literal': anchor.isoformat(), 'lag_h': lag,
                               'past_literal': endpoint.isoformat(), 'anchor_m': base,
                               'past_m': past, 'value_m_per_h': value})
                checks += 1
            f['current_contract_base_m'] = old_base
            f['current_contract_last_literal'] = old_at.isoformat() if old_at else None
            f['current_contract_age_minutes'] = age
            assert f['dH0.5_m_per_h'] is None and old_base is None
            checks += 1
            features.append(f)
            complete_hourly = all(f[f'dH{lag}_m_per_h'] is not None for lag in (1, 2, 4, 8)) and base is not None
            for h in range(1, 13):
                target_time = origin + timedelta(hours=h)
                if target_time >= stop:
                    continue
                actual = raw.get(target_time)
                row = {'window': window, 'origin_literal': origin.isoformat(), 'horizon_h': h,
                       'target_literal': target_time.isoformat(), 'base_m': base,
                       'actual_m': actual, 'complete_hourly_features': complete_hourly,
                       'current_contract_base_m': old_base}
                targets.append(row)
                local.append(row)
        for h in range(1, 13):
            population = [r for r in local if r['horizon_h'] == h]
            assert len(population) == 168 - h
            checks += 1
            for subset in ('all', 'level_ge_7m'):
                observed = [r for r in population if r['actual_m'] is not None and (subset == 'all' or r['actual_m'] >= 7)]
                pairs = [r for r in observed if r['base_m'] is not None]
                metrics.append({'window': window, 'horizon_h': h, 'subset': subset,
                                'scheduled_rows': len(population), 'boundary_exclusions': h,
                                'missing_truth': sum(r['actual_m'] is None for r in population),
                                'observed_targets': len(observed), 'anchor_target_pairs': len(pairs),
                                'missing_anchor_on_observed_target': len(observed)-len(pairs),
                                'complete_hourly_pairs': sum(r['complete_hourly_features'] for r in pairs),
                                'complete_six_field_pairs': 0, 'current_contract_pairs': 0})
    save(OUT / 'features.csv', features)
    save(OUT / 'targets.csv', targets)
    save(OUT / 'lookup-traces.csv', traces)
    save(OUT / 'coverage.csv', metrics)
    for name, digest in source_hashes.items():
        assert sha(ROOT / name) == digest
    dump(OUT / 'verification.json', {'checks': checks, 'source_hashes_verified': len(source_hashes),
         'origins': len(features), 'lookup_traces': len(traces), 'scheduled_targets': len(targets),
         'fits': 0, 'inferences': 0, 'operational_changes': 0, 'goal_achieved': False})
    dump(OUT / 'manifest.json', {'created_at_utc': datetime.now(timezone.utc).isoformat(),
         'files': [{'file': str(p.relative_to(OUT)), 'sha256': sha(p)} for p in sorted(OUT.iterdir())],
         'source_sha256': source_hashes})
    print(json.dumps({'output': str(OUT), 'checks': checks, 'metrics': len(metrics), 'targets': len(targets)}))


if __name__ == '__main__':
    run()
