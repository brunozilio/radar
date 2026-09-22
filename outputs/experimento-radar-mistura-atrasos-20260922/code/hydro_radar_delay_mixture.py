"""Predeclared delay-profile robustness experiment; no operational mutation."""
import ast,csv,hashlib,importlib.metadata,json
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import joblib,numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
import hydro_prospective_ledger as ledger
from hydro_hourly_forecast import ROOT,BASE,epoch,iso

SOURCES={
 'A':ROOT/'outputs/mucum-hourly-20260922T000704-0300',
 'B':ROOT/'outputs/mucum-hourly-20260922T010016-0300'}
OUT=ROOT/'outputs/experimento-radar-mistura-atrasos-20260922'
PROTOCOL=ROOT/'docs/radar-delay-profile-mixture-protocol.json'
FAMILIES=('profile_A_control','profile_B_control','mixed_profile_candidate')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def save(p,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def num(v):return float(v) if np.isfinite(v) else None
def target_for(truth,h):
    target=np.full_like(truth,np.nan);target[:-h]=truth[h:];return target
def evaluate(rows):
    groups=defaultdict(list)
    for r in rows:groups[r['phase'],r['profile'],r['nominal_lead_h']].append(r)
    result=[]
    for (phase,profile,h),group in sorted(groups.items()):
        for population in ('full_schedule','complete24','missing24'):
            pop=[r for r in group if population=='full_schedule' or r['complete24']==(population=='complete24')]
            for subset in ('all','level_ge_7m'):
                observed=[r for r in pop if r['actual_m'] is not None and (subset=='all' or r['actual_m']>=7)]
                for family in FAMILIES:
                    pairs=[r for r in observed if r[family+'_m'] is not None]
                    error=np.array([r[family+'_m']-r['actual_m'] for r in pairs]);ae=abs(error);hits=int((ae<=.5).sum())
                    result.append(dict(phase=phase,profile=profile,horizon_h=h,population=population,subset=subset,family=family,
                        scheduled_rows=len(pop),missing_truth=sum(r['actual_m'] is None for r in pop),observed_targets=len(observed),pairs=len(pairs),
                        failures=len(observed)-len(pairs),hits=hits,paired_hit_fraction=hits/len(pairs) if pairs else None,
                        observed_target_hit_fraction=hits/len(observed) if observed else None,mae_m=float(ae.mean()) if pairs else None,
                        bias_m=float(error.mean()) if pairs else None,p98_abs_m=float(np.quantile(ae,.98)) if pairs else None,max_abs_m=float(ae.max()) if pairs else None))
    return result

def run():
    assert not OUT.exists(),'Never overwrite a started experiment.'
    protocol=json.loads(PROTOCOL.read_text());assert protocol['planned_models']==72
    start,end,stop=[epoch(s) for s in ('2025-10-01T00:00:00-03:00','2026-07-01T00:00:00-03:00','2026-09-21T00:00:00-03:00')]
    records={r['sha256']:r for r in ledger.read_records(ledger.DEFAULT)};data={};paths={PROTOCOL,Path(__file__),BASE/'previsao-atualizada.csv',ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_prospective_ledger.py'}
    for profile,folder in SOURCES.items():
        result=json.loads((folder/'run-result.json').read_text());assert len(result['forecasts'])==1
        issue=records[result['forecasts'][0]['receipt_sha256']];assert issue['kind']=='forecast_issue' and issue['payload']['model_id']=='radar_arvores_live_candidate'
        path=folder/'radar-features.npz'
        receipt=next(records[h] for h in issue['payload']['input_receipts'] if records[h]['payload'].get('source_path')==str(path))
        assert sha(path)==receipt['payload']['blob_sha256']==sha(ledger.DEFAULT/receipt['payload']['blob'])
        d=dict(np.load(path));keep=d['times']<stop;data[profile]={k:v[keep] for k,v in d.items()}
        assert data[profile]['features'].shape==(12912,180)
        paths.update((path,folder/'run-result.json',folder/'radar_arvores_live_candidate.json'))
    for name in ('verificacao-variacao-treino-horario-20260922','diagnostico-variacao-treino-horario-20260922'):
        folder=ROOT/'outputs'/name
        manifest=json.loads((folder/'artifact-hashes.json').read_text())
        for item in manifest:assert sha(folder/item['file'])==item['sha256']
        paths.update(p for p in folder.iterdir() if p.is_file())
    t=data['A']['times'];truth=data['A']['truth'];XA=data['A']['features'];XB=data['B']['features'];ba=data['A']['base'];bb=data['B']['base']
    np.testing.assert_array_equal(t,data['B']['times']);np.testing.assert_array_equal(truth,data['B']['truth']);np.testing.assert_array_equal(XA[:,120:],XB[:,120:])
    assert np.all(np.diff(t)==3600) and not np.isinf(XA).any() and not np.isinf(XB).any()
    complete={s:np.isfinite(data[s]['features'][:,:24]).all(axis=1) for s in ('A','B')}
    assignment=np.random.Generator(np.random.PCG64(57)).integers(0,2,size=len(t),dtype=np.int8)
    mixed=np.where(assignment[:,None]==0,XA,XB);mb=np.where(assignment==0,ba,bb)
    configs=list(csv.DictReader((BASE/'previsao-atualizada.csv').open()))
    masks={}
    for h in range(1,13):
        target=target_for(truth,h)
        common=np.isfinite(ba)&np.isfinite(bb)&np.isfinite(target)&complete['A']&complete['B']
        first=t+h*3600<start;second=(t>=start)&(t+h*3600<end)
        masks[f'validation_h{h}']=common&first;masks[f'test_h{h}']=common&(first|second)
    runtime={n:importlib.metadata.version(n) for n in ('numpy','scipy','scikit-learn','joblib','threadpoolctl')}
    expected=ROOT/'outputs/experimento-radar-historico-2020-20260921/experiment.json';paths.add(expected)
    assert runtime==json.loads(expected.read_text())['runtime']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)}
    OUT.mkdir();(OUT/'models').mkdir();(OUT/'code').mkdir()
    (OUT/'protocol.json').write_bytes(PROTOCOL.read_bytes());(OUT/'code'/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    np.savez_compressed(OUT/'prepared-inputs.npz',times=t,truth=truth,features_A=XA,features_B=XB,base_A=ba,base_B=bb,complete_A=complete['A'],complete_B=complete['B'],assignment=assignment)
    np.savez_compressed(OUT/'training-masks.npz',**masks)
    prepared={name:sha(OUT/name) for name in ('prepared-inputs.npz','training-masks.npz')}
    dump(OUT/'pre-fit-manifest.json',dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(),input_sha256=hashes,prepared_sha256=prepared,
        runtime=runtime,planned_models=72,assignment_A=int((assignment==0).sum()),assignment_B=int((assignment==1).sum()),training_started=False))
    predictions=[];training=[]
    for h in range(1,13):
        target=target_for(truth,h);leaf,loss=ast.literal_eval(configs[h-1]['parameters']);assert configs[h-1]['model']=='arvores_previsao_chuva'
        for phase,left,right in (('validation',start,end),('test',end,stop)):
            ix=np.flatnonzero(masks[f'{phase}_h{h}']);assert len(ix)>=1000 and np.all(t[ix]+h*3600<left)
            scheduled=np.flatnonzero((t>=left)&(t+h*3600<right));values={}
            for family,X,base in ((FAMILIES[0],XA,ba),(FAMILIES[1],XB,bb),(FAMILIES[2],mixed,mb)):
                delta=target[ix]-base[ix];weights=1+2*(abs(delta)>=1)+2*(target[ix]>=9)
                model=HistGradientBoostingRegressor(max_iter=180,max_leaf_nodes=leaf,min_samples_leaf=35,learning_rate=.055,l2_regularization=10,loss=loss,early_stopping=False,random_state=57)
                model.fit(X[ix],delta,sample_weight=weights);joblib.dump(model,OUT/'models'/f'{phase}-{family}-{h}.joblib')
                training.append(dict(phase=phase,family=family,horizon_h=h,n=len(ix),distinct_origins=len(np.unique(t[ix])),
                    profile_A_rows=len(ix) if family==FAMILIES[0] else 0 if family==FAMILIES[1] else int((assignment[ix]==0).sum()),
                    profile_B_rows=len(ix) if family==FAMILIES[1] else 0 if family==FAMILIES[0] else int((assignment[ix]==1).sum()),
                    weights_sum=int(weights.sum()),targets_ge_7m=int((target[ix]>=7).sum()),latest_training_target=iso((t[ix]+h*3600).max()),cutoff_exclusive=iso(left),leaf_nodes=leaf,loss=loss))
                for profile in ('A','B'):
                    d=data[profile];apply=scheduled[np.isfinite(d['base'][scheduled])];v=np.full(len(t),np.nan)
                    v[apply]=model.predict(d['features'][apply])+d['base'][apply];assert np.isfinite(v[apply]).all();values[family,profile]=v
            for profile in ('A','B'):
                for i in scheduled:
                    r=dict(phase=phase,profile=profile,origin=iso(t[i]),target_time=iso(t[i]+h*3600),nominal_lead_h=h,
                        complete24=bool(complete[profile][i]),base_m=num(data[profile]['base'][i]),actual_m=num(target[i]))
                    r.update({family+'_m':num(values[family,profile][i]) for family in FAMILIES});predictions.append(r)
            print('delay mixture completed',phase,h,flush=True)
    predictions.sort(key=lambda r:(r['phase'],r['profile'],r['origin'],r['nominal_lead_h']))
    assert len(predictions)==204168 and len(training)==72
    metrics=evaluate(predictions);assert len(metrics)==864
    save(OUT/'predictions.csv',predictions);save(OUT/'evaluation.csv',metrics);save(OUT/'training.csv',training)
    for path,digest in hashes.items():assert sha(ROOT/path)==digest,path
    for path,digest in prepared.items():assert sha(OUT/path)==digest,path
    dump(OUT/'experiment.json',dict(finished_at_utc=datetime.now(timezone.utc).isoformat(),models_fitted=72,scheduled_profile_rows=len(predictions),
        distinct_schedule_rows=len(predictions)//2,metrics=len(metrics),runtime=runtime,input_sha256=hashes,prepared_sha256=prepared,
        training_membership_common=True,samples_duplicated=False,seed_search=False,independent_test=False,promoted=False,live_issuance=False,goal_achieved=False))
    dump(OUT/'artifact-hashes.json',[dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file()])
    print(json.dumps(dict(output=str(OUT),models=72,metrics=864,goal_achieved=False)))

if __name__=='__main__':
    with threadpool_limits(limits=2):run()
