"""Verify frozen Radar models and samples without training or operational imports."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from collections import Counter
import ast,csv,json,hashlib,importlib.metadata
import numpy as np
import joblib
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
EXP=ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921'
BASE=ROOT/'outputs/mucum-atualizacao-15h-2026-09-21'
TZ=timezone(timedelta(hours=-3))
def ep(s):
    d=datetime.fromisoformat(s);return (d if d.tzinfo else d.replace(tzinfo=TZ)).timestamp()
def iso(t):return datetime.fromtimestamp(float(t),TZ).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csvrows(p):return list(csv.DictReader(p.open()))
def num(s):return float(s) if s else np.nan
def dump(n,x):(OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
checks=[]
def check(name,ok,**detail):checks.append(dict(name=name,passed=bool(ok),**detail))
def eq(name,a,b,tol=0):
    a,b=np.asarray(a,dtype=float),np.asarray(b,dtype=float);same=a.shape==b.shape
    finite=np.isfinite(a)&np.isfinite(b) if same else np.array([],dtype=bool)
    delta=float(np.max(abs(a[finite]-b[finite]))) if finite.any() else 0.
    masks=same and np.array_equal(np.isnan(a),np.isnan(b)) and np.array_equal(np.isposinf(a),np.isposinf(b)) and np.array_equal(np.isneginf(a),np.isneginf(b))
    check(name,masks and delta<=tol,max_abs_difference=delta,finite_values=int(finite.sum()),tolerance=tol)

if not (EXP/'experiment.json').exists():raise SystemExit('Experiment is still incomplete; no fits or restarts performed.')
meta=json.loads((EXP/'experiment.json').read_text());proto=json.loads((EXP/'protocol.json').read_text())
for path,digest in meta['input_sha256'].items():check('input_hash:'+path,sha(Path(path))==digest)
for r in json.loads((EXP/'artifact-hashes.json').read_text()):check('artifact_hash:'+r['file'],sha(EXP/r['file'])==r['sha256'])
check('amended_protocol_snapshot',(EXP/'protocol.json').read_bytes()==(ROOT/'docs/radar-native-missing-runtime19-protocol.json').read_bytes())
check('amendment_runtime_explicit','1.9.1' in proto['runtime'] and 'not expected to reproduce' in proto['runtime'])
check('runtime_matches',all(importlib.metadata.version(k)==v for k,v in meta['runtime'].items()))
check('not_promoted',all(meta[k] is False for k in ['promoted','live_issuance','goal_achieved']))
# Extract only pure original array feature/shift functions from preserved snapshots.
def fn(path,name):return next(x for x in ast.parse(path.read_text()).body if isinstance(x,ast.FunctionDef) and x.name==name)
scope={'np':np}
exec(compile(ast.Module(body=[fn(EXP/'code/hydro_routing_fit.py','shift'),fn(EXP/'code/hydro_latency_forecast.py','telemetry_features')],type_ignores=[]),'<pure-features>','exec'),scope)
z=dict(np.load(BASE/'telemetria-latencia.npz'));qt=z['times'];raw={k[4:]:v for k,v in z.items() if k.startswith('raw:')};d={k:v for k,v in z.items() if k!='times' and not k.startswith('raw:')}
t,X,H,truth,phase,_=scope['telemetry_features'](qt,raw,d);s=dict(np.load(EXP/'features.npz'));complete=np.isfinite(X[:,:24]).all(axis=1)
eq('feature_times',t,s['times']);eq('base_level',H,s['base']);eq('hourly_truth',truth[phase],s['truth']);eq('complete24_mask',complete,s['complete24']);eq('telemetry_120',X,s['features'][:,:120])
check('hour_grid',np.all(np.diff(t)==3600));check('shape_180',s['features'].shape==(len(t),180))
# Independent fixed-index accumulation of the archived future hours, excludes origin.
cols=[]
for model in ['gfs_seamless','ecmwf_ifs025','icon_global']:
    p=BASE/'nwp-historical-icon.json' if model=='icon_global' else ROOT/f'outputs/mucum-propagacao-2026-09-21/raw/chuva-previsao-historica-{model}.json'
    locations=json.loads(p.read_text());check('five_weather_locations:'+model,len(locations)==5)
    for loc in locations:
        lookup={ep(at):float(v) if v is not None else np.nan for at,v in zip(loc['hourly']['time'],loc['hourly']['precipitation_previous_day1'])}
        hour=np.array([[lookup.get(at+h*3600,np.nan) for h in range(1,13)] for at in t])
        for window in [3,6,9,12]:cols.append(hour[:,:window].sum(axis=1))
W=np.column_stack(cols);eq('weather_60_original_order',W,s['features'][:,120:])
F=np.column_stack([X,W]);start=ep('2025-10-01T00:00:00-03:00');end=ep('2026-07-01T00:00:00-03:00');stop=ep('2026-09-21T00:00:00-03:00')
rows=csvrows(EXP/'predictions.csv');index={(r['phase'],r['origin'],int(r['nominal_lead_h'])):r for r in rows}
check('unique_keys',len(index)==len(rows)==meta['rows'])
configs=csvrows(BASE/'previsao-atualizada.csv');training={(r['phase'],r['family'],int(r['horizon_h'])):r for r in csvrows(EXP/'training.csv')}
expected_keys=set();members=[];coverage=[]
with threadpool_limits(limits=2):
  for h in range(1,13):
    target=scope['shift'](truth,-h*4)[phase];delta=target-H;finite=np.isfinite(H)&np.isfinite(target);weights=1+2*(abs(delta)>=1)+2*(target>=9)
    first=t+h*3600<start;second=(t>=start)&(t+h*3600<end)
    leaf,loss=ast.literal_eval(configs[h-1]['parameters'])
    for split,left,right in [('validation',start,end),('test',end,stop)]:
      scheduled=np.flatnonzero((t>=left)&(t+h*3600<right));apply=scheduled[np.isfinite(H[scheduled])]
      saved=[index[(split,iso(t[i]),h)] for i in scheduled];expected_keys.update((split,iso(t[i]),h) for i in scheduled)
      eq(f'base_rows:{split}:{h}',[num(r['base_m']) for r in saved],H[scheduled]);eq(f'target_rows:{split}:{h}',[num(r['actual_m']) for r in saved],target[scheduled])
      check(f'target_time_and_complete:{split}:{h}',all(ep(r['target_time'])==t[i]+h*3600 and (r['original_complete24']=='True')==complete[i] for r,i in zip(saved,scheduled)))
      for family in ['baseline','candidate']:
        mask=finite&(first if split=='validation' else (first|second))
        if family=='baseline':mask &=complete
        train=np.flatnonzero(mask);tr=training[split,family,h]
        check(f'membership_metadata:{split}:{family}:{h}',len(train)==int(tr['n']) and int((~complete[train]).sum())==int(tr['with_missing_first24']) and (t[train]+h*3600).max()==ep(tr['latest_training_target']) and (t[train]+h*3600).max()<ep(tr['cutoff_exclusive']))
        if split=='test' and family=='baseline':
          ordered=np.r_[np.flatnonzero(finite&complete&first),np.flatnonzero(finite&complete&second)]
          check(f'original_train_order_h{h}',np.array_equal(train,ordered))
        model=joblib.load(EXP/'models'/f'{split}-{family}-{h}.joblib')
        expected_params=dict(max_iter=180,max_leaf_nodes=leaf,min_samples_leaf=35,learning_rate=.055,l2_regularization=10,loss=loss,early_stopping=False,random_state=57)
        check(f'frozen_parameters:{split}:{family}:{h}',all(model.get_params()[k]==v for k,v in expected_params.items()) and model.n_iter_==180 and model.n_features_in_==180)
        check(f'tree_root_sample_counts:{split}:{family}:{h}',all(int(p[0].nodes[0]['count'])==len(train) for p in model._predictors))
        y=delta[train];w=weights[train]
        if loss=='squared_error':inter=np.average(y,weights=w)
        else:
          order=np.argsort(y);j=np.searchsorted(np.cumsum(w[order]),w.sum()*.5,side='left');inter=y[order[j]]
        eq(f'weighted_initial_intercept:{split}:{family}:{h}',model._baseline_prediction,[[inter]],1e-12)
        predicted=np.full(len(t),np.nan);predicted[apply]=model.predict(F[apply])+H[apply]
        eq(f'inference_all_scheduled:{split}:{family}:{h}',[num(r[family+'_m']) for r in saved],predicted[scheduled],1e-10)
        check(f'only_missing_base_blocks_prediction:{split}:{family}:{h}',np.array_equal(np.isfinite([num(r[family+'_m']) for r in saved]),np.isfinite(H[scheduled])))
        members.append(dict(phase=split,family=family,horizon_h=h,n=len(train),missing24=int((~complete[train]).sum()),indices_sha256=hashlib.sha256(train.tobytes()).hexdigest(),target_delta_sha256=hashlib.sha256(y.tobytes()).hexdigest(),weights_sha256=hashlib.sha256(w.tobytes()).hexdigest()))
      coverage.append(dict(phase=split,horizon_h=h,scheduled=len(scheduled),base_missing=int((~np.isfinite(H[scheduled])).sum()),target_missing=int((~np.isfinite(target[scheduled])).sum()),pairs=int(finite[scheduled].sum()),pairs_complete24=int((finite&complete)[scheduled].sum()),pairs_missing24=int((finite&~complete)[scheduled].sum()),target_missing_with_predictions=int((np.isfinite(H)&~np.isfinite(target))[scheduled].sum())))
check('all_scheduled_keys_preserved',expected_keys==set(index))
check('48_models',len(training)==48==meta['models_fitted'] and len(list((EXP/'models').glob('*.joblib')))==48)
old={(r['origin'],int(float(r['lead_h']))):r for r in csvrows(BASE/'retrospectivas-latencia.csv') if r['model']=='arvores_previsao_chuva' and r['phase']=='test'}
comparison=csvrows(EXP/'runtime-comparison.csv');compkeys={(r['origin'],int(r['horizon_h'])) for r in comparison}
check('all_archived_pairs_compared',len(comparison)==len(compkeys)==len(old)==meta['historical_test_predictions_compared'] and compkeys==set(old))
maxdiff=0.;comparison_ok=True
for r in comparison:
    key=(r['origin'],int(r['horizon_h']));oldvalue=float(old[key]['forecast_m']);newvalue=num(index['test',key[0],key[1]]['baseline_m']);delta=abs(newvalue-oldvalue)
    comparison_ok &= float(r['archived_runtime_forecast_m'])==oldvalue and float(r['current_runtime_refit_m'])==newvalue and float(r['abs_difference_m'])==delta
    maxdiff=max(maxdiff,delta)
check('runtime_differences_preserved',comparison_ok and maxdiff==meta['max_runtime_difference_m'] and meta['historical_test_predictions_exactly_reproduced']==(maxdiff==0),max_difference_m=maxdiff)
# Coverage only; no recomputation of the principal performance report.
for r in csvrows(EXP/'evaluation.csv'):
    rr=[x for x in rows if x['phase']==r['phase'] and int(x['nominal_lead_h'])==int(r['horizon_h']) and (r['population']=='full_schedule' or (x['original_complete24']=='True')==(r['population']=='complete24'))]
    obs=[x for x in rr if x['actual_m'] and (r['subset']=='all' or float(x['actual_m'])>=7)]
    paired=[x for x in obs if x[r['family']+'_m']]
    check('evaluation_coverage:'+':'.join(r[k] for k in ['phase','horizon_h','subset','population','family']),len(rr)==int(r['scheduled_rows']) and len(obs)==int(r['observed_targets']) and len(paired)==int(r['n']) and len(obs)-len(paired)==int(r['failures']))
dump('training-membership.json',members);dump('coverage.json',coverage)
dump('verification.json',dict(passed=all(r['passed'] for r in checks),checks=checks,rows=len(rows),models=48,limitations=[
'Models were loaded and inferred, never refitted. Training membership corroborated through source, metadata, root counts and weighted initial intercept; this does not reconstruct every split independently.',
'Amendment content and preserved artifacts inspected; exact pre-execution chronology relies on parent record, not a new signed receipt.',
'New runtime baseline is a refit, not an exactly reproduced historical forecast. Both compared families use the same operational runtime.',
'Source publication availability and datum remain assumptions. Previously inspected development; no promotion or prospective accuracy claim.'
]))
dump('artifact-hashes.json',[dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'])
print(json.dumps(dict(passed=all(r['passed'] for r in checks),checks=len(checks),failed=[r for r in checks if not r['passed']],rows=len(rows),models=48),ensure_ascii=False))
