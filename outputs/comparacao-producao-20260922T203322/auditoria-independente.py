"""Independent audit of already-downloaded production data; no network or product writes."""
from pathlib import Path
from datetime import datetime
import json, hashlib, math, collections

P = Path(__file__).resolve().parent
def stamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()

receipts = json.loads((P / 'r2-receipts.json').read_text())['receipts']
summary = json.loads((P / 'resumo.json').read_text())
expected = json.loads((P / 'comparacao-hora-a-hora.json').read_text())
pages = json.loads((P / 'd1-observacoes.json').read_text())
observations = [row for page in pages for row in page['results']]
assert len(observations) == 1055
assert all(page['meta']['rows_written'] == 0 and not page['meta']['changed_db'] for page in pages)

truth = {}
for row in observations:
    key = (row['station'], stamp(row['timestamp']))
    assert math.isfinite(row['level']) and abs(row['level'] - row['level_cm'] / 100) < 1e-12
    if key not in truth or row['source'] == 'SACE/SGB':
        truth[key] = row

issues = {}
copies = 0
key_counts = collections.Counter()
for receipt in receipts:
    body = (P / receipt['file']).read_bytes()
    assert hashlib.sha256(body).hexdigest() == receipt['sha256']
    key_counts[receipt['key'].split('/')[1]] += 1
    envelope = json.loads(body)
    for city in ['mucum', 'encantado', 'santa-tereza']:
        payload = envelope if city == 'mucum' else envelope.get(city)
        if not payload:
            continue
        generated, reference = stamp(payload['generatedAt']), stamp(payload['referenceAt'])
        assert payload.get('station', city) == city
        key = (city, generated, reference)
        essential = {name: payload[name] for name in ['generatedAt', 'referenceAt', 'observation', 'models']}
        modified = receipt.get('listed', {}).get('last_modified')
        stored = stamp(modified) if modified else None
        if key in issues:
            copies += 1
            assert issues[key]['essential'] == essential
            if stored is not None:
                issues[key]['stored'] = min(issues[key]['stored'], stored) if issues[key]['stored'] is not None else stored
            issues[key]['sources'].append(receipt['key'])
        else:
            issues[key] = dict(city=city, generated=generated, reference=reference,
                               payload=payload, essential=essential, stored=stored, sources=[receipt['key']])

latest = {}
for value in issues.values():
    key = value['city'], value['reference']
    if key not in latest or value['generated'] > latest[key]['generated']:
        latest[key] = value

codes = {'mucum': '86510000', 'encantado': '86720000', 'santa-tereza': '86472600'}
rows = {}
for value in latest.values():
    for model in value['payload']['models']:
        for point in model['points']:
            target = stamp(point['timestamp'])
            lead = (target - value['reference']) / 3600
            assert lead in [1, 2, 3, 4, 5, 6] and target > value['generated']
            observed = truth.get((codes[value['city']], target))
            rows[value['city'], value['reference'], lead] = dict(issue=value, point=point,
                                                               observed=observed, target=target)
assert len(rows) == len(expected) == 300
for reported in expected:
    key = reported['station'], stamp(reported['reference_at']), reported['nominal_lead_h']
    row = rows[key]
    issue, observed, point = row['issue'], row['observed'], row['point']
    assert stamp(reported['generated_at']) == issue['generated']
    assert stamp(reported['target_at']) == row['target']
    assert reported['forecast_m'] == point['level']
    assert abs(reported['actual_lead_h'] - (row['target'] - issue['generated']) / 3600) < 1e-12
    assert reported['observed_m'] == (observed['level'] if observed else None)
    assert reported['observed_source'] == (observed['source'] if observed else None)
    if observed:
        error = point['level'] - observed['level']
        assert abs(reported['error_m'] - error) < 1e-12
        assert abs(reported['abs_error_m'] - abs(error)) < 1e-12
        assert reported['status'] == 'matched'
        assert issue['stored'] is None or issue['stored'] < row['target']

metrics = {}
for city in codes:
    metrics[city] = {}
    for horizon in range(1, 7):
        group = [row for key, row in rows.items() if key[0] == city and key[2] == horizon and row['observed']]
        errors = [row['point']['level'] - row['observed']['level'] for row in group]
        count = len(errors)
        calculated = dict(n=count, mae_m=sum(map(abs, errors)) / count,
                          rmse_m=math.sqrt(sum(error * error for error in errors) / count),
                          bias_m=sum(errors) / count, max_abs_m=max(map(abs, errors)),
                          within_050m=sum(abs(error) <= .5 for error in errors),
                          hit_rate_050m=sum(abs(error) <= .5 for error in errors) / count)
        for name, value in calculated.items():
            assert abs(value - summary['metrics'][city][str(horizon)][name]) < 1e-12, (city, horizon, name)
        metrics[city][horizon] = calculated

largest = sorted([row for key, row in rows.items() if key[0] == 'mucum' and row['observed']],
                 key=lambda row: abs(row['point']['level'] - row['observed']['level']), reverse=True)[:3]
details = []
for row in largest:
    issue, observed, point = row['issue'], row['observed'], row['point']
    details.append(dict(generatedAt=issue['payload']['generatedAt'], referenceAt=issue['payload']['referenceAt'],
                        targetAt=point['timestamp'], prediction=point['level'], observed=observed['level'],
                        error=point['level'] - observed['level'], actualLeadH=(row['target'] - issue['generated']) / 3600,
                        objects=issue['sources'], d1_original=observed))
result = dict(status='passed', checked_raw_hashes=len(receipts), d1_readonly_confirmed=True,
              raw_counts=dict(key_counts), unique_station_issues=len(issues), removed_copies=copies,
              selected_station_rounds=len(latest), checked_rows=len(rows), checked_metric_groups=18,
              metric_tolerance=1e-12, metrics=metrics, largest_mucum_errors=details)
print(json.dumps(result, ensure_ascii=False, indent=2))
