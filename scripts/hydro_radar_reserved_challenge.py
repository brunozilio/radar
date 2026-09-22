"""One preregistered retrospective RADAR challenge; freeze inputs before inference."""
import argparse,csv,hashlib,importlib.metadata,json
from datetime import datetime,timedelta,timezone
from pathlib import Path
import joblib,numpy as np
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[1]
M=ROOT/'outputs/radar-matrizes-reservadas-2021-2022-20260922'
V=ROOT/'outputs/verificacao-radar-matrizes-reservadas-2021-2022-20260922'
FROZEN=ROOT/'outputs/congelamento-radar-reserva-2021-2022-20260922'
PROTOCOL=ROOT/'docs/radar-reserved-2021-2022-challenge-protocol.json'
OUT=ROOT/'outputs/experimento-radar-reservas-2021-2022-20260922'
FAMILIES=('control120','candidate120_plus2020')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def iso(t):return datetime.fromtimestamp(t,timezone(timedelta(hours=-3))).isoformat()
def num(x):return float(x) if np.isfinite(x) else None
def save(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def verify(folder):
    hh=json.loads((folder/'artifact-hashes.json').read_text())
    pairs=hh['files'].items() if isinstance(hh,dict) else [(r['file'],r['sha256']) for r in hh]
    for file,h in pairs:assert sha(folder/file)==h,str(folder/file)

def freeze():
    assert not OUT.exists(),'Do not overwrite an existing challenge.'
    for folder in (M,V,FROZEN):verify(folder)
    protocol=json.loads(PROTOCOL.read_text());assert sha(PROTOCOL)==sha(FROZEN/'protocol.json')
    # Independent matrix auditor must have completed before model access.
    report=json.loads((V/'verification.json').read_text());assert report['passed'] is True
    paths={PROTOCOL,Path(__file__)}
    for folder in (M,V,FROZEN):paths.update(p for p in folder.rglob('*') if p.is_file())
    for name,h in protocol['reference_sha256'].items():
        p=ROOT/name;assert sha(p)==h,name;paths.add(p)
    prep=json.loads((M/'preparation.json').read_text())
    for name,h in prep['input_sha256'].items():
        p=ROOT/name;assert sha(p)==h,name;paths.add(p)
    for r in protocol['model_records']:
        p=ROOT/r['file'];assert sha(p)==r['sha256'];paths.add(p)
    for year,n in ((2021,744),(2022,1464)):
        a=np.load(M/str(year)/'features.npz');assert a['features'].shape==(n,120) and np.all(np.diff(a['times'])==3600)
    runtime={k:importlib.metadata.version(k) for k in protocol['runtime']};assert runtime==protocol['runtime']
    OUT.mkdir();(OUT/'protocol.json').write_bytes(PROTOCOL.read_bytes());(OUT/'evaluation-code.py').write_bytes(Path(__file__).read_bytes())
    gate=dict(registered_at_utc=now(),protocol_sha256=sha(PROTOCOL),runtime=runtime,
        input_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},
        independent_audit=str((V/'verification.json').relative_to(ROOT)),
        planned_models=24,planned_prediction_rows=26340,planned_boundary_exclusions=156,
        planned_metric_rows=432,inference_started=False,training_allowed=False,promotion_allowed=False)
    dump(OUT/'pre-inference-manifest.json',gate)
    print(json.dumps(dict(gate=str(OUT/'pre-inference-manifest.json'),input_files=len(paths),registered_at=gate['registered_at_utc'],inference=False)))

def evaluate():
    gate=json.loads((OUT/'pre-inference-manifest.json').read_text())
    assert not (OUT/'inference-started.json').exists(),'Never silently repeat a started challenge; inspect state first.'
    for name,h in gate['input_sha256'].items():assert sha(ROOT/name)==h,name
    protocol=json.loads((OUT/'protocol.json').read_text());assert sha(OUT/'protocol.json')==gate['protocol_sha256']
    assert {k:importlib.metadata.version(k) for k in gate['runtime']}==gate['runtime']
    models={(r['family'],r['horizon_h']):r for r in protocol['model_records']}
    assert len(models)==24
    started=now();assert started>gate['registered_at_utc'];dump(OUT/'inference-started.json',dict(started_at_utc=started,pre_inference_manifest_sha256=sha(OUT/'pre-inference-manifest.json')))
    rows=[];boundary=[]
    for year,n in ((2021,744),(2022,1464)):
        data=dict(np.load(M/str(year)/'features.npz'));times,F,base,truth,complete=(data[k] for k in ('times','features','base','truth','complete24'))
        diag=list(csv.DictReader((M/str(year)/'qi-origin-diagnostics.csv').open()));assert len(diag)==n
        for h in range(1,13):
            scheduled=np.arange(n-h);target=truth[h:];bb=base[:n-h];apply=np.where(np.isfinite(bb))[0];pred={}
            for family in FAMILIES:
                m=models[family,h];path=ROOT/m['file'];assert sha(path)==m['sha256']
                model=joblib.load(path);assert model.n_features_in_==120 and model.get_params()==m['parameters']
                values=np.full(len(scheduled),np.nan);values[apply]=model.predict(F[apply])+bb[apply];assert np.isfinite(values[apply]).all()
                pred[family]=values
            boundary.append(dict(year=year,horizon_h=h,origins=n,scheduled_rows=n-h,boundary_excluded=h))
            for j in scheduled:
                assert times[j]+h*3600==times[j+h]
                rows.append(dict(year=year,origin=iso(times[j]),target_time=iso(times[j+h]),nominal_lead_h=h,base_m=num(bb[j]),actual_m=num(target[j]),
                    complete24=bool(complete[j]),control120_m=num(pred['control120'][j]),candidate120_plus2020_m=num(pred['candidate120_plus2020'][j]),
                    missing_base=not bool(np.isfinite(bb[j])),missing_truth=not bool(np.isfinite(target[j])),qi_reported_zero_used=diag[j]['uses_any_zero']=='True'))
            print('evaluated reserved year',year,'horizon',h,flush=True)
    rows.sort(key=lambda r:(r['year'],r['origin'],r['nominal_lead_h']));assert len(rows)==gate['planned_prediction_rows']
    assert sum(r['boundary_excluded'] for r in boundary)==gate['planned_boundary_exclusions']
    metrics=[]
    for period in ('2021','2022','pooled'):
        for h in range(1,13):
            for population in ('full_schedule','complete24','missing24'):
                pop=[r for r in rows if (period=='pooled' or str(r['year'])==period) and r['nominal_lead_h']==h and
                    (population=='full_schedule' or r['complete24']==(population=='complete24'))]
                for subset in ('all','level_ge_7m'):
                    observed=[r for r in pop if r['actual_m'] is not None and (subset=='all' or r['actual_m']>=7)]
                    for family in FAMILIES:
                        paired=[r for r in observed if r[family+'_m'] is not None]
                        e=np.array([r[family+'_m']-r['actual_m'] for r in paired]);ae=abs(e);hits=int((ae<=.5).sum())
                        metrics.append(dict(period=period,horizon_h=h,population=population,subset=subset,family=family,
                            scheduled_population_rows=len(pop),missing_truth_in_population=sum(r['actual_m'] is None for r in pop),observed_targets=len(observed),
                            paired_predictions=len(paired),missing_forecasts=len(observed)-len(paired),hits=hits,
                            paired_hit_fraction=hits/len(paired) if paired else None,observed_target_hit_fraction=hits/len(observed) if observed else None,
                            mae_m=float(ae.mean()) if paired else None,bias_m=float(e.mean()) if paired else None,
                            p98_abs_m=float(np.quantile(ae,.98)) if paired else None,max_abs_m=float(ae.max()) if paired else None))
    assert len(metrics)==gate['planned_metric_rows']
    save(OUT/'predictions.csv',rows);save(OUT/'evaluation.csv',metrics);save(OUT/'boundary-coverage.csv',boundary)
    for name,h in gate['input_sha256'].items():assert sha(ROOT/name)==h,name
    dump(OUT/'experiment.json',dict(started_at_utc=started,finished_at_utc=now(),unique_models=24,model_load_calls=48,models_fitted=0,
        prediction_rows=len(rows),metric_rows=len(metrics),boundary_exclusions=sum(r['boundary_excluded'] for r in boundary),
        training_membership_changed=False,input_files_unchanged=True,promoted=False,live_issuance=False,goal_achieved=False,
        uncertainty='Hourly samples and targets are correlated; no certified independent-event confidence claim. This historical challenge does not satisfy prospective counts, metadata or10independent floods.',
        reservation_status='First reserved-window results now generated. Any subsequent adjustment informed by them makes these windows development data, never a fresh independent comparison.',
        pre_inference_manifest_sha256=sha(OUT/'pre-inference-manifest.json')))
    dump(OUT/'artifact-hashes.json',[dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'])
    print(json.dumps(dict(output=str(OUT),rows=len(rows),metrics=len(metrics),models_fitted=0,goal_achieved=False)))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['freeze-inputs','evaluate']);args=ap.parse_args()
    with threadpool_limits(limits=2):
        freeze() if args.action=='freeze-inputs' else evaluate()
