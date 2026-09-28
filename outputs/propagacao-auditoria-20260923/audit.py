"""Independent read-only numerical audit. No model imports, fitting or writes to experiment."""
from pathlib import Path
from datetime import datetime, timezone
import csv, json, hashlib, re
from collections import defaultdict
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
RUN=ROOT/'outputs/propagacao-modelo-20260923'
manifest=json.loads((RUN/'execution-manifest.json').read_text())
model=json.loads((RUN/'model.json').read_text())
report=json.loads((RUN/'evaluation.json').read_text())
checks=[]
def check(label,condition,details=None):
 checks.append({'check':label,'passed':bool(condition),'details':details})
 if not condition: print('FAIL',label,details)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stamp(s):return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def iso(s):return datetime.fromtimestamp(float(s),timezone.utc).isoformat()
def same(a,b):
 if a is None or b is None:return a is b
 return bool(np.isclose(a,b,rtol=1e-10,atol=1e-10))
for rel,sha in manifest['files'].items():check('frozen_input_hash:'+rel,digest(ROOT/rel)==sha)
source_manifest=json.loads((ROOT/'outputs/propagacao-dados-20260923/manifest.json').read_text())
for s in source_manifest['sources']:check('raw_source_hash:'+s['path'],digest(Path(s['path']))==s['sha256'])
check('predictions_sha256',digest(RUN/'predictions.csv')==(RUN/'predictions.sha256').read_text().split()[0])
check('model_dataset_digest',model['dataset']['npzSha256']==digest(ROOT/'outputs/propagacao-dados-20260923/exact-hour-level-flow.npz'))
loaded=np.load(ROOT/'outputs/propagacao-dados-20260923/exact-hour-level-flow.npz',allow_pickle=False)
times=loaded['times']; data={k:loaded[k].copy() for k in loaded.files if k!='times'}
check('hourly_grid',np.all(np.diff(times)==3600) and np.all(times%3600==0))
lookup={float(t):i for i,t in enumerate(times)}
keys=model['requiredSources']; local=data['86510000:H']; flows=[k for k in keys if not k.endswith(':H')]
for k in flows:data[k][data[k]<0]=np.nan
def delay(x,n):
 a=np.full_like(x,np.nan,dtype=float)
 if n==0:return x.copy()
 if n>0:a[n:]=x[:-n]
 else:a[:n]=x[-n:]
 return a
trans={k:np.log1p(v/1000) if k in flows else v for k,v in data.items()}
def feature(name):
 parts=name.split(':');base=trans[':'.join(parts[:2])];lag=0;slope=None
 for part in parts[2:]:
  if part.startswith('lag'):lag=int(part[3:])
  elif part.startswith('slope'):slope=int(part[5:])
  else:raise AssertionError(part)
 return delay(base,lag) if slope is None else (delay(base,lag)-delay(base,lag+slope))/slope
names=model['horizons'][0]['featureNames']; X=np.column_stack([feature(n) for n in names])
contemp=X[:,[i for i,n in enumerate(names) if ':lag' not in n]]
matrices={'lagged':X,'contemporaneous':contemp}
complete=np.isfinite(X).all(axis=1)&np.isfinite(contemp).all(axis=1)&np.logical_and.reduce([np.isfinite(data[k]) for k in keys])
check('missing_origin_count',int((~complete).sum())==report['missingOriginsExcluded'])
trend=(local-delay(local,2))/2
cuts=[stamp(model[k]) for k in ['trainingCutoff','validationCutoff','testCutoff']]
embargo=33*3600
check('cutoffs_and_embargo',cuts==[stamp('2025-10-01T00:00:00-03:00'),stamp('2026-07-01T00:00:00-03:00'),stamp('2026-09-21T00:00:00-03:00')] and model['embargoHours']==33)
def phase_mask(h,phase):
 target=times+h*3600
 return {'train':target<cuts[0],'validation':(times>=cuts[0]+embargo)&(target<cuts[1]),'test':(times>=cuts[1]+embargo)&(target<cuts[2]),'stress_current':times>=cuts[2]}[phase]
# Recompute all lag diagnostics on training differences, without fitting coefficients.
lag_map={}
for source in [k for k in keys if k!='86510000:H']:
 scores=[];dy=local-delay(local,1);dx=trans[source]-delay(trans[source],1)
 for lag in range(25):
  z=delay(dx,lag);mask=(times<cuts[0])&np.isfinite(dy)&np.isfinite(z)
  corr=float(np.corrcoef(z[mask],dy[mask])[0,1]) if mask.sum()>=48 and np.std(z[mask])>1e-10 and np.std(dy[mask])>1e-10 else None
  ref=next(r for r in report['lagCorrelations'] if r['source']==source and r['lagHours']==lag)
  check(f'lag:{source}:{lag}',int(mask.sum())==ref['pairs'] and same(corr,ref['correlation']))
  if corr is not None and corr>0:scores.append((corr,-lag,int(mask.sum())))
 best=max(scores) if scores else None
 selected=model['lags'][source]
 check('selected_lag:'+source,selected['lagHours']==(-best[1] if best else 0) and same(selected['correlation'],best[0] if best else None))
 lag_map[source]=selected
membership={};coverage=[];normal_equations=[]
for h in range(1,7):
 target=delay(local,-h);target_known=np.isfinite(target)
 membership[h]={}
 for phase in ['train','validation','test','stress_current']:
  scheduled=phase_mask(h,phase);ids=np.flatnonzero(scheduled&complete&target_known)
  membership[h][phase]=ids
  check(f'membership:{h}:{phase}',ids.tolist()==report['rowMembershipByHorizon'][str(h)][phase])
  natural={family:np.isfinite(xx).all(axis=1) for family,xx in matrices.items()}
  natural.update(persistence=np.isfinite(local),local_trend_2h=np.isfinite(local)&np.isfinite(trend))
  for family,ready in natural.items():
   count=int((scheduled&ready&target_known).sum())
   check(f'natural_availability:{h}:{phase}:{family}',count==report['naturalAvailabilityByHorizon'][str(h)][family][phase])
   coverage.append({'h':h,'phase':phase,'model':family,'scheduled_origins':int(scheduled.sum()),'exact_targets_known':int((scheduled&target_known).sum()),'targets_beyond_snapshot':int((scheduled&(times+h*3600>times[-1])).sum()),'targets_missing_inside_snapshot':int((scheduled&~target_known&(times+h*3600<=times[-1])).sum()),'natural_input_ready':int((scheduled&ready).sum()),'natural_verified_pairs':count,'intersection_verified_pairs':int(len(ids)),'intersection_input_ready':int((scheduled&complete).sum())})
 # Alpha/family minima reconstructed from recorded pre-test validation scores.
 choices=[]
 for family in matrices:
  candidates=[r for r in report['selection'] if r['h']==h and r['family']==family]
  check(f'alpha_grid:{h}:{family}',sorted(r['alpha'] for r in candidates)==[1,10,100,1000])
  for r in candidates:
   m=r['validationMetrics'];s=m['mae_m']+.5*(m['rapid_rise_mae_m'] or 0)+.5*(m['high_water_mae_m'] or 0)
   check(f'selection_score:{h}:{family}:{r["alpha"]}',same(s,r['validationScore']))
  best=min(candidates,key=lambda r:(r['validationScore'],-r['alpha']))
  choices.append(best)
 best=min(choices,key=lambda r:(r['validationScore'],r['family']))
 entry=model['horizons'][h-1];p=entry['parameters']
 check(f'family_alpha_selection:{h}',best['family']==entry['family'] and best['alpha']==p['alpha'] and same(best['validationScore'],entry['validationScore']))
 check(f'feature_order:{h}',entry['featureNames']==names)
 # Verify stored coefficients satisfy ridge normal equations. No solve or refit.
 ids=np.r_[membership[h]['train'],membership[h]['validation']];xx=X[ids];y=target[ids]-local[ids]
 mean=xx.mean(axis=0);scale=xx.std(axis=0);scale[scale<1e-8]=1
 check(f'preprocessing:{h}',np.allclose(mean,p['mean'],atol=1e-10) and np.allclose(scale,p['scale'],atol=1e-10) and same(y.mean(),p['intercept']) and len(ids)==p['trainingRows'])
 z=(xx-mean)/scale;beta=np.asarray(p['beta']);rhs=z.T@(y-p['intercept']);lhs=(z.T@z+p['alpha']*np.eye(len(beta)))@beta
 relative=float(np.max(abs(lhs-rhs))/max(1,np.max(abs(rhs))))
 check(f'ridge_normal_equation:{h}',relative<1e-10,relative)
 normal_equations.append({'h':h,'maximum_relative_equation_residual':relative,'fit_performed':False})
 # Source ranges are original train+validation only.
 check(f'training_ranges:{h}',np.allclose(xx.min(axis=0),p['featureMin']) and np.allclose(xx.max(axis=0),p['featureMax']))
rows=list(csv.DictReader((RUN/'predictions.csv').open()));groups=defaultdict(list);seen=set();replays=[]
for row in rows:
 h=int(row['h']);origin=stamp(row['origin']);target_time=stamp(row['target_time']);i=lookup.get(origin);phase=row['phase'];family=row['model']
 identity=(h,phase,family,origin)
 if identity in seen:raise AssertionError('duplicate prediction '+str(identity))
 seen.add(identity)
 if i is None or target_time!=origin+h*3600 or i+h>=len(times):raise AssertionError('inexact time '+str(identity))
 base=float(row['base_m']);actual=float(row['actual_m']);pred=float(row['forecast_m'])
 if not (same(base,local[i]) and same(actual,local[i+h]) and np.isfinite(pred)):raise AssertionError('unaligned value '+str(identity))
 row.update(h=h,index=i,base_m=base,actual_m=actual,forecast_m=pred)
 groups[(h,phase,family)].append(row)
check('unique_exact_prediction_rows',len(seen)==len(rows),len(rows))
def summary(rr):
 if not rr:return {'n':0}
 e=np.array([r['forecast_m']-r['actual_m'] for r in rr]);a=abs(e)
 return {'n':len(rr),'mae_m':float(a.mean()),'rmse_m':float(np.sqrt(np.mean(e**2))),'bias_m':float(e.mean()),'p90_abs_m':float(np.quantile(a,.9)),'p98_abs_m':float(np.quantile(a,.98)),'max_abs_m':float(a.max()),'within_10cm_rate':float(np.mean(a<=.1)),'within_20cm_rate':float(np.mean(a<=.2)),'within_50cm_rate':float(np.mean(a<=.5)),'within_50cm_hits':int((a<=.5).sum())}
metrics=[];strata=[];paired=[];peak_ids=np.flatnonzero((times>=cuts[2])&np.isfinite(local));peak_i=int(peak_ids[np.argmax(local[peak_ids])]);peak_at=times[peak_i]
for (h,phase,family),rr in groups.items():
 ids=np.array([r['index'] for r in rr]);check(f'prediction_membership:{h}:{phase}:{family}',ids.tolist()==membership[h][phase].tolist())
 m=summary(rr);ref=next(r for r in report['evaluations'] if r['h']==h and r['phase']==phase and r['model']==family)
 for k,v in m.items():check(f'metric:{h}:{phase}:{family}:{k}',same(v,ref[k]))
 metrics.append({'h':h,'phase':phase,'model':family,**m})
 subsets={'water_ge_7m':[r for r in rr if r['actual_m']>=7], 'water_ge_9m':[r for r in rr if r['actual_m']>=9], 'rapid_target_rise_ge_1m':[r for r in rr if r['actual_m']-r['base_m']>=1], 'origin_rising':[r for r in rr if trend[r['index']]>.05], 'origin_falling':[r for r in rr if trend[r['index']]<-.05], 'origin_stable':[r for r in rr if abs(trend[r['index']])<=.05]}
 if phase=='stress_current':
  subsets.update(pre_peak=[r for r in rr if times[r['index']]+h*3600<peak_at-3*3600],peak_window=[r for r in rr if abs(times[r['index']]+h*3600-peak_at)<=3*3600],recession=[r for r in rr if times[r['index']]+h*3600>peak_at+3*3600])
 for name,selected in subsets.items():strata.append({'h':h,'phase':phase,'model':family,'group':name,**summary(selected)})
 for name,count_key,mae_key in [('water_ge_7m','water_at_least_7m_n','water_at_least_7m_mae_m'),('water_ge_9m','high_water_n','high_water_mae_m'),('rapid_target_rise_ge_1m','rapid_rise_n','rapid_rise_mae_m')]:
  small=summary(subsets[name]);check(f'subgroup_metric:{h}:{phase}:{family}:{name}',small['n']==ref[count_key] and same(small.get('mae_m'),ref[mae_key]))
 for name in ['rising','falling','stable']:
  small=summary(subsets['origin_'+name]);previous=ref['originPhases'][name]
  check(f'origin_phase_metric:{h}:{phase}:{family}:{name}',small['n']==previous['n'] and same(small.get('mae_m'),previous['mae_m']) and same(small.get('within_20cm_rate'),previous['within_20cm_rate']))
 if phase=='validation' and family=='lagged':
  selected=model['horizons'][h-1];errors=np.array([r['actual_m']-r['forecast_m'] for r in rr])
  check(f'validation_residual_envelope:{h}',same(float(np.quantile(errors,.05)),selected['empiricalErrorQuantiles']['p05']) and same(float(np.quantile(errors,.95)),selected['empiricalErrorQuantiles']['p95']))
  rapid=summary(subsets['rapid_target_rise_ge_1m']);high=summary(subsets['water_ge_9m'])
  check(f'selected_validation_score_from_csv:{h}',same(m['mae_m']+.5*rapid.get('mae_m',0)+.5*high.get('mae_m',0),selected['validationScore']))
 # Replay published selected-model held-out and stress predictions with stored coefficients.
 if family=='lagged' and phase!='validation':
  entry=model['horizons'][h-1];p=entry['parameters'];calc=local[ids]+((X[ids]-p['mean'])/p['scale'])@p['beta']+p['intercept'];saved=np.array([r['forecast_m'] for r in rr]);err=float(np.max(abs(calc-saved)))
  check(f'frozen_prediction_replay:{h}:{phase}',err<1e-10,err);replays.append({'h':h,'phase':phase,'n':len(ids),'max_abs_difference_m':err})
 if family in ['persistence','local_trend_2h']:
  calc=local[ids]+(h*trend[ids] if family=='local_trend_2h' else 0);check(f'baseline_replay:{h}:{phase}:{family}',np.allclose(calc,[r['forecast_m'] for r in rr],rtol=0,atol=1e-10))
for h in range(1,7):
 for phase in ['validation','test','stress_current']:
  candidate=groups[(h,phase,'lagged')]
  for family in ['contemporaneous','persistence','local_trend_2h']:
   control=groups[(h,phase,family)];check(f'paired_origins:{h}:{phase}:{family}',[r['index'] for r in candidate]==[r['index'] for r in control])
   c=np.array([abs(r['forecast_m']-r['actual_m']) for r in candidate]);b=np.array([abs(r['forecast_m']-r['actual_m']) for r in control]);d=c-b
   paired.append({'h':h,'phase':phase,'comparator':family,'n':len(d),'candidate_mae_m':float(c.mean()),'comparator_mae_m':float(b.mean()),'difference_mae_m':float(d.mean()),'improved':int((d < -1e-12).sum()),'worse':int((d>1e-12).sum()),'unchanged':int((abs(d)<=1e-12).sum()),'candidate_hit_rate':float(np.mean(c<=.5)),'comparator_hit_rate':float(np.mean(b<=.5))})
def write_csv(name,content):
 fields=list(dict.fromkeys(k for r in content for k in r));f=(OUT/name).open('w',newline='');w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(content);f.close()
for name,content in [('metrics.csv',metrics),('strata.csv',strata),('coverage.csv',coverage),('paired-comparisons.csv',paired),('frozen-inference-replay.csv',replays)]:write_csv(name,content)
# Mark every data/model artifact hash; do not mutate or copy predictions into the run.
result={'schema':1,'audited_at':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'passed':sum(r['passed'] for r in checks),'failed':sum(not r['passed'] for r in checks),'refit_performed':False,'production_writes':False,'experiment_hashes':{p.name:digest(p) for p in RUN.iterdir() if p.is_file()},'audit_script_sha256':digest(Path(__file__)),'stress_observed_peak':{'time':iso(peak_at),'level_m':float(local[peak_i]),'definition':'First maximum exact-hour Muçum observation in frozen September21 onward snapshot; phase diagnostic only, not independent event certification'},'ridge_equation_checks':normal_equations,'checks':checks}
(OUT/'checks.json').write_text(json.dumps(result,ensure_ascii=False,allow_nan=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['check_count','passed','failed','refit_performed','stress_observed_peak']},ensure_ascii=False))
if result['failed']:raise SystemExit(1)
