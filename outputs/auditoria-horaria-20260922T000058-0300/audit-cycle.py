import contextlib, csv, hashlib, io, json, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/Users/brunozilio/Documents/radar')
sys.path.insert(0, str(ROOT/'scripts'))
import hydro_prospective_ledger as ledger

OUT = Path(__file__).parent
checks = []
def check(path, expected):
    path = Path(path)
    actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    checks.append({'path': str(path), 'expected': expected, 'actual': actual, 'ok': actual == expected})

with (OUT/'report-command.log').open('x') as log, contextlib.redirect_stdout(log):
    report = ledger.report(ledger.DEFAULT)
records = ledger.read_records(ledger.DEFAULT)
known = {r['sha256']: r for r in records}
summary = json.loads((report/'summary.json').read_text())
cadence = json.loads((report/'cadence.json').read_text())
report_text = (report/'report.md').read_text()
sources = []
forecasts = []
for run in sorted((ROOT/'outputs').glob('mucum-hourly-20260922T000*')):
    manifest = json.loads((run/'collection-manifest.json').read_text())
    for row in manifest:
        if 'sha256' in row:
            check(run/'raw'/row['file'], row['sha256'])
    info = {'run': str(run), 'requests': len(manifest), 'failures_by_source': dict(Counter(r['source'] for r in manifest if 'error' in r)),
            'failures': [r for r in manifest if 'error' in r], 'retries': [r for r in manifest if 'first_attempt_error' in r],
            'run_result_exists': (run/'run-result.json').exists(), 'source_ages_exist': (run/'idades-fontes.csv').exists()}
    if info['source_ages_exist']:
        info['source_ages'] = list(csv.DictReader((run/'idades-fontes.csv').open()))
    if info['run_result_exists']:
        result = json.loads((run/'run-result.json').read_text())
        info['run_result'] = result
        for f in result['forecasts']:
            rec = known[f['receipt_sha256']]
            pp = rec['payload']
            for sha in pp['input_receipts']:
                rr = known[sha]
                check(ledger.DEFAULT/rr['payload']['blob'], rr['payload']['blob_sha256'])
                assert ledger.timestamp(rr['recorded_at']) <= ledger.timestamp(rec['recorded_at'])
            for artifact in pp['model_artifacts']:
                check(artifact['path'], artifact['sha256'])
                check(ledger.DEFAULT/artifact['blob'], artifact['sha256'])
            forecasts.append({'recorded_at': rec['recorded_at'], 'reference_at': pp['reference_at'],
                'points': [{**point, 'actual_lead_h': (ledger.timestamp(point['valid_at'])-ledger.timestamp(rec['recorded_at'])).total_seconds()/3600} for point in pp['points']]})
    sources.append(info)

index = json.loads((ledger.DEFAULT/'history-index/current.json').read_text())
hist = Path(index['directory'])
check(hist/'manifest.json', index['manifest_sha256'])
hm = json.loads((hist/'manifest.json').read_text())
for filename, sha in hm['files'].items():
    check(hist/filename, sha)
if hm.get('parent_directory'):
    check(Path(hm['parent_directory'])/'manifest.json', hm['parent_manifest_sha256'])

capture = json.loads((OUT/'capture-ana.json').read_text())
check(ledger.DEFAULT/capture['payload']['blob'], capture['payload']['blob_sha256'])
old = {}
for rec in records:
    if rec['sha256'] == capture['sha256']:
        break
    if rec['kind'] == 'observation_receipt':
        for row in rec['payload']['observations']:
            old[(row['station_id'], row['valid_at'])] = row
fresh = capture['payload']['observations']
capture_summary = {'receipt': capture['sha256'], 'recorded_at': capture['recorded_at'], 'count': len(fresh),
    'new': sum((r['station_id'], r['valid_at']) not in old for r in fresh),
    'revised': sum((r['station_id'],r['valid_at']) in old and old[(r['station_id'],r['valid_at'])] != r for r in fresh),
    'latest': max(fresh, key=lambda x: x['valid_at'])}
rows = list(csv.DictReader((report/'verification.csv').open()))
diagnostics = [r for r in rows if r['status']=='matched' and r['evidence_kind']=='forecast_issue' and 1<=int(r['minimum_verified_lead_h'])<=12 and 'manual_revision' not in r['exclusion_reasons']]
new_pairs = [r for r in diagnostics if ledger.timestamp(r['valid_at']) >= ledger.timestamp('2026-09-21T23:00:00-03:00')]
started = [r for r in records if r['kind']=='cycle_started' and r['payload']['requested_reference']=='2026-09-22T00:00:00-03:00']
ids = {r['sha256'] for r in started}
terminals = [r for r in records if r['kind'] in ['cycle_completed','cycle_failed'] and r['payload']['cycle_sha256'] in ids]
research = ROOT/'outputs/pesquisa-mucum-nivelamento-20260922T030138Z'
research_manifest = json.loads((research/'manifest.json').read_text())
for item in research_manifest['files']:
    check(research/item['path'], item['sha256'])
audit = {'audited_at': datetime.now(timezone.utc).isoformat(), 'report': str(report), 'cycles_started': started, 'cycle_terminal_records': terminals,
    'source_runs': sources, 'forecasts': forecasts, 'history_index': index, 'capture': capture_summary, 'summary': summary,
    'new_diagnostic_pairs': new_pairs, 'hash_checks': checks, 'hash_failures': [r for r in checks if not r['ok']],
    'research': str(research), 'research_manifest': research_manifest,
    'limitations': ['Datum e fuso atuais não verificados; medições aprovadas pela origem não certificam esses metadados.',
                    'Meteorologia atual difere do treinamento; corte fixo 21/09/2026 00h BRT.',
                    'Nenhum ajuste neste evento, promoção, execução do modelo retirado ou publicação.']}
(OUT/'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'report': str(report), 'cycle_states': [r['kind'] for r in terminals],
    'runs': [{k:v for k,v in r.items() if k in ['run','requests','failures_by_source','run_result_exists','source_ages_exist']} for r in sources],
    'hash_checks':len(checks),'hash_failures':audit['hash_failures'], 'capture':capture_summary,
    'coverage': {k:cadence[k] for k in ['closed_windows','complete_windows','coverage_percent','status_counts']},
    'status_counts':summary['status_counts'], 'eligible':summary['goal_eligible_pairs'], 'new_pairs':new_pairs,
    'forecasts':forecasts},ensure_ascii=False,indent=2))
