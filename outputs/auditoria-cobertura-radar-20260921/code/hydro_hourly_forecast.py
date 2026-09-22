"""Public data -> one experimental Radar forecast -> sealed prospective receipts.

No deployment. Historical cutoffs and hyperparameters are frozen; new evidence
does not silently tune them. The extra nominal hour covers a real 12-hour lead.
"""
from __future__ import annotations
import argparse, ast, csv, fcntl, hashlib, importlib.metadata, json, os, sys
from datetime import datetime, timedelta
from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy.linalg import solve
from threadpoolctl import threadpool_limits
import hydro_prospective_ledger as ledger
from hydro_hourly_collect import collect, ROOT, BASE, TZ, dump
import hydro_history

PREV=ROOT/'outputs/mucum-propagacao-2026-09-21'
CUTOFF='2026-09-21T00:00:00-03:00'
MODELS=['gfs_seamless','ecmwf_ifs025','icon_global']
GROUPS=['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def epoch(value):
    d=datetime.fromisoformat(value)
    return (d if d.tzinfo else d.replace(tzinfo=TZ)).timestamp()
def iso(t): return datetime.fromtimestamp(float(t),TZ).isoformat()
def rows(p): return list(csv.DictReader(p.open()))
def archive_path(model):
    return BASE/'nwp-historical-icon.json' if model=='icon_global' else PREV/'raw'/f'chuva-previsao-historica-{model}.json'

def weather_values(path,location,targets,field):
    item=json.loads(path.read_text())[location]
    if item.get('utc_offset_seconds') != -10800:
        raise ValueError(f'Unexpected weather timezone: {path}')
    if item['hourly_units'][field]!='mm': raise ValueError('Rain must be millimeters')
    h=item['hourly']; lookup={epoch(t):v for t,v in zip(h['time'],h[field])}
    a=np.array([lookup.get(float(t),np.nan) for t in targets],dtype=float)
    if np.any(a<0): raise ValueError('Negative rainfall')
    return a

def receive(root,path,kind='input_receipt',extra=None):
    blob,digest=ledger.store_blob(root,path.read_bytes(),path.suffix.lstrip('.') or 'bin')
    return ledger.append(root,kind,{'blob':blob,'blob_sha256':digest,'source_path':str(path.resolve()),**(extra or {})})['sha256']

def weather_features(times,out):
    columns=[]
    for model in MODELS:
        for loc in range(5):
            for window in [3,6,9,12]:
                future=times[:,None]+np.arange(1,window+1)*3600
                a=weather_values(archive_path(model),loc,future.ravel(),'precipitation_previous_day1').reshape(future.shape)
                # Keep historical inputs as archived previous-day forecasts. The
                # current row is explicitly versioned as a live-forecast candidate.
                a[-1]=weather_values(out/'raw'/f'weather-{model}.json',loc,future[-1],'precipitation')
                columns.append(a.sum(axis=1))
    result=np.column_stack(columns)
    if not np.isfinite(result[-1]).all(): raise ValueError('Missing live weather window')
    return result

def ridge_fit(X,y,train,alpha,weights):
    med=np.array([np.nanmedian(X[train,j]) if np.isfinite(X[train,j]).any() else 0 for j in range(X.shape[1])])
    x=np.column_stack([np.where(np.isfinite(X[train]),X[train],med),~np.isfinite(X[train])])
    mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale<1e-8]=1;x=(x-mean)/scale
    w=weights[train]/weights[train].mean();ym=np.average(y[train],weights=w)
    beta=solve(np.einsum('ni,n,nj->ij',x,w,x)+alpha*np.eye(x.shape[1]),np.einsum('ni,n,n->i',x,w,y[train]-ym),assume_a='pos')
    return dict(median=med,mean=mean,scale=scale,beta=beta,intercept=ym)

def ridge_predict(state,x):
    v=np.r_[np.where(np.isfinite(x),x,state['median']),~np.isfinite(x)]
    return float((v-state['mean'])/state['scale'] @ state['beta']+state['intercept'])

def calculate(out,root,reference,receipts,cycle_id=None,revision=None):
    os.environ.update(HYDRO_OUTPUT_DIR=str(out),HYDRO_ORIGIN=reference.isoformat(),HYDRO_HORIZON='13')
    from hydro_latency_forecast import prepare_current,telemetry_features
    from hydro_routing_fit import shift
    t,raw,delayed,ages=prepare_current()
    times,X,H,truth,phase,_=telemetry_features(t,raw,delayed)
    if times[-1]!=reference.timestamp(): raise ValueError('Feature origin mismatch')
    if not np.isfinite(H[-1]): raise ValueError('No current Muçum level')
    W=weather_features(times,out);features=np.column_stack([X,W])
    np.savez_compressed(out/'radar-features.npz',times=times,features=features,base=H,truth=truth[phase])
    for name in ['telemetria-latencia.npz','radar-features.npz']:
        receipts.append(receive(root,out/name))
    modeldir=out/'models';modeldir.mkdir()
    configs=rows(BASE/'previsao-atualizada.csv');points=[]
    cutoff=epoch(CUTOFF)
    for lead in range(1,15):
        target=shift(truth,-lead*4)[phase];delta=target-H
        valid=np.isfinite(H)&np.isfinite(target)&np.isfinite(X[:,:24]).all(axis=1)
        train=np.where(valid&(times+lead*3600<cutoff))[0]
        if len(train)<1000: raise ValueError('Insufficient historical training examples')
        leaf,loss=ast.literal_eval(configs[min(lead,12)-1]['parameters'])
        model=HistGradientBoostingRegressor(max_iter=180,max_leaf_nodes=leaf,min_samples_leaf=35,learning_rate=.055,l2_regularization=10,loss=loss,early_stopping=False,random_state=57)
        model.fit(features[train],delta[train],sample_weight=(1+2*(abs(delta)>=1)+2*(target>=9))[train])
        value=float(model.predict(features[-1:])[0]+H[-1])
        joblib.dump(model,modeldir/f'radar-{lead}.joblib')
        points.append({'valid_at':iso(times[-1]+lead*3600),'nominal_lead_h':lead,'level_m':value})
    print('Radar trained and calculated with frozen pre-event cutoff',flush=True)
    last=next(a for a in ages if a['source']=='86510000')
    artifacts=[{'path':str(p.resolve()),'sha256':sha(p)} for p in sorted(modeldir.iterdir())]
    code=[Path(__file__),*[ROOT/'scripts'/name for name in ['hydro_latency_forecast.py','hydro_rain_windows.py','hydro_routing_data.py','hydro_model.py','hydro_routing_fit.py','hydro_history.py','hydro-hourly-requirements.txt']]]
    artifacts.extend({'path':str(p.resolve()),'sha256':sha(p)} for p in code)
    for artifact in artifacts:
        artifact['blob'],digest=ledger.store_blob(root,Path(artifact['path']).read_bytes(),Path(artifact['path']).suffix.lstrip('.'))
        if digest!=artifact['sha256']: raise ValueError('Artifact changed during preservation')
    runtime={name:importlib.metadata.version(name) for name in ['numpy','scipy','numba','scikit-learn','shapely','pyproj','joblib','threadpoolctl']}
    version='hourly-live-weather-v1:'+sha(Path(__file__))[:16]
    results=[]
    for mid,pp in [('radar_arvores_live_candidate',points)]:
        packet={'station_id':'86510000','datum_id':'ANA:86510000:reference-unverified','model_id':mid,'model_version':version,'reference_at':reference.isoformat(),'produced_at':datetime.now(TZ).isoformat(),'training_cutoff':CUTOFF,'input_receipts':receipts,'model_artifacts':artifacts,'points':pp,'last_observed':last,'status':'experimental; no promotion or 98% claim','limitations':['Current meteorological forecasts differ from previous-day training predictors; new candidate version.','Nominal hours 13-14 use frozen hour-12 hyperparameters; no accuracy validation at those horizons.','Datum and legacy endpoint timezone not independently verified.']}
        packet['runtime_versions']=runtime
        packet['cycle_sha256']=cycle_id
        if revision:
            packet['manual_revision']={**revision,'previous_forecast':revision['previous_forecasts'][mid]}
        emission=datetime.now(TZ).timestamp()
        packet['points']=[p for p in pp if epoch(p['valid_at'])>emission]
        packet['omitted_elapsed_targets']=[p['valid_at'] for p in pp if epoch(p['valid_at'])<=emission]
        if not packet['points'] or epoch(packet['points'][-1]['valid_at'])-emission<12*3600: raise ValueError('Calculation no longer covers 12 real hours; recollect')
        dump(out/f'{mid}.json',packet)
        issue=ledger.register_forecast(root,packet);results.append({'model_id':mid,'receipt_sha256':issue['sha256'],'recorded_at':issue['recorded_at'],'points':packet['points']})
    return {'reference_at':reference.isoformat(),'last_observed':last,'forecasts':results,'status':'issued-experimental','goal_achieved':False}

def run():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path);ap.add_argument('--ledger',type=Path,default=ledger.DEFAULT);ap.add_argument('--weather-transition',type=Path)
    ap.add_argument('--revision-reason',help='Explicitly requested diagnostic revision; original hourly issues remain unchanged')
    ap.add_argument('--require-observation-at',help='Require this exact approved Muçum observation before calculating')
    args=ap.parse_args()
    if args.revision_reason and (not args.revision_reason.strip() or not args.require_observation_at or args.source):
        ap.error('Revision requires a reason, an exact observation time, and fresh collection')
    args.ledger.mkdir(parents=True,exist_ok=True)
    lock=(args.ledger/'.hourly.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    current_reference=datetime.now(TZ).replace(minute=0,second=0,microsecond=0).isoformat()
    previous={r['payload']['model_id']:r['sha256'] for r in ledger.read_records(args.ledger) if r['kind']=='forecast_issue' and r['payload']['reference_at']==current_reference and not r['payload'].get('manual_revision')}
    completed=set(previous)
    args.revision=None
    if args.revision_reason:
        if not {'radar_arvores_live_candidate'}<=completed:
            raise ValueError('Manual revision requires the original Radar hourly forecast')
        args.revision={'reason':args.revision_reason,'reference_at':current_reference,'previous_forecasts':previous,'required_observation_at':args.require_observation_at,'evaluation':'Diagnostic revision; excluded from scheduled accuracy sample to avoid double counting'}
    if {'radar_arvores_live_candidate'}<=completed and not args.revision:
        lock.close()
        print('Radar forecast for this reference hour already registered; not duplicating evidence.');return
    cycle=ledger.append(args.ledger,'cycle_started',{'requested_reference':current_reference,'manual_revision':args.revision})
    args.cycle_sha256=cycle['sha256']
    try:
        execute(args)
    except Exception as exc:
        ledger.append(args.ledger,'cycle_failed',{'cycle_sha256':cycle['sha256'],'error':type(exc).__name__+': '+str(exc)})
        raise
    else:
        ledger.append(args.ledger,'cycle_completed',{'cycle_sha256':cycle['sha256']})
        ledger.report(args.ledger)
    finally:
        lock.close()

def execute(args):
    now=datetime.now(TZ);out=args.source or ROOT/'outputs'/('mucum-hourly-'+now.strftime('%Y%m%dT%H%M%S%z'))
    if not args.source:
        out.mkdir();collect(out,now)
    manifest=json.loads((out/'collection-manifest.json').read_text())
    if args.require_observation_at:
        required_at=epoch(args.require_observation_at)
        observations=ledger.parse_ana((out/'raw/ana-86510000-fresh.xml').read_bytes(),'86510000','ANA:86510000:reference-unverified')
        if required_at>now.timestamp() or not any(epoch(o['valid_at'])==required_at and o['quality']=='Dado aprovado' and o['level_m'] is not None for o in observations):
            raise ValueError('Required exact approved Muçum observation unavailable')
    required=[r for r in manifest if r['source'] in ['ANA','CERAN','Open-Meteo']]
    if any('error' in r for r in required): raise ValueError('Required public source failed; no cached fallback')
    if any((now-datetime.fromisoformat(r['collected_at'])).total_seconds()>3600 for r in required): raise ValueError('Collection is stale')
    receipts=[]
    for item in manifest:
        if 'error' in item: continue
        path=out/'raw'/item['file']
        if sha(path)!=item['sha256']: raise ValueError('Collected data modified')
        extra={'collection':item}
        kind='input_receipt'
        if item['file']=='ana-86510000-fresh.xml':
            kind='observation_receipt';extra['observations']=ledger.parse_ana(path.read_bytes(),'86510000','ANA:86510000:reference-unverified')
        receipts.append(receive(args.ledger,path,kind,extra))
    # Retain the exact static inputs, including normalized ANA training arrays.
    static=[PREV/'telemetria.npz',PREV/'chuva-pesos.json',BASE/'previsao-atualizada.csv',*[archive_path(m) for m in MODELS],*sorted((PREV/'raw').glob('normalized-*.npz'))]
    for p in static: receipts.append(receive(args.ledger,p))
    history=hydro_history.build(out,args.ledger/'history-index',PREV,args.weather_transition)
    for p in sorted(history.iterdir()):receipts.append(receive(args.ledger,p))
    os.environ['HYDRO_HISTORY_DIR']=str(history.resolve())
    reference=datetime.now(TZ).replace(minute=0,second=0,microsecond=0)
    if args.revision and reference.isoformat()!=args.revision['reference_at']:
        raise ValueError('Revision crossed its reference hour; use the normal hourly runner')
    print(f'Calculating origin {reference.isoformat()} in {out}',flush=True)
    with threadpool_limits(limits=2): result=calculate(out,args.ledger,reference,receipts,args.cycle_sha256,args.revision)
    if args.revision: result['manual_revision']=args.revision
    dump(out/'run-result.json',result)
    dump(out/'run.json',{'started_at':now.isoformat(),'finished_at':datetime.now(TZ).isoformat(),'reference_time':reference.isoformat(),'status':'issued-experimental'})
    print(json.dumps({'output':str(out),'status':result['status'],'last_observed':result['last_observed']}),flush=True)

if __name__=='__main__':run()
