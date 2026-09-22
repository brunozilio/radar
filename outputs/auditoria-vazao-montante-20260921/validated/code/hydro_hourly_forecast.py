"""Public data -> two experimental forecasts -> sealed prospective receipts.

No deployment. Historical cutoffs and hyperparameters are frozen; new evidence
does not silently tune them. The extra nominal hour covers a real 12-hour lead.
"""
from __future__ import annotations
import argparse, ast, csv, fcntl, hashlib, importlib.metadata, importlib.util, json, os, sys
from datetime import datetime, timedelta
from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy.linalg import solve
from threadpoolctl import threadpool_limits
import hydro_prospective_ledger as ledger
from hydro_hourly_collect import collect, ROOT, BASE, TZ, dump
from hydro_flow_diagnostics import feature_names, attribution, outside_training_range

PREV=ROOT/'outputs/mucum-propagacao-2026-09-21'
HGE=ROOT/'experiments/hge-water-balance'
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

def calculate(out,root,reference,receipts):
    os.environ.update(HYDRO_OUTPUT_DIR=str(out),HYDRO_ORIGIN=reference.isoformat(),HYDRO_HORIZON='13')
    from hydro_latency_forecast import prepare_current,telemetry_features
    from hydro_mass_check import prepare_data
    from hydro_routing_fit import shift
    t,raw,delayed,ages=prepare_current()
    times,X,H,truth,phase,_=telemetry_features(t,raw,delayed)
    if times[-1]!=reference.timestamp(): raise ValueError('Feature origin mismatch')
    if not np.isfinite(H[-1]): raise ValueError('No current Muçum level')
    prepare_data()
    d=dict(np.load(out/'dados-roteamento.npz'));z=dict(np.load(out/'telemetria-latencia.npz'))
    W=weather_features(times,out);features=np.column_stack([X,W])
    np.savez_compressed(out/'radar-features.npz',times=times,features=features,base=H,truth=truth[phase])
    for name in ['telemetria-latencia.npz','dados-roteamento.npz','radar-features.npz']:
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
    ix=np.searchsorted(z['times'],times);fc=[]
    for key in ['julho:Q','julho:I','monte:Q','monte:I','castro:Q','castro:I','86500000:Q']:
        a=z[key][ix]/1000;fc.extend([a,a-shift(a,1),(a-shift(a,3))/3,(a-shift(a,6))/6])
    for group in GROUPS:
        for window in [3,6,12,24,48]:fc.append(z[group+f':P{window}'][ix]/100)
    F=np.column_stack(fc);future_q={};flow_diagnostics=[];alphas={(r['source'],int(r['lead_h'])):float(r['alpha']) for r in rows(BASE/'previsao-vazoes-montante.csv')}
    for source,key in [('julho','julho:Q'),('carreiro','86500000:Q')]:
        known=z[key][ix]/1000;future_q[source]={}
        if not np.isfinite(known[-1]): raise ValueError('Missing current upstream discharge')
        for k in range(14):
            target=shift(d[source],-k);delta=target-known
            train=np.where(np.isfinite(target)&np.isfinite(known)&(times+k*3600<cutoff))[0]
            state=ridge_fit(F,delta,train,alphas[(source,min(k,11))],1+2*(target>2))
            joblib.dump(state,modeldir/f'flow-{source}-{k}.joblib')
            future_q[source][k]=max(0,ridge_predict(state,F[-1])+known[-1])*1000
            contributions=attribution(state,F[-1],feature_names())
            maximum=float(np.max(target[train])*1000)
            flow_diagnostics.append({'source':source,'lead_h':k,'forecast_m3_s':future_q[source][k],'training_max_target_m3_s':maximum,'above_training_max':future_q[source][k]>maximum,'features_outside_training_range':outside_training_range(F[train],F[-1],feature_names()),'largest_linear_contributions':sorted(contributions,key=lambda r:abs(r['contribution_m3_s']),reverse=True)[:10],'note':'Describes extrapolation, not a physical cap or calibrated uncertainty interval.'})
    dump(out/'upstream-flow-forecasts.json',{s:{str(k):v for k,v in values.items()} for s,values in future_q.items()})
    dump(out/'upstream-extrapolation.json',flow_diagnostics)
    spec=importlib.util.spec_from_file_location('hge_hourly',HGE/'run.py');hge=importlib.util.module_from_spec(spec);spec.loader.exec_module(hge)
    p=next(x['parameters'] for x in json.loads((ROOT/'outputs/mucum-hge-experimental-2026-09-21/parametros.json').read_text()) if x['pet_mm_day_hypothesis']==3)
    pars=np.array([p[k] for k in hge.NAMES]);area=float(d['area'])
    alltimes=np.r_[times,times[-1]+np.arange(1,15)*3600];members=[]
    for model in MODELS:
        a=weather_values(archive_path(model),0,alltimes,'precipitation_previous_day1')
        live=weather_values(out/'raw'/f'weather-{model}.json',0,alltimes,'precipitation')
        # Preserve old historical forcing; use refreshed weather only for the
        # most recent seven days and future, without fitting on this event.
        use=(alltimes>=reference.timestamp()-7*86400)&np.isfinite(live);a[use]=live[use];members.append(a)
    arr=np.array(members);count=np.isfinite(arr).sum(axis=0)
    if np.any(count==0): raise ValueError('All weather members missing at an hour')
    rainmean=np.nansum(arr,axis=0)/count
    rain=d['amount']+np.maximum(0,1-d['coverage'])*rainmean[:len(times)]
    if not np.isfinite(rain).all() or np.any(rain<0): raise ValueError('Invalid completed rainfall')
    states,err=hge.simulate(rain,3.,pars,area,hge.initial_state(pars))
    future,err2=hge.simulate(rainmean[len(times):],3.,pars,area,states[-1].copy())
    if max(abs(err).max(),abs(err2).max())>1e-8: raise ValueError('Water balance failed')
    kernels=rows(BASE/'roteamento-vazao-pesos.csv')
    weights={source:np.array([float(r['weight']) for r in kernels if r['source']==label]) for source,label in [('julho','14 de Julho'),('carreiro','Passo Carreiro')]}
    if any(abs(w.sum()-1)>1e-6 for w in weights.values()): raise ValueError('Routing conservation failed')
    past=(d['X'][:,:12]@weights['julho']+d['X'][:,12:33]@weights['carreiro'])*1000+states[:,-1]
    last=next(a for a in ages if a['source']=='86510000');ot=epoch(last['last_time']);oi=np.searchsorted(z['times'],ot)
    baseq=float(z['raw:86510000:Q'][oi]);baseh=float(z['raw:86510000:H'][oi])
    if not np.isfinite(baseq) or baseh!=last['value']: raise ValueError('H/Q anchor mismatch')
    residual=baseq-float(np.interp(ot,times[-25:],past[-25:]));age=(times[-1]-ot)/3600
    rating=json.loads((BASE/'conferencia-balanco.json').read_text())['rating_parameters'];offset=baseh-float(hge.stage(baseq,rating));hp=[]
    for lead in range(1,15):
        total=0.
        for source,lags in [('julho',range(1,13)),('carreiro',range(4,25))]:
            for lag,w in zip(lags,weights[source]):
                k=lead-lag;value=future_q[source][k] if k>=0 else d[source][len(times)-1+k]*1000
                if not np.isfinite(value): raise ValueError('Missing routing input')
                total+=w*value
        q=total+future[lead-1,-1]+residual*np.exp(-(lead+age)/6)
        if not np.isfinite(q) or q<0: raise ValueError('Invalid forecast flow')
        hp.append({'valid_at':iso(times[-1]+lead*3600),'nominal_lead_h':lead,'level_m':float(hge.stage(q,rating)+offset)})
    np.savez_compressed(modeldir/'hge-state.npz',parameters=pars,state=states[-1],rating=rating,julho=weights['julho'],carreiro=weights['carreiro'])
    artifacts=[{'path':str(p.resolve()),'sha256':sha(p)} for p in sorted(modeldir.iterdir())]
    code=[Path(__file__),*[ROOT/'scripts'/name for name in ['hydro_latency_forecast.py','hydro_mass_check.py','hydro_rain_windows.py','hydro_routing_data.py','hydro_model.py','hydro_routing_fit.py','hydro_flow_diagnostics.py','hydro-hourly-requirements.txt']],out/'upstream-extrapolation.json',HGE/'run.py',HGE/'vendor/hydrological_model.py']
    artifacts.extend({'path':str(p.resolve()),'sha256':sha(p)} for p in code)
    for artifact in artifacts:
        artifact['blob'],digest=ledger.store_blob(root,Path(artifact['path']).read_bytes(),Path(artifact['path']).suffix.lstrip('.'))
        if digest!=artifact['sha256']: raise ValueError('Artifact changed during preservation')
    runtime={name:importlib.metadata.version(name) for name in ['numpy','scipy','numba','scikit-learn','shapely','pyproj','joblib','threadpoolctl']}
    version='hourly-live-weather-v1:'+sha(Path(__file__))[:16]
    results=[]
    for mid,pp in [('radar_arvores_live_candidate',points),('hge_arno_live_candidate',hp)]:
        packet={'station_id':'86510000','datum_id':'ANA:86510000:reference-unverified','model_id':mid,'model_version':version,'reference_at':reference.isoformat(),'produced_at':datetime.now(TZ).isoformat(),'training_cutoff':CUTOFF,'input_receipts':receipts,'model_artifacts':artifacts,'points':pp,'last_observed':last,'status':'experimental; no promotion or 98% claim','limitations':['Current meteorological forecasts differ from previous-day training predictors; new candidate version.','Nominal hours 13-14 use frozen hour-12 hyperparameters; no accuracy validation at those horizons.','Datum and legacy endpoint timezone not independently verified.','Frozen HGE PET=3 mm/day and correction tau=6h; point rainfall proxy.']}
        packet['runtime_versions']=runtime
        if mid=='hge_arno_live_candidate':
            packet['upstream_extrapolation']={'forecast_above_training_max_count':sum(r['above_training_max'] for r in flow_diagnostics),'flow_models_with_outside_features':sum(bool(r['features_outside_training_range']) for r in flow_diagnostics),'detail_path':str((out/'upstream-extrapolation.json').resolve()),'uncertainty_note':'PET/rainfall sensitivity does not cover the error of future upstream-flow estimates; flagged predictions remain in evaluation.'}
        emission=datetime.now(TZ).timestamp()
        packet['points']=[p for p in pp if epoch(p['valid_at'])>emission]
        packet['omitted_elapsed_targets']=[p['valid_at'] for p in pp if epoch(p['valid_at'])<=emission]
        if not packet['points'] or epoch(packet['points'][-1]['valid_at'])-emission<12*3600: raise ValueError('Calculation no longer covers 12 real hours; recollect')
        dump(out/f'{mid}.json',packet)
        issue=ledger.register_forecast(root,packet);results.append({'model_id':mid,'receipt_sha256':issue['sha256'],'recorded_at':issue['recorded_at'],'points':packet['points']})
    return {'reference_at':reference.isoformat(),'last_observed':last,'forecasts':results,'status':'issued-experimental','goal_achieved':False}

def run():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path);ap.add_argument('--ledger',type=Path,default=ledger.DEFAULT);args=ap.parse_args()
    args.ledger.mkdir(parents=True,exist_ok=True)
    lock=(args.ledger/'.hourly.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    current_reference=datetime.now(TZ).replace(minute=0,second=0,microsecond=0).isoformat()
    completed={r['payload']['model_id'] for r in ledger.read_records(args.ledger) if r['kind']=='forecast_issue' and r['payload']['reference_at']==current_reference}
    if {'radar_arvores_live_candidate','hge_arno_live_candidate'}<=completed:
        lock.close()
        print('Both forecasts for this reference hour already registered; not duplicating evidence.');return
    cycle=ledger.append(args.ledger,'cycle_started',{'requested_reference':current_reference})
    try:
        execute(args)
    except Exception as exc:
        ledger.append(args.ledger,'cycle_failed',{'cycle_sha256':cycle['sha256'],'error':type(exc).__name__+': '+str(exc)})
        raise
    else:
        ledger.append(args.ledger,'cycle_completed',{'cycle_sha256':cycle['sha256']})
    finally:
        lock.close()

def execute(args):
    now=datetime.now(TZ);out=args.source or ROOT/'outputs'/('mucum-hourly-'+now.strftime('%Y%m%dT%H%M%S%z'))
    if not args.source:
        out.mkdir();collect(out,now)
    manifest=json.loads((out/'collection-manifest.json').read_text())
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
    static=[PREV/'telemetria.npz',PREV/'chuva-pesos.json',BASE/'previsao-atualizada.csv',BASE/'previsao-vazoes-montante.csv',BASE/'roteamento-vazao-pesos.csv',BASE/'conferencia-balanco.json',ROOT/'outputs/mucum-hge-experimental-2026-09-21/parametros.json',*[archive_path(m) for m in MODELS],*sorted((PREV/'raw').glob('normalized-*.npz'))]
    for p in static: receipts.append(receive(args.ledger,p))
    reference=datetime.now(TZ).replace(minute=0,second=0,microsecond=0)
    print(f'Calculating origin {reference.isoformat()} in {out}',flush=True)
    with threadpool_limits(limits=2): result=calculate(out,args.ledger,reference,receipts)
    dump(out/'run-result.json',result)
    dump(out/'run.json',{'started_at':now.isoformat(),'finished_at':datetime.now(TZ).isoformat(),'reference_time':reference.isoformat(),'status':'issued-experimental'})
    ledger.report(args.ledger)
    print(json.dumps({'output':str(out),'status':result['status'],'last_observed':result['last_observed']}),flush=True)

if __name__=='__main__':run()
