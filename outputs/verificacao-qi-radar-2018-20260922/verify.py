import csv, hashlib, json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / 'outputs/auditoria-qi-radar-2018-20260922'
OUT = Path(__file__).resolve().parent
assert not (OUT / 'verification.json').exists()
ids = {'JIUHQJ', 'JIUHMC', 'JIUHCA'}
checks = 0
source_rows = []
for receipt in json.loads((P / 'source-manifest.json').read_text()):
    raw = P / receipt['file']
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == receipt['sha256']
    with raw.open(encoding='utf-8-sig', newline='') as stream:
        selected = [dict(r, source_file=str(raw.relative_to(ROOT)), source_record_index=str(i))
                    for i, r in enumerate(csv.DictReader(stream, delimiter=';'))
                    if r['id_reservatorio'].strip() in ids]
    literal = list(csv.DictReader((P / ('ceran-' + receipt['month'] + '-source-values.csv')).open()))
    assert selected == literal
    source_rows += selected
    checks += len(selected) + 1
source = {(r['id_reservatorio'], r['din_instante']): r for r in source_rows}
by_plant = {code: [(datetime.fromisoformat(r['din_instante']), r) for r in source_rows if r['id_reservatorio'] == code] for code in ids}
traces = list(csv.DictReader((P / 'lag-source-trace.csv').open()))
for trace in traces:
    query = datetime.fromisoformat(trace['query_literal'])
    eligible = [(t, r) for t, r in by_plant[trace['plant']] if t <= query]
    at, row = max(eligible, key=lambda item: item[0])
    assert row['din_instante'] == trace['source_literal']
    assert row['source_file'] == trace['source_file'] and row['source_record_index'] == trace['source_record_index']
    age = (query - at).total_seconds()
    assert age == float(trace['age_seconds']) and age <= 5400
    field = 'val_vazaodefluente' if trace['variable'] == 'Q' else 'val_vazaoafluente'
    assert float(trace['value_m3s']) == float(row[field])
    assert at <= query < datetime.fromisoformat(trace['origin_literal'])
    checks += 5
missing_template = []
for code in sorted(ids):
    times = {datetime.fromisoformat(r['din_instante']) for r in source_rows if r['id_reservatorio'] == code and r['din_instante'].startswith('2018-10')}
    expected = {datetime(2018, 10, d, h) for d in range(1, 32) for h in range(1, 24)} | {datetime(2018, 10, d, 23, 59) for d in range(1, 32)}
    assert expected - times == {datetime(2018, 10, 20, 23, 59)} and not times - expected
    missing_template.append({'plant': code, 'missing_literal_label': '2018-10-20 23:59:00', 'inside_study_windows': False})
    checks += 1
for entry in json.loads((P / 'artifact-hashes.json').read_text()):
    assert hashlib.sha256((P / entry['file']).read_bytes()).hexdigest() == entry['sha256']
    checks += 1
result = {'checks': checks, 'raw_rows_reconstructed': len(source_rows), 'lookups_verified': len(traces),
          'missing_against_daily_literal_label_template': missing_template,
          'source_manifest_sha256': hashlib.sha256((P / 'artifact-hashes.json').read_bytes()).hexdigest(),
          'fits': 0, 'inferences': 0, 'goal_achieved': False}
(OUT / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
