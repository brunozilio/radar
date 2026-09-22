"""Independent fixed-delay-mixture audit. No fit, operational helper or network."""
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
import ast,csv,hashlib,json,importlib.metadata
import numpy as np,joblib
from threadpoolctl import threadpool_limits
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent;E=R/'outputs/experimento-radar-mistura-atrasos-20260922'
F=('profile_A_control','profile_B_control','mixed_profile_candidate');checks=[];inputs={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def track(p):inputs[str(p.relative_to(R))]=sha(p);return p
def js(p):return json.loads(track(p).read_text())
def cr(p):return list(csv.DictReader(track(p).open()))
def nz(p):return dict(np.load(track(p)))
def ck(n,b):checks.append({'check':n,'passed':bool(b)});assert b,n
def eq(a,b):return a.shape==b.shape and np.array_equal(a,b,equal_nan=True)
def epoch(s):return datetime.fromisoformat(s).timestamp()
def iso(t):return datetime.fromtimestamp(float(t),timezone.utc).astimezone(timezone(__import__('datetime').timedelta(hours=-3))).isoformat()
def num(v):return float(v) if v not in ('',None) else np.nan
def jdump(n,d):(P/n).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def save(n,rr):
 with (P/n).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
def mnum(v):return float(v) if np.isfinite(v) else None
def run():
 assert (E/'experiment.json').exists(),'Wait for final artifact; never restart training.'
 exp=js(E/'experiment.json');prefit=js(E/'pre-fit-manifest.json');proto=js(E/'protocol.json')
 ck('registration before prepared manifest before completion',proto['registered_at_utc']<prefit['recorded_at_utc']<exp['finished_at_utc'])
 ck('protocol copiedexact',sha(track(R/'docs/radar-delay-profile-mixture-protocol.json'))==sha(E/'protocol.json'))
 for q in (prefit,exp):
  for f,h in q['input_sha256'].items():ck('inputhash:'+f,sha(track(R/f))==h)
  for f,h in q['prepared_sha256'].items():ck('preparedhash:'+f,sha(track(E/f))==h)
 for f in js(E/'artifact-hashes.json'):ck('artifact:'+f['file'],sha(track(E/f['file']))==f['sha256'])
 runtime={k:importlib.metadata.version(k) for k in exp['runtime']};ck('runtime equal',runtime==exp['runtime']==prefit['runtime'])
 start,end,stop=map(epoch,['2025-10-01T00:00:00-03:00','2026-07-01T00:00:00-03:00','2026-09-21T00:00:00-03:00'])
 data={}
 for profile,path in proto['profiles'].items():
  raw=nz(R/path);keep=raw['times']<stop;data[profile]={k:v[keep] for k,v in raw.items()}
 a,b=data['A'],data['B'];t=a['times'];truth=a['truth'];prepared=nz(E/'prepared-inputs.npz');masks=nz(E/'training-masks.npz')
 ck('12912 by180',a['features'].shape==b['features'].shape==(12912,180));ck('truth/time/weather exact',eq(t,b['times']) and eq(truth,b['truth']) and eq(a['features'][:,120:],b['features'][:,120:]));ck('times hourly',np.all(np.diff(t)==3600))
 complete={p:np.isfinite(d['features'][:,:24]).all(axis=1) for p,d in data.items()}
 rng=np.random.Generator(np.random.PCG64(57));assign=rng.integers(0,2,size=len(t),dtype=np.int8);ck('seed57exact',eq(assign,prepared['assignment']));ck('6408A6504B',int((assign==0).sum())==6408 and int((assign==1).sum())==6504)
 for k,val in [('times',t),('truth',truth)]+[(f'features_{p}',d['features']) for p,d in data.items()]+[(f'base_{p}',d['base']) for p,d in data.items()]+[(f'complete_{p}',complete[p]) for p in data]:ck('prepared:'+k,eq(prepared[k],val))
 mixedX=np.where(assign[:,None]==0,a['features'],b['features']);mixedbase=np.where(assign==0,a['base'],b['base'])
 fitX={F[0]:a['features'],F[1]:b['features'],F[2]:mixedX};fitbase={F[0]:a['base'],F[1]:b['base'],F[2]:mixedbase}
 cfgpath=next(x for x in exp['input_sha256'] if x.endswith('/previsao-atualizada.csv'));configs=cr(R/cfgpath)
 training=cr(E/'training.csv');trainingby={(r['phase'],r['family'],int(r['horizon_h'])):r for r in training};ck('72training unique',len(training)==len(trainingby)==72)
 rows=cr(E/'predictions.csv');ck('204168rows',len(rows)==204168);groups=defaultdict(list);keys=set();truth_missing=Counter() if False else defaultdict(int)
 for r in rows:
  k=(r['phase'],r['profile'],r['origin'],int(r['nominal_lead_h']));ckdup=k in keys
  if ckdup:raise AssertionError('duplicatepredictionkey')
  keys.add(k);groups[(r['phase'],r['profile'],int(r['nominal_lead_h']))].append(r)
 ck('48groups',len(groups)==48)
 audittrain=[];replay=[];samples={};schedule_count=0
 for h in range(1,13):
  target=np.full(len(t),np.nan);target[:-h]=truth[h:];common=np.isfinite(a['base'])&np.isfinite(b['base'])&np.isfinite(target)&complete['A']&complete['B']
  first=t+h*3600<start;second=(t>=start)&(t+h*3600<end);leaf,loss=ast.literal_eval(configs[h-1]['parameters'])
  for phase,left,right,mask in [('validation',start,end,common&first),('test',end,stop,common&(first|second))]:
   ix=np.flatnonzero(mask);ck(f'{phase}h{h}mask',eq(mask,masks[f'{phase}_h{h}']));ck(f'{phase}h{h}cutoff/order',np.all(t[ix]+h*3600<left) and len(np.unique(t[ix]))==len(ix) and np.all(np.diff(ix)>0))
   scheduled=np.flatnonzero((t>=left)&(t+h*3600<right));schedule_count+=len(scheduled);samples[f'{phase}_h{h}_ix']=ix
   params_prev=None
   for family in F:
    y=target[ix]-fitbase[family][ix];w=1+2*(abs(y)>=1)+2*(target[ix]>=9);r=trainingby[(phase,family,h)]
    profilea=len(ix) if family==F[0] else 0 if family==F[1] else int((assign[ix]==0).sum())
    for k,v in {'n':len(ix),'distinct_origins':len(ix),'profile_A_rows':profilea,'profile_B_rows':len(ix)-profilea,'weights_sum':int(w.sum()),'targets_ge_7m':int((target[ix]>=7).sum()),'leaf_nodes':leaf}.items():ck(f'{phase}{family}h{h}{k}',int(r[k])==v)
    ck(f'{phase}{family}h{h}cutoffstrings',epoch(r['latest_training_target'])==max(t[ix]+h*3600) and epoch(r['cutoff_exclusive'])==left and r['loss']==loss)
    samples[f'{phase}_{family}_h{h}_delta']=y;samples[f'{phase}_{family}_h{h}_weights']=w
    model=joblib.load(track(E/'models'/f'{phase}-{family}-{h}.joblib'));params=model.get_params()
    fixed={'max_iter':180,'max_leaf_nodes':leaf,'min_samples_leaf':35,'learning_rate':.055,'l2_regularization':10,'loss':loss,'early_stopping':False,'random_state':57}
    ck(f'{phase}{family}h{h}config',all(params[k]==v for k,v in fixed.items()) and model.n_features_in_==180 and model.n_iter_==180)
    if params_prev is not None:ck(f'{phase}{family}h{h}fullparameterssame',params==params_prev)
    params_prev=params
    audittrain.append(dict(phase=phase,family=family,horizon_h=h,n=len(ix),profile_A_rows=profilea,profile_B_rows=len(ix)-profilea,weights_sum=int(w.sum()),delta_sha256=hashlib.sha256(y.tobytes()).hexdigest(),weights_sha256=hashlib.sha256(w.tobytes()).hexdigest(),features_sha256=hashlib.sha256(fitX[family][ix].tobytes()).hexdigest()))
    for profile in ('A','B'):
     rr=groups[phase,profile,h];idx=np.array([np.searchsorted(t,epoch(z['origin'])) for z in rr]);ck(f'{phase}{profile}h{h}schedule',eq(idx,scheduled));d=data[profile];apply=np.isfinite(d['base'][idx]);pred=np.full(len(idx),np.nan)
     pred[apply]=model.predict(d['features'][idx[apply]])+d['base'][idx[apply]]
     saved=np.array([num(z[family+'_m']) for z in rr]);ck(f'{phase}{profile}{family}h{h}inferenceexact',eq(pred,saved))
     replay.append(dict(phase=phase,profile=profile,family=family,horizon_h=h,rows=len(idx),inferred=int(apply.sum()),max_difference_m=0.0,exact=True))
     if family==F[0]:
      ck(f'{phase}{profile}h{h}targets/bases',eq(target[idx],np.array([num(z['actual_m']) for z in rr])) and eq(d['base'][idx],np.array([num(z['base_m']) for z in rr])))
      ck(f'{phase}{profile}h{h}complete/targettime',all((z['complete24']=='True')==bool(complete[profile][i]) and epoch(z['target_time'])==t[i]+h*3600 for z,i in zip(rr,idx)))
 ck('102084 physical scheduledrows',schedule_count==102084);ck('144replays',len(replay)==144)
 # Every metric from CSV values, retaining unknown targets and failures separately.
 metrics=[]
 for (phase,profile,h),rr in sorted(groups.items()):
  actual=np.array([num(z['actual_m']) for z in rr]);comp=np.array([z['complete24']=='True' for z in rr])
  for population in ('full_schedule','complete24','missing24'):
   pop=np.ones(len(rr),bool) if population=='full_schedule' else comp if population=='complete24' else ~comp
   for subset in ('all','level_ge_7m'):
    obs=pop&np.isfinite(actual)&(np.ones(len(rr),bool) if subset=='all' else actual>=7)
    for family in F:
     pred=np.array([num(z[family+'_m']) for z in rr]);paired=obs&np.isfinite(pred);error=pred[paired]-actual[paired];ae=abs(error);n=int(paired.sum());nt=int(obs.sum());hits=int(np.sum(ae<=.5))
     metrics.append(dict(phase=phase,profile=profile,horizon_h=h,population=population,subset=subset,family=family,scheduled_rows=int(pop.sum()),missing_truth=int((pop&~np.isfinite(actual)).sum()),observed_targets=nt,pairs=n,failures=nt-n,hits=hits,paired_hit_fraction=hits/n if n else None,observed_target_hit_fraction=hits/nt if nt else None,mae_m=float(ae.mean()) if n else None,bias_m=float(error.mean()) if n else None,p98_abs_m=float(np.quantile(ae,.98)) if n else None,max_abs_m=float(ae.max()) if n else None))
 key=lambda r:(r['phase'],r['profile'],int(r['horizon_h']),r['population'],r['subset'],r['family'])
 saved={key(r):r for r in cr(E/'evaluation.csv')};ck('864uniquemetrics',len(saved)==len(metrics)==864)
 for r in metrics:
  s=saved[key(r)];ok=True
  for k,v in r.items():
   if k in ('phase','profile','population','subset','family'):ok&=s[k]==v
   elif v is None:ok&=s[k]==''
   else:ok&=abs(float(s[k])-v)<=1e-12
  ck('metric'+str(key(r)),ok)
 # Matching-profile controls only; cross-controls remain in complete metrics.
 contrasts=[];index={key(r):r for r in metrics}
 for r in metrics:
  if r['family']!=F[2] or r['population']!='full_schedule':continue
  control=F[0] if r['profile']=='A' else F[1];c=index[(r['phase'],r['profile'],r['horizon_h'],r['population'],r['subset'],control)]
  contrasts.append(dict(phase=r['phase'],profile=r['profile'],horizon_h=r['horizon_h'],subset=r['subset'],control=control,observed_targets=r['observed_targets'],failures=r['failures'],control_hits=c['hits'],candidate_hits=r['hits'],delta_hits=r['hits']-c['hits'],control_mae_m=c['mae_m'],candidate_mae_m=r['mae_m'],delta_mae_m=r['mae_m']-c['mae_m'] if r['mae_m'] is not None else None,control_max_m=c['max_abs_m'],candidate_max_m=r['max_abs_m']))
 save('training-reconstruction.csv',audittrain);np.savez_compressed(P/'reconstructed-samples.npz',**samples);save('inference-replay.csv',replay);save('independent-metrics.csv',metrics);save('matching-profile-contrasts.csv',contrasts)
 jdump('input-hashes.json',inputs);jdump('verification.json',{'passed':all(c['passed'] for c in checks),'checked_at_utc':datetime.now(timezone.utc).isoformat(),'checks_count':len(checks),'checks':checks,'models':72,'inference_applications':144,'rows_two_profiles':len(rows),'physical_scheduled_rows':schedule_count,'metric_rows':len(metrics),'assignment_A':6408,'assignment_B':6504,'no_fit_no_network':True,'limits':['Both profiles and periods are previously inspected development, not independent future validation.','The duplicated evaluation views are not independent events.','Reconstructing input samples/weights and inspecting fit source does not independently refit/certify tree optimization.','Registration/pre-fit/completion timestamps and hashes checked; no separate authenticated fit-start timestamp.','No operational baseline reproduction claim: shared intersection membership differs from original issue fits.','No promotion or98percentaccuracy claim.']})
 print('PASS',len(checks),'checks;144exact applications;864metrics',flush=True)
if __name__=='__main__':
 with threadpool_limits(limits=2):run()
