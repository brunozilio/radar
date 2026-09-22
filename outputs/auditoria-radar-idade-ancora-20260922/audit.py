"""Independent anchor-age audit; no fit/network/operational imports."""
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict,Counter
import csv,json,hashlib,importlib.metadata
import numpy as np,joblib
from threadpoolctl import threadpool_limits
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent;E=R/'outputs/experimento-radar-idade-ancora-20260922';B=R/'outputs/experimento-radar-mistura-atrasos-20260922'
F=('profile_A_control','profile_B_control','mixed_profile_candidate','age_mixed_candidate');checks=[];inputs={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def track(p):inputs[str(p.relative_to(R))]=sha(p);return p
def js(p):return json.loads(track(p).read_text())
def cr(p):return list(csv.DictReader(track(p).open()))
def nz(p):return dict(np.load(track(p)))
def ck(n,b):checks.append({'check':n,'passed':bool(b)});assert b,n
def eq(a,b):return a.shape==b.shape and np.array_equal(a,b,equal_nan=True)
def ep(s):return datetime.fromisoformat(s).timestamp()
def num(x):return float(x) if x not in ('',None) else np.nan
def jd(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def save(n,rr):
 with (P/n).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
def run():
 assert (E/'experiment.json').exists(),'Wait for completion; never launch fit.'
 exp=js(E/'experiment.json');pre=js(E/'pre-fit-manifest.json');proto=js(E/'protocol.json');parent=js(B/'experiment.json')
 ck('registration/pre-fit/completion order',proto['registered_at_utc']<pre['recorded_at_utc']<exp['finished_at_utc']);ck('copiedprotocol',sha(E/'protocol.json')==sha(track(R/'docs/radar-anchor-age-feature-protocol.json')))
 for m in (pre,exp):
  for path,h in m['input_sha256'].items():ck('input:'+path,sha(track(R/path))==h)
  ck('agehash',sha(track(E/'age-inputs.npz'))==m['age_inputs_sha256'])
 for folder in (B,E):
  for r in js(folder/'artifact-hashes.json'):ck('artifact:'+folder.name+'/'+r['file'],sha(track(folder/r['file']))==r['sha256'])
 ck('runtime',exp['runtime']==parent['runtime']=={k:importlib.metadata.version(k) for k in exp['runtime']})
 d=nz(B/'prepared-inputs.npz');masks=nz(B/'training-masks.npz');savedage=nz(E/'age-inputs.npz');t=d['times'];truth=d['truth'];assign=d['assignment']
 ck('PCG64assignment57',eq(assign,np.random.Generator(np.random.PCG64(57)).integers(0,2,size=len(t),dtype=np.int8)));ck('assignmentcounts',int((assign==0).sum())==6408 and int((assign==1).sum())==6504)
 trace=cr(E/'age-trace.csv');traceidx={(r['profile'],float(r['origin_epoch'])):r for r in trace};ck('25824 tracekeys',len(traceidx)==len(trace)==25824)
 age={};X={};agesummary=[];tracerows=[]
 folders={'A':R/'outputs/mucum-hourly-20260922T000704-0300','B':R/'outputs/mucum-hourly-20260922T010016-0300'}
 for profile,folder in folders.items():
  z=nz(folder/'history/ana-86510000.npz');sm=js(folder/'history/manifest.json');ck(profile+'historyhash',sha(folder/'history/ana-86510000.npz')==sm['files']['ana-86510000.npz']);ck(profile+'source sortedunique',np.all(np.diff(z['times'])>0))
  a=next(r for r in cr(folder/'idades-fontes.csv') if r['source']=='86510000');delay=float(a['delay_minutes'])*60;ck(profile+'delay15/30',delay==(900 if profile=='A' else 1800))
  # Independent sequential predecessor lookup; never search backwards past a NaN.
  recbase=np.full(len(t),np.nan);recage=np.full(len(t),np.nan);pointer=-1;reasons=Counter()
  for i,origin in enumerate(t):
   query=origin-delay
   while pointer+1<len(z['times']) and z['times'][pointer+1]<=query:pointer+=1
   source_time=z['times'][pointer] if pointer>=0 else np.nan;source_value=z['level'][pointer] if pointer>=0 else np.nan;admissible=pointer>=0 and query-source_time<=900
   if admissible:recbase[i]=source_value
   if np.isfinite(recbase[i]):recage[i]=(origin-source_time)/60;reasons['finite']+=1
   elif pointer<0:reasons['no_predecessor']+=1
   elif not admissible:reasons['expired']+=1
   else:reasons['newest_record_nonfinite']+=1
   r=traceidx[profile,float(origin)]
   ck(profile+f'trace{i}',int(r['source_index'])==pointer and num(r['query_epoch'])==query and (r['asof_admissible']=='True')==admissible and eq(np.array([num(r['selected_source_epoch']),num(r['original_level_m']),num(r['base_m']),num(r['age_minutes'])]),np.array([source_time,source_value,recbase[i],recage[i]])))
  ck(profile+'base exact includingNaN',eq(recbase,d['base_'+profile]));ck(profile+'age exact',eq(recage,savedage['age_'+profile]));ck(profile+'age missingnesssame',eq(np.isnan(recage),np.isnan(recbase)));ck(profile+'no future and bounds',np.all((recage[np.isfinite(recage)]>=delay/60)&(recage[np.isfinite(recage)]<=delay/60+15)))
  vals,cts=np.unique(recage[np.isfinite(recage)],return_counts=True)
  for val,n in zip(vals,cts):agesummary.append(dict(profile=profile,age_minutes=float(val),origins=int(n)))
  agesummary.append(dict(profile=profile,age_minutes=None,origins=int(np.isnan(recage).sum())))
  tracerows.append(dict(profile=profile,delay_minutes=delay/60,**{k:reasons[k] for k in ('finite','no_predecessor','expired','newest_record_nonfinite')}));age[profile]=recage;X[profile]=np.column_stack((d['features_'+profile],recage));ck(profile+'181preserves180',X[profile].shape==(12912,181) and eq(X[profile][:,:180],d['features_'+profile]))
 oldrows=cr(B/'predictions.csv');rows=cr(E/'predictions.csv');ck('204168 identical parentfields',len(rows)==len(oldrows)==204168 and all(all(r[k]==v for k,v in o.items()) for r,o in zip(rows,oldrows)))
 groups=defaultdict(list)
 for r in rows:groups[(r['phase'],r['profile'],int(r['nominal_lead_h']))].append(r)
 ck('48schedule groups',len(groups)==48)
 oldtrain={(r['phase'],r['family'],int(r['horizon_h'])):r for r in cr(B/'training.csv')};newtrain={(r['phase'],int(r['horizon_h'])):r for r in cr(E/'training.csv')};ck('24new trainingrows',len(newtrain)==24)
 mixedX=np.where(assign[:,None]==0,X['A'],X['B']);mb=np.where(assign==0,d['base_A'],d['base_B']);mixedage=np.where(assign==0,age['A'],age['B']);ck('mixed age frommatchingprofile',eq(mixedX[:,180],mixedage))
 start,end,stop=map(ep,['2025-10-01T00:00:00-03:00','2026-07-01T00:00:00-03:00','2026-09-21T00:00:00-03:00']);replay=[];train=[];samples={}
 for h in range(1,13):
  target=np.full(len(t),np.nan);target[:-h]=truth[h:];common=np.isfinite(d['base_A'])&np.isfinite(d['base_B'])&np.isfinite(target)&np.isfinite(d['features_A'][:,:24]).all(1)&np.isfinite(d['features_B'][:,:24]).all(1);first=t+h*3600<start;second=(t>=start)&(t+h*3600<end)
  for phase,left,right,mask in [('validation',start,end,common&first),('test',end,stop,common&(first|second))]:
   ck(f'{phase}h{h}mask',eq(mask,masks[f'{phase}_h{h}']));ix=np.flatnonzero(mask);ck(f'{phase}h{h}order/cutoff',len(np.unique(t[ix]))==len(ix) and np.all(np.diff(ix)>0) and np.all(t[ix]+h*3600<left));y=target[ix]-mb[ix];w=1+2*(abs(y)>=1)+2*(target[ix]>=9)
   info=oldtrain[phase,F[2],h];new=newtrain[phase,h];ck(f'{phase}h{h}metadata preserved',all(new[k]==v for k,v in info.items() if k!='family') and new['family']==F[3] and new['features']=='181');ck(f'{phase}h{h}weights/count',len(ix)==int(info['n']) and int(w.sum())==int(info['weights_sum']))
   samples[f'{phase}_h{h}_indices']=ix;samples[f'{phase}_h{h}_delta']=y;samples[f'{phase}_h{h}_weights']=w;samples[f'{phase}_h{h}_age']=mixedage[ix]
   old=joblib.load(track(B/'models'/f'{phase}-{F[2]}-{h}.joblib'));newmodel=joblib.load(track(E/'models'/f'{phase}-{F[3]}-{h}.joblib'));ck(f'{phase}h{h}sameparamsplus181',newmodel.get_params()==old.get_params() and newmodel.n_features_in_==181 and old.n_features_in_==180 and newmodel.n_iter_==180)
   train.append(dict(phase=phase,horizon_h=h,n=len(ix),weights_sum=int(w.sum()),profile_A_rows=int((assign[ix]==0).sum()),profile_B_rows=int((assign[ix]==1).sum()),age15_rows=int((mixedage[ix]==15).sum()),age30_rows=int((mixedage[ix]==30).sum()),age45_rows=int((mixedage[ix]==45).sum()),delta_sha256=hashlib.sha256(y.tobytes()).hexdigest(),weights_sha256=hashlib.sha256(w.tobytes()).hexdigest(),inputs181_sha256=hashlib.sha256(mixedX[ix].tobytes()).hexdigest()))
   for profile in ('A','B'):
    rr=groups[phase,profile,h];ixs=np.array([np.searchsorted(t,ep(r['origin'])) for r in rr]);scheduled=np.flatnonzero((t>=left)&(t+h*3600<right));ck(f'{phase}{profile}h{h}schedule',eq(ixs,scheduled));base=d['base_'+profile];apply=np.isfinite(base[scheduled])
    ck(f'{phase}{profile}h{h}targets/bases',eq(target[scheduled],np.array([num(r['actual_m']) for r in rr])) and eq(base[scheduled],np.array([num(r['base_m']) for r in rr])))
    for family in F:
     model=newmodel if family==F[3] else joblib.load(track(B/'models'/f'{phase}-{family}-{h}.joblib'));xx=X[profile] if family==F[3] else d['features_'+profile];pred=np.full(len(scheduled),np.nan);pred[apply]=model.predict(xx[scheduled[apply]])+base[scheduled[apply]];frozen=np.array([num(r[family+'_m']) for r in rr]);ck(f'{phase}{profile}{family}h{h}exactinference',eq(pred,frozen));replay.append(dict(phase=phase,profile=profile,family=family,horizon_h=h,scheduled=len(scheduled),inferred=int(apply.sum()),max_difference_m=0.0,exact=True))
 ck('192 replays144parent48new',len(replay)==192 and sum(r['family']==F[3] for r in replay)==48)
 metrics=[]
 for (phase,profile,h),rr in sorted(groups.items()):
  actual=np.array([num(r['actual_m']) for r in rr]);complete=np.array([r['complete24']=='True' for r in rr])
  for population in ('full_schedule','complete24','missing24'):
   pop=np.ones(len(rr),bool) if population=='full_schedule' else complete if population=='complete24' else ~complete
   for subset in ('all','level_ge_7m'):
    obs=pop&np.isfinite(actual)&(np.ones(len(rr),bool) if subset=='all' else actual>=7)
    for family in F:
     pred=np.array([num(r[family+'_m']) for r in rr]);pair=obs&np.isfinite(pred);err=pred[pair]-actual[pair];ae=abs(err);n=int(pair.sum());nobs=int(obs.sum());hits=int((ae<=.5).sum())
     metrics.append(dict(phase=phase,profile=profile,horizon_h=h,population=population,subset=subset,family=family,scheduled_rows=int(pop.sum()),missing_truth=int((pop&~np.isfinite(actual)).sum()),observed_targets=nobs,pairs=n,failures=nobs-n,hits=hits,paired_hit_fraction=hits/n if n else None,observed_target_hit_fraction=hits/nobs if nobs else None,mae_m=float(ae.mean()) if n else None,bias_m=float(err.mean()) if n else None,p98_abs_m=float(np.quantile(ae,.98)) if n else None,max_abs_m=float(ae.max()) if n else None))
 key=lambda r:(r['phase'],r['profile'],int(r['horizon_h']),r['population'],r['subset'],r['family'])
 saved={key(r):r for r in cr(E/'evaluation.csv')};oldmetrics={key(r):r for r in cr(B/'evaluation.csv')};ck('1152 unique metrics',len(metrics)==len(saved)==1152)
 for r in metrics:
  ok=True
  for k,v in r.items():
   if k in ('phase','profile','population','subset','family'):ok&=saved[key(r)][k]==v
   elif v is None:ok&=saved[key(r)][k]==''
   else:ok&=abs(float(saved[key(r)][k])-v)<=1e-12
  ck('metric'+str(key(r)),ok)
  if r['family']!=F[3]:ck('parentmetric'+str(key(r)),saved[key(r)]==oldmetrics[key(r)])
 index={key(r):r for r in metrics};contrasts=[]
 for r in metrics:
  if r['family']!=F[3] or r['population']!='full_schedule':continue
  for reference in (F[2],F[0] if r['profile']=='A' else F[1]):
   b=index[(r['phase'],r['profile'],r['horizon_h'],r['population'],r['subset'],reference)]
   contrasts.append(dict(phase=r['phase'],profile=r['profile'],horizon_h=r['horizon_h'],subset=r['subset'],reference=reference,observed_targets=r['observed_targets'],failures=r['failures'],reference_hits=b['hits'],aged_hits=r['hits'],delta_hits=r['hits']-b['hits'],reference_mae_m=b['mae_m'],aged_mae_m=r['mae_m'],delta_mae_m=r['mae_m']-b['mae_m'] if r['mae_m'] is not None else None,reference_max_m=b['max_abs_m'],aged_max_m=r['max_abs_m']))
 bothage=np.r_[age['A'],age['B']];profilelabels=np.r_[np.zeros(len(t)),np.ones(len(t))];finite=np.isfinite(bothage);corr=float(np.corrcoef(bothage[finite],profilelabels[finite])[0,1]);jd('age-profile-association.json',{'all_pre_stop_origins_each_view_once':True,'age_profile_pearson':corr,'finite_views':int(finite.sum()),'overlap_age_minutes':sorted(set(age['A'][np.isfinite(age['A'])])&set(age['B'][np.isfinite(age['B'])])),'interpretation':'Association reflects paired construction, not independent events or causal effect; age partly identifies entire delayprofile.'})
 save('age-reconstruction-summary.csv',agesummary);save('base-failure-reasons.csv',tracerows);save('training-reconstruction.csv',train);save('inference-replay.csv',replay);save('independent-metrics.csv',metrics);save('contrasts.csv',contrasts);np.savez_compressed(P/'reconstructed-ages-samples.npz',age_A=age['A'],age_B=age['B'],**samples);jd('input-hashes.json',inputs)
 jd('verification.json',{'passed':all(c['passed'] for c in checks),'checked_at_utc':datetime.now(timezone.utc).isoformat(),'checks_count':len(checks),'checks':checks,'models_reapplied':96,'applications':192,'new_model_applications':48,'parent_model_applications':144,'rows':len(rows),'metrics':1152,'age_profile_correlation':corr,'fit_or_network':False,'limits':['Measurement-age reconstruction is not publication/receipt-latency certification.','Two ageprofiles are associated with other delayed predictors, so improvements do not isolate Muçumage causally.','Periods previously inspected; no independent holdout/98percent/promotion.','No refit; serialized models do not contain all training samples, although samples,weights,sourcecode and summaries were checked.']})
 print('PASS',len(checks),'checks;192exactreplays;1152metrics',flush=True)
if __name__=='__main__':
 with threadpool_limits(limits=2):run()
