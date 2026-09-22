from pathlib import Path
from datetime import datetime
import sys,json,hashlib,csv
sys.path.insert(0,str(Path.cwd()/'scripts'))
import hydro_prospective_ledger as ledger
out=Path(__file__).resolve().parent
run=Path('outputs/mucum-hourly-20260921T200235-0300').resolve()
root=Path('outputs/monitoramento-prospectivo').resolve()
records=ledger.read_records(root);bysha={r['sha256']:r for r in records}
checks={};errors=[]
def check(path,digest):
    path=Path(path);key=str(path)
    if key in checks:return
    ok=path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==digest
    checks[key]=ok
    if not ok:errors.append(key)
r=json.loads((run/'run-result.json').read_text());manifest=json.loads((run/'collection-manifest.json').read_text())
for x in manifest:
    if 'sha256' in x:check(run/'raw'/x['file'],x['sha256'])
artifacts=set();inputs=set();timing=[]
for f in r['forecasts']:
    rec=bysha[f['receipt_sha256']];packet=rec['payload'];assert rec['recorded_at']==f['recorded_at']
    for art in packet['model_artifacts']:
        check(art['path'],art['sha256']);check(root/art['blob'],art['sha256']);artifacts.add(art['path'])
    for sha in packet['input_receipts']:
        src=bysha[sha];p=src['payload'];check(root/p['blob'],p['blob_sha256']);inputs.add(sha)
        assert datetime.fromisoformat(src['recorded_at']) < datetime.fromisoformat(rec['recorded_at'])
    leads=[(datetime.fromisoformat(p['valid_at'])-datetime.fromisoformat(rec['recorded_at'])).total_seconds()/3600 for p in packet['points']]
    assert set(range(1,13))<=set(int(h) for h in leads)
    timing.append({'model':f['model_id'],'recorded_at':f['recorded_at'],'leads_h':leads})
index=json.loads((root/'history-index/current.json').read_text());hist=Path(index['directory']);check(hist/'manifest.json',index['manifest_sha256']);hm=json.loads((hist/'manifest.json').read_text())
for name,sha in hm['files'].items():check(hist/name,sha)
capture=json.loads((out/'capture-ana.json').read_text());old={}
for rec in records:
    if rec['sha256']==capture['sha256']:break
    if rec['kind']=='observation_receipt':
        for o in rec['payload'].get('observations',[]):old[(o['station_id'],o['datum_id'],o['valid_at'])]=o
obs=capture['payload']['observations'];new=[];revised=[]
for o in obs:
    key=(o['station_id'],o['datum_id'],o['valid_at'])
    if key not in old:new.append(o)
    elif old[key]!=o:revised.append({'previous':old[key],'current':o})
check(root/capture['payload']['blob'],capture['payload']['blob_sha256'])
rr=json.loads((out/'report-result.json').read_text());report=Path(rr['report']);cadence=json.loads((report/'cadence.json').read_text())
ages=list(csv.DictReader((run/'idades-fontes.csv').open()));ex=json.loads((run/'upstream-extrapolation.json').read_text());m=max(ex,key=lambda x:x['forecast_m3_s'])
audit={'audited_at':datetime.now().astimezone().isoformat(),'run':str(run),'runner':'duplicate suppressed; no new forecast','checks':{'files':len(checks),'model_artifacts':len(artifacts),'input_receipts':len(inputs),'history_files':len(hm['files']),'errors':errors},'collection':{'responses':len(manifest),'failures':[x for x in manifest if 'error' in x],'retries':[x for x in manifest if 'first_attempt_error' in x]},'pipeline_errors':[], 'original_cycle_pipeline_log':'No standalone pipeline log found in run directory; inspected collection failures, sealed cycle events and run-result instead','source_ages':ages,'stale_auxiliaries_over_180_minutes':[x for x in ages if float(x['delay_minutes'])>180],'history_index':index,'issuance':timing,'capture':{'receipt':capture['sha256'],'recorded_at':capture['recorded_at'],'observations':len(obs),'new':new,'revisions':revised,'latest':max(obs,key=lambda o:o['valid_at'])},'extrapolation':{'above_training_max':sum(x['above_training_max'] for x in ex),'outside_inputs':sum(bool(x['features_outside_training_range']) for x in ex),'total':len(ex),'maximum':m},'report':str(report),'summary':rr['summary'],'cadence':cadence}
(out/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
(out/'hash-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps({'checks':audit['checks'],'new':len(new),'revisions':len(revised),'status_counts':rr['summary']['status_counts'],'cadence':cadence},ensure_ascii=False,indent=2))
assert not errors
