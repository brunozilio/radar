"""Independent weight-threshold experiment audit; inference only, no fitting/network."""
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone
import csv,json,hashlib,importlib.metadata
import numpy as np,joblib
from threadpoolctl import threadpool_limits
P=Path(__file__).resolve().parent;R=P.parents[1];E=R/'outputs/experimento-radar-peso-cheia-7m-20260922';B=R/'outputs/experimento-radar-mistura-atrasos-20260922'
F=('profile_A_control','profile_B_control','mixed_profile_candidate','flood_weight_7m');checks=[];inputs={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def track(p):inputs[str(p.relative_to(R))]=sha(p);return p
def js(p):return json.loads(track(p).read_text())
def csvrows(p):return list(csv.DictReader(track(p).open()))
def nz(p):return dict(np.load(track(p)))
def ck(n,b):checks.append(dict(check=n,passed=bool(b)));assert b,n
def eq(a,b):return np.array_equal(a,b,equal_nan=True)
def ep(s):return datetime.fromisoformat(s).timestamp()
def num(s):return float(s) if s not in ('',None) else np.nan
def dump(n,v):(P/n).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def save(n,rows):
 with (P/n).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 exp=js(E/'experiment.json');pre=js(E/'pre-fit-manifest.json');proto=js(E/'protocol.json')
 ck('protocol hash',sha(E/'protocol.json')=='1f8ccf42085b3c3430aa9c7efe03b49eb4ddf7dcf90cb688ce156ebb7355c35c')
 ck('recorded ordering',proto['registered_at_utc']<pre['recorded_at_utc']<exp['finished_at_utc'])
 ck('runtime',exp['runtime']==pre['runtime']=={k:importlib.metadata.version(k) for k in exp['runtime']})
 for meta in (pre,exp):
  for path,digest in meta['input_sha256'].items():ck('source '+path,sha(track(R/path))==digest)
  for path,digest in meta['prepared_sha256'].items():ck('prefit weightplan '+path,sha(track(E/path))==digest)
 for folder in (B,E):
  for r in js(folder/'artifact-hashes.json'):ck('artifact '+folder.name+'/'+r['file'],sha(track(folder/r['file']))==r['sha256'])
 ck('executed code identical',sha(E/'code/hydro_radar_flood_weight.py')==sha(track(R/'scripts/hydro_radar_flood_weight.py')))
 d=nz(B/'prepared-inputs.npz');masks=nz(B/'training-masks.npz');savedweights=nz(E/'training-weights.npz');expected=nz(P/'expected-training-vectors.npz');weightplan={(r['phase'],int(r['horizon_h'])):r for r in csvrows(E/'weight-plan.csv')};t=d['times'];truth=d['truth'];n=len(t);assign=d['assignment']
 ck('PCG57 assignment',eq(assign,np.random.Generator(np.random.PCG64(57)).integers(0,2,size=n,dtype=np.int8)))
 ck('48 weightvectors',len(savedweights)==48)
 X=d['features_A'].copy();X[assign==1]=d['features_B'][assign==1];base=d['base_A'].copy();base[assign==1]=d['base_B'][assign==1]
 train={(r['phase'],int(r['horizon_h'])):r for r in csvrows(E/'training.csv')};oldtrain={(r['phase'],int(r['horizon_h'])):r for r in csvrows(B/'training.csv') if r['family']==F[2]}
 rows=csvrows(E/'predictions.csv');oldrows=csvrows(B/'predictions.csv')
 ck('preserved204168 rows',len(rows)==len(oldrows)==204168 and all(all(r[k]==v for k,v in old.items()) for r,old in zip(rows,oldrows)))
 groups=defaultdict(list)
 for r in rows:groups[r['phase'],r['profile'],int(r['nominal_lead_h'])].append(r)
 ck('24models',len(list((E/'models').glob('*.joblib')))==len(train)==24)
 start,end,stop=map(ep,('2025-10-01T00:00:00-03:00','2026-07-01T00:00:00-03:00','2026-09-21T00:00:00-03:00'));training=[];replay=[]
 for h in range(1,13):
  target=np.r_[truth[h:],np.full(h,np.nan)];eligible=np.isfinite(d['base_A'])&np.isfinite(d['base_B'])&np.isfinite(target)&np.isfinite(d['features_A'][:,:24]).all(1)&np.isfinite(d['features_B'][:,:24]).all(1)
  for phase,left,right in (('validation',start,end),('test',end,stop)):
   mask=eligible&((t+h*3600<start) if phase=='validation' else ((t+h*3600<start)|((t>=start)&(t+h*3600<end))))
   ck(f'{phase}{h}mask',eq(mask,masks[f'{phase}_h{h}']));ix=np.flatnonzero(mask);y=target[ix]-base[ix];w=1+2*(abs(y)>=1)+2*(target[ix]>=9);before=w.copy();w=1+2*(abs(y)>=1)+2*(target[ix]>=7);changed=(target[ix]>=7)&(target[ix]<9);info=train[phase,h]
   ck(f'{phase}{h}order/cutoff',np.all(np.diff(ix)>0) and len(np.unique(t[ix]))==len(ix) and np.all(t[ix]+h*3600<left))
   ck(f'{phase}{h}parent fields',all(info[k]==v for k,v in oldtrain[phase,h].items() if k not in ('family','weights_sum')) and int(info['n'])==len(ix) and int(info['weights_sum'])==int(sum(w)) and int(info['old_weights_sum'])==int(sum(before)) and float(info['flood_weight_threshold_m'])==7)
   ck(f'{phase}{h}paired saved weights',eq(savedweights[f'{phase}_h{h}_old'],before) and eq(savedweights[f'{phase}_h{h}_new'],w) and eq(w-before,2*changed))
   ck(f'{phase}{h}pre-candidate expectations',eq(ix,expected[f'{phase}_h{h}_indices']) and eq(y,expected[f'{phase}_h{h}_delta']) and eq(before,expected[f'{phase}_h{h}_weights9']) and eq(w,expected[f'{phase}_h{h}_weights7']))
   row=weightplan[phase,h]
   calculated=dict(rows=len(ix),targets_below_7m=int((target[ix]<7).sum()),targets_7_to_9m=int(changed.sum()),targets_ge_9m=int((target[ix]>=9).sum()),old_weights_sum=int(sum(before)),new_weights_sum=int(sum(w)),increase=int(2*changed.sum()))
   ck(f'{phase}{h}weight plan counts',all(int(row[k])==v for k,v in calculated.items()))
   ck(f'{phase}{h}weight bytehash',row['old_weights_sha256']==hashlib.sha256(before.tobytes()).hexdigest() and row['new_weights_sha256']==hashlib.sha256(w.tobytes()).hexdigest())
   model=joblib.load(track(E/'models'/f'{phase}-{h}.joblib'));parent=joblib.load(track(B/'models'/f'{phase}-{F[2]}-{h}.joblib'))
   ck(f'{phase}{h}params',model.get_params()==parent.get_params() and model.n_features_in_==180 and model.n_iter_==180)
   training.append(dict(phase=phase,horizon_h=h,**calculated,indices_sha256=hashlib.sha256(ix.tobytes()).hexdigest(),responses_sha256=hashlib.sha256(y.tobytes()).hexdigest(),old_weights_sha256=hashlib.sha256(before.tobytes()).hexdigest(),new_weights_sha256=hashlib.sha256(w.tobytes()).hexdigest(),original_mixed_inputs_sha256=hashlib.sha256(X[ix].tobytes()).hexdigest()))
   for profile in ('A','B'):
    rr=groups[phase,profile,h];schedule=np.flatnonzero((t>=left)&(t+h*3600<right));ck(f'{phase}{profile}{h}schedule',eq(t[schedule],np.array([ep(r['origin']) for r in rr])))
    bb=d['base_'+profile][schedule];xx=d['features_'+profile][schedule];valid=np.isfinite(bb)
    ck(f'{phase}{profile}{h}truth/base',eq(target[schedule],np.array([num(r['actual_m']) for r in rr])) and eq(bb,np.array([num(r['base_m']) for r in rr])))
    for family in F:
     current=model if family==F[3] else joblib.load(track(B/'models'/f'{phase}-{family}-{h}.joblib'));pred=np.full(len(schedule),np.nan);pred[valid]=current.predict(xx[valid])+bb[valid]
     saved=np.array([num(r[family+'_m']) for r in rr]);ck(f'{phase}{profile}{h}{family}exact original inputs',eq(pred,saved))
     replay.append(dict(phase=phase,profile=profile,horizon_h=h,family=family,scheduled=len(schedule),applied=int(valid.sum()),exact=True,max_difference_m=0.,original_input_sha256=hashlib.sha256(xx[valid].tobytes()).hexdigest()))
 metrics=[]
 for (phase,profile,h),rr in sorted(groups.items()):
  a=np.array([num(r['actual_m']) for r in rr]);complete=np.array([r['complete24']=='True' for r in rr])
  for population in ('full_schedule','complete24','missing24'):
   pop=np.ones(len(rr),bool) if population=='full_schedule' else complete if population=='complete24' else ~complete
   for subset in ('all','level_ge_7m'):
    obs=pop&np.isfinite(a)&(np.ones(len(rr),bool) if subset=='all' else a>=7)
    for family in F:
     p=np.array([num(r[family+'_m']) for r in rr]);pair=obs&np.isfinite(p);err=p[pair]-a[pair];ae=abs(err);nobs=int(obs.sum());npairs=len(err);hits=int((ae<=.5).sum())
     metrics.append(dict(phase=phase,profile=profile,horizon_h=h,population=population,subset=subset,family=family,scheduled_rows=int(pop.sum()),missing_truth=int((pop&~np.isfinite(a)).sum()),observed_targets=nobs,pairs=npairs,failures=nobs-npairs,hits=hits,paired_hit_fraction=hits/npairs if npairs else None,observed_target_hit_fraction=hits/nobs if nobs else None,mae_m=float(ae.mean()) if npairs else None,bias_m=float(err.mean()) if npairs else None,p98_abs_m=float(np.quantile(ae,.98)) if npairs else None,max_abs_m=float(ae.max()) if npairs else None))
 key=lambda r:(r['phase'],r['profile'],int(r['horizon_h']),r['population'],r['subset'],r['family'])
 saved={key(r):r for r in csvrows(E/'evaluation.csv')};oldmetrics={key(r):r for r in csvrows(B/'evaluation.csv')}
 ck('1152 metrics192replays',len(metrics)==len(saved)==1152 and len(replay)==192)
 for r in metrics:
  s=saved[key(r)];ok=True
  for k,v in r.items():ok &= s[k]==v if isinstance(v,str) else s[k]=='' if v is None else abs(float(s[k])-v)<1e-12
  ck('metric '+str(key(r)),ok)
  if r['family'] in F[:3]:ck('parent metric '+str(key(r)),s==oldmetrics[key(r)])
 idx={key(r):r for r in metrics};contrasts=[]
 for r in metrics:
  if r['family']!=F[3] or r['population']!='full_schedule':continue
  for ref in (F[2],F[0] if r['profile']=='A' else F[1]):
   old=idx[(r['phase'],r['profile'],r['horizon_h'],r['population'],r['subset'],ref)]
   contrasts.append(dict(phase=r['phase'],profile=r['profile'],horizon_h=r['horizon_h'],subset=r['subset'],reference=ref,observed_targets=r['observed_targets'],pairs=r['pairs'],failures=r['failures'],old_hits=old['hits'],new_hits=r['hits'],delta_hits=r['hits']-old['hits'],old_mae_m=old['mae_m'],new_mae_m=r['mae_m'],old_max_m=old['max_abs_m'],new_max_m=r['max_abs_m']))
 for path,digest in inputs.items():ck('unchanged '+path,sha(R/path)==digest)
 save('training-reconstruction.csv',training);save('inference-replay.csv',replay);save('independent-metrics.csv',metrics);save('contrasts.csv',contrasts);dump('input-hashes.json',inputs)
 dump('verification.json',dict(passed=True,checked_at_utc=datetime.now(timezone.utc).isoformat(),checks_count=len(checks),checks=checks,models=24,control_applications=144,candidate_applications=48,metrics=1152,rows=204168,paired_weight_vectors=48,timeline_origins=12912,fit_or_network=False,limits=['Serialized HGB does not prove the samples/weights actually consumed during fit; reconstruction, saved paired weights, executed source and hashes provide bounded evidence, no refit.','7m is an analytical threshold, not an official alert criterion; sample reweighting does not guarantee improved precision.','Same development periods already inspected; profiles are paired views.','Recorded local timestamps are not authenticated independent proof of fit timing.','No promotion or operational change.']))
 print('PASS',len(checks),'checks',flush=True)
if __name__=='__main__':
 with threadpool_limits(limits=2):main()
