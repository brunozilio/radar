"""Frozen, retrospective persistence comparator; never issues a forecast."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import hydro_prospective_ledger as ledger

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'outputs/monitoramento-prospectivo/reports/20260922T064302109000Z'
OUT = ROOT / 'outputs/diagnostico-persistencia-live-20260922'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    OUT.mkdir(exist_ok=False)
    source = json.loads((REPORT / 'summary.json').read_text())
    records = ledger.read_records(ledger.DEFAULT)[:source['records']]
    assert records[-1]['sha256'] == source['ledger_tip_sha256']
    by_hash = {r['sha256']: r for r in records}
    dump(OUT / 'plan.json', {
        'report': str(REPORT), 'as_of': source['created_at'],
        'ledger_tip': source['ledger_tip_sha256'],
        'scope': 'All regular Radar issues, real lead buckets 1..12, per version and lead.',
        'comparator': 'Constant last_observed.value, verified against a pre-issue source receipt.',
        'not_emitted': True, 'diagnostic_only': True, 'fit_count': 0,
        'threshold_m': 0.5, 'no_model_selection': True,
    })
    selected = {}
    receipt_hashes = set()
    for r in records:
        if r['kind'] != 'forecast_issue':
            continue
        p = r['payload']
        if ledger.is_retired_model(p['model_id']) or p.get('manual_revision'):
            continue
        anchor = p['last_observed']
        assert ledger.timestamp(anchor['last_time']) <= ledger.timestamp(r['recorded_at'])
        witnesses = []
        for receipt_id in p.get('input_receipts', []):
            receipt = by_hash[receipt_id]
            if receipt['kind'] != 'observation_receipt':
                continue
            assert ledger.timestamp(receipt['recorded_at']) <= ledger.timestamp(r['recorded_at'])
            q = receipt['payload']
            for obs in q.get('observations', []):
                if (obs['station_id'] == p['station_id'] and
                    ledger.timestamp(obs['valid_at']) == ledger.timestamp(anchor['last_time']) and
                    obs['quality'] == 'Dado aprovado' and obs['level_m'] == anchor['value']):
                    assert sha(ledger.DEFAULT / q['blob']) == q['blob_sha256']
                    witnesses.append(receipt_id)
                    receipt_hashes.add(receipt_id)
        selected[r['sha256']] = (r, witnesses)
    output = []
    for row in csv.DictReader((REPORT / 'verification.csv').open()):
        if row['forecast_record'] not in selected:
            continue
        lead = int(row['minimum_verified_lead_h'])
        if not 1 <= lead <= 12:
            continue
        r, witnesses = selected[row['forecast_record']]
        anchor = r['payload']['last_observed']
        result = {**row, 'anchor_time': anchor['last_time'],
                  'anchor_m': anchor['value'], 'anchor_source_verified': bool(witnesses),
                  'anchor_receipts': ','.join(witnesses),
                  'persistence_m': anchor['value'] if witnesses else None,
                  'persistence_abs_error_m': None, 'persistence_hit': None,
                  'radar_better_abs_error': None, 'radar_minus_persistence_abs_m': None}
        if row['status'] == 'matched' and witnesses:
            actual = float(row['observed_m'])
            radar_error = abs(float(row['forecast_m']) - actual)
            assert radar_error == float(row['abs_error_m'])
            baseline_error = abs(anchor['value'] - actual)
            result.update(persistence_abs_error_m=baseline_error,
                          persistence_hit=baseline_error <= .5,
                          radar_better_abs_error=radar_error < baseline_error,
                          radar_minus_persistence_abs_m=radar_error-baseline_error)
        output.append(result)
    with (OUT / 'pairs.csv').open('w') as f:
        w = csv.DictWriter(f, fieldnames=list(output[0])); w.writeheader(); w.writerows(output)
    groups = defaultdict(list)
    for r in output:
        groups[(r['model_version'], int(r['minimum_verified_lead_h']))].append(r)
    scores = []
    for (version, lead), rows in sorted(groups.items()):
        paired = [r for r in rows if r['persistence_abs_error_m'] is not None]
        n = len(paired)
        scores.append({'version': version, 'real_lead_bucket': lead, 'scheduled': len(rows),
                       'statuses': dict(Counter(r['status'] for r in rows)),
                       'missing_anchor_source': sum(not r['anchor_source_verified'] for r in rows),
                       'paired': n, 'unique_targets': len({r['valid_at'] for r in paired}),
                       'radar_hits': sum(float(r['abs_error_m']) <= .5 for r in paired),
                       'persistence_hits': sum(r['persistence_hit'] for r in paired),
                       'radar_mae_m': sum(float(r['abs_error_m']) for r in paired)/n if n else None,
                       'persistence_mae_m': sum(r['persistence_abs_error_m'] for r in paired)/n if n else None,
                       'radar_better': sum(r['radar_better_abs_error'] for r in paired),
                       'diagnostic_only': True, 'goal_eligible': False})
    dump(OUT / 'scorecard.json', scores)
    dump(OUT / 'sources.json', {
        'report_files': [{'path': str(REPORT / n), 'sha256': sha(REPORT / n)}
                         for n in ['summary.json', 'verification.csv']],
        'issue_receipts': list(selected), 'anchor_receipts': sorted(receipt_hashes),
        'ledger_code_sha256': sha(Path(ledger.__file__)),
        'observation_receipts': sorted({r['observation_record'] for r in output if r['observation_record']}),
    })
    (OUT / 'code.py').write_bytes(Path(__file__).read_bytes())
    dump(OUT / 'manifest.json', [{'file': str(p.relative_to(OUT)), 'sha256': sha(p)}
                                for p in sorted(OUT.iterdir()) if p.is_file()])
    print(json.dumps({'rows': len(output), 'groups': len(scores), 'issues': len(selected),
                      'verified_anchor_issues': sum(bool(x[1]) for x in selected.values()),
                      'pairs': sum(s['paired'] for s in scores)}))


if __name__ == '__main__':
    main()
