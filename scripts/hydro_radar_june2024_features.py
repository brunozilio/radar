"""Prepare June2024 observed Radar research matrix; no fit or inference."""
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from hydro_hourly_forecast import ROOT, epoch, iso
from hydro_latency_forecast import telemetry_features
from hydro_model import asof
from hydro_rain_windows import observed_rain_windows
from hydro_routing_fit import shift

OUT = ROOT / 'outputs/radar-matriz-observada-junho2024-20260922'
HYDRO = ROOT / 'outputs/radar-insumos-observados-junho2024-20260922'
QI = ROOT / 'outputs/auditoria-qi-radar-junho2024-20260922'
PROTOCOL = ROOT / 'docs/radar-june2024-observed-features-protocol.json'
WEIGHTS = ROOT / 'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json'
DELAYS = ROOT / 'outputs/auditoria-latencias-chuva-20260921/latencies.json'
LEVELS = {'86510000': (900, 900), '86472000': (1800, 900), '86472600': (900, 900), '86500000': (1800, 900)}
PLANTS = {'julho': 'JIUHQJ', 'monte': 'JIUHMC', 'castro': 'JIUHCA'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def save(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def parse(row, field):
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError):
        return np.nan
    if row.get('CQ_' + field) != 'Dado aprovado' or not np.isfinite(value) or value < 0:
        return np.nan
    if field == 'ChuvaFinal' and value > 150:
        return np.nan
    return value / 100 if field == 'NivelFinal' else value


def run():
    OUT.mkdir(exist_ok=False)
    for item in json.loads((HYDRO / 'manifest.json').read_text())['files']:
        assert sha(HYDRO / item['file']) == item['sha256']
    for item in json.loads((QI / 'artifact-hashes.json').read_text()):
        assert sha(QI / item['file']) == item['sha256']
    protocol = json.loads(PROTOCOL.read_text())
    weights = json.loads(WEIGHTS.read_text())
    delays = {r['station']: r for r in json.loads(DELAYS.read_text())['stations']}
    paths = {PROTOCOL, Path(__file__), WEIGHTS, DELAYS, HYDRO / 'manifest.json', QI / 'artifact-hashes.json', QI / 'ons-references.json'}
    paths.update(ROOT / 'scripts' / name for name in ('hydro_hourly_forecast.py', 'hydro_latency_forecast.py', 'hydro_model.py', 'hydro_rain_windows.py', 'hydro_routing_fit.py'))
    paths.update(HYDRO / 'stations' / f'ana-{code}-all-qc.jsonl' for w in protocol['windows'] for code in delays)
    ons = []
    for ref in json.loads((QI / 'ons-references.json').read_text()):
        path = ROOT / ref['literal_csv']
        assert sha(path) == ref['csv_sha256']
        paths.add(path)
        ons += list(csv.DictReader(path.open()))
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}
    dump(OUT / 'preparation-plan.json', {'created_at_utc': datetime.now(timezone.utc).isoformat(), 'protocol': protocol, 'source_sha256': hashes})
    targets, rain_coverage, feature_coverage, traces = [], [], [], []
    summaries = []
    for window in protocol['windows']:
        label = window['origin_start']
        grid = np.arange(epoch(window['warmup_start'] + 'T00:00:00-03:00'), epoch(window['stop_exclusive'] + 'T00:00:00-03:00'), 900)
        assert len(grid) == 960
        raw, delayed, rain, level_sources = {}, {}, {}, {}
        for code in sorted(delays):
            rows = [json.loads(line) for line in (HYDRO / 'stations' / f'ana-{code}-all-qc.jsonl').read_text().splitlines()]
            times = np.array([epoch(r['DataHora']) for r in rows])
            assert np.all(np.diff(times) > 0)
            values = np.array([parse(r, 'ChuvaFinal') for r in rows])
            rw = observed_rain_windows(times, values, grid) if len(rows) else {h: (np.zeros(len(grid)), np.zeros(len(grid))) for h in (1, 3, 6, 12, 24, 48)}
            steps = int(delays[code]['shift_steps_15min'])
            assert steps == int(delays[code]['delay_seconds'] / 900)
            rain[code] = {h: (shift(v[0], steps), shift(v[1], steps)) for h, v in rw.items()}
            if code in LEVELS:
                level = np.array([parse(r, 'NivelFinal') for r in rows])
                level_sources[code] = (times, level)
                raw[code + ':H'] = asof(times, level, grid, max_age=0)
                lag, age = LEVELS[code]
                delayed[code + ':H'] = asof(times, level, grid - lag, max_age=age)
        for plant, code in PLANTS.items():
            rows = sorted([r for r in ons if r['id_reservatorio'].strip() == code], key=lambda r: r['din_instante'])
            times = np.array([epoch(r['din_instante']) for r in rows])
            assert np.all(np.diff(times) > 0)
            for key, field in [('Q', 'val_vazaodefluente'), ('I', 'val_vazaoafluente')]:
                values = np.array([float(r[field]) if r[field] else np.nan for r in rows])
                raw[plant + ':' + key] = asof(times, values, grid, max_age=5400)
                delayed[plant + ':' + key] = asof(times, values, grid - 3600, max_age=5400)
        for group in weights:
            for h in (1, 3, 6, 12, 24, 48):
                amount = sum(w * np.nan_to_num(rain[c][h][0], nan=0) for c, w in group['weights'].items())
                cover = sum(w * np.nan_to_num(rain[c][h][1], nan=0) for c, w in group['weights'].items())
                delayed[group['group'] + f':P{h}'] = np.where(cover >= .5, amount, np.nan)
                delayed[group['group'] + f':C{h}'] = cover
        times, features, base, truth, phase, _ = telemetry_features(grid, raw, delayed)
        keep = times >= epoch(label + 'T00:00:00-03:00')
        times, features, base, truth = times[keep], features[keep], base[keep], truth[phase][keep]
        assert features.shape == (168, 120) and np.isnan(features[:, 6:12]).all() and np.isnan(features[:, 18:24]).all()
        assert np.all(np.diff(times) == 3600) and not np.isinf(features).any()
        np.savez_compressed(OUT / f'{label}-features.npz', times=times, features=features, base=base, truth=truth, complete24=np.isfinite(features[:, :24]).all(axis=1))
        np.savez_compressed(OUT / f'{label}-quarter-hour.npz', times=grid, **{'raw:' + k: v for k, v in raw.items()}, **delayed)
        for code, (source_times, values) in level_sources.items():
            lag, max_age = LEVELS[code]
            for origin in times:
                query = origin - lag
                j = np.searchsorted(source_times, query, side='right') - 1
                age = query - source_times[j] if j >= 0 else None
                usable = j >= 0 and age <= max_age and np.isfinite(values[j])
                traces.append({'window': label, 'station': code, 'origin_assumed_brt': iso(origin), 'query_assumed_brt': iso(query), 'source_assumed_brt': iso(source_times[j]) if j >= 0 else None, 'age_seconds': age, 'usable': bool(usable), 'value_m': float(values[j]) if usable else None})
        for h in range(1, 13):
            actual = shift(truth, -h)
            valid = np.isfinite(base[:-h]) & np.isfinite(actual[:-h])
            targets.append({'window': label, 'horizon_h': h, 'scheduled_rows': len(times) - h, 'boundary_exclusions': h, 'observed_targets': int(np.isfinite(actual[:-h]).sum()), 'pairs': int(valid.sum()), 'missing_truth': int(np.isnan(actual[:-h]).sum()), 'observed_without_base': int((np.isfinite(actual[:-h]) & ~np.isfinite(base[:-h])).sum()), 'high_targets': int((actual[:-h] >= 7).sum()), 'high_pairs': int((valid & (actual[:-h] >= 7)).sum())})
        for group in weights:
            for h in (1, 3, 6, 12, 24, 48):
                cover = delayed[group['group'] + f':C{h}'][phase][keep]
                amount = delayed[group['group'] + f':P{h}'][phase][keep]
                rain_coverage.append({'window': label, 'group': group['group'], 'hours': h, 'origins': len(times), 'finite_precipitation': int(np.isfinite(amount).sum()), 'coverage_min': float(np.min(cover)), 'coverage_max': float(np.max(cover)), 'coverage_mean': float(np.mean(cover))})
        feature_coverage += [{'window': label, 'column': j, 'finite': int(np.isfinite(features[:, j]).sum()), 'missing': int(np.isnan(features[:, j]).sum())} for j in range(120)]
        summaries.append({'window': label, 'origins': 168, 'features': 120, 'finite_base': int(np.isfinite(base).sum()), 'approved_truth': int(np.isfinite(truth).sum()), 'missing_cells': int(np.isnan(features).sum()), 'complete24': 0})
    save(OUT / 'target-coverage.csv', targets)
    save(OUT / 'rain-coverage.csv', rain_coverage)
    save(OUT / 'feature-coverage.csv', feature_coverage)
    save(OUT / 'level-source-trace.csv', traces)
    names = [code + ':' + key for code in LEVELS for key in ['H', 'dH0.5', 'dH1', 'dH2', 'dH4', 'dH8']]
    names += [plant + ':' + key for plant in PLANTS for key in ['Q06', 'Q', 'I', 'dQ1', 'dQ2', 'dQ4', 'dQ8']]
    names += [g['group'] + ':' + key for g in weights for key in [v for h in (1, 3, 6, 12, 24, 48) for v in (f'P{h}', f'C{h}')] + ['P3lag3', 'P3lag6', 'P3lag12']]
    assert len(names) == 120
    dump(OUT / 'feature-catalog.json', names)
    for name, digest in hashes.items():
        assert sha(ROOT / name) == digest
    dump(OUT / 'preparation.json', {'windows': summaries, 'input_sha256': hashes, 'fits': 0, 'inferences': 0, 'operational_changes': 0, 'goal_achieved': False})
    dump(OUT / 'artifact-hashes.json', [{'file': str(p.relative_to(OUT)), 'sha256': sha(p)} for p in sorted(OUT.iterdir())])
    print(json.dumps(summaries), flush=True)


if __name__ == '__main__':
    run()
