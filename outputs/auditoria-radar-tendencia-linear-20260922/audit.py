"""Independent audit: no fit, operational imports or network."""
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
import csv,json,hashlib,importlib.metadata
import numpy as np,joblib
from threadpoolctl import threadpool_limits
P=Path(__file__).resolve().parent;R=P.parents[1]
E=R/'outputs/experimento-radar-tendencia-linear-20260922';B=R/'outputs/experimento-radar-mistura-atrasos-20260922'
F=('profile_A_control','profile_B_control','mixed_profile_candidate','linear_trend_only','linear_trend_hybrid')
C=np.array([i for i in range(24) if i%6!=0]); inputs={};checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tr(p):inputs[str(p.relative_to(R))]=sha(p);return p
def js(p):return json.loads(tr(p).read_text())
def rd(p):return list(csv.DictReader(tr(p).open()))
def nz(p):return dict(np.load(tr(p)))
def ck(n,b):checks.append(dict(check=n,passed=bool(b)));assert b,n
def eq(a,b):return np.array_equal(a,b,equal_nan=True)
def num(v):return float(v) if v not in ('',None) else np.nan
def ep(v):return datetime.fromisoformat(v).timestamp()
def dump(n,v):(P/n).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def save(n,rows):
 with (P/n).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 exp=js(E/'experiment.json');pre=js(E/'pre-fit-manifest.json');proto=js(E/'protocol.json')
 ck('protocol registered hash',sha(E/'protocol.json')=='523a56df3d6fe52a7ef856bf5f2d22be17f31a2b2f2f471a63d5592f23b2a613')
 ck('timestamps',proto['registered_at_utc']<pre['recorded_at_utc']<exp['finished_at_utc'])
 ck('runtime',exp['runtime']==pre['runtime']=={k:importlib.metadata.version(k) for k in exp['runtime']})
 ck('20 columns',eq(C,np.array(pre['slope_indices'])))
 for meta in (exp,pre):
  for path,digest in meta['input_sha256'].items():ck('input '+path,sha(tr(R/path))==digest)
 for folder in (B,E):
  for item in js(folder/'artifact-hashes.json'):ck('artifact '+str(folder.name)+'/'+item['file'],sha(tr(folder/item['file']))==item['sha256'])
 ck('executed source copy',sha(E/'code/hydro_radar_linear_trend_hybrid.py')==sha(tr(R/'scripts/hydro_radar_linear_trend_hybrid.py')))
 d=nz(B/'prepared-inputs.npz');masks=nz(B/'training-masks.npz');t=d['times'];truth=d['truth'];assign=d['assignment'];n=len(t)
 ck('PCG64 counts',eq(assign,np.random.Generator(np.random.PCG64(57)).integers(0,2,size=n,dtype=np.int8)) and (assign==0).sum()==6408 and (assign==1).sum()==6504)
 X=d['features_A'].copy();X[assign==1]=d['features_B'][assign==1];base=d['base_A'].copy();base[assign==1]=d['base_B'][assign==1]
 rows=rd(E/'predictions.csv');oldrows=rd(B/'predictions.csv')
 ck('all parent row fields exact',len(rows)==len(oldrows)==204168 and all(all(r[k]==v for k,v in old.items()) for r,old in zip(rows,oldrows)))
 groups=defaultdict(list)
 for r in rows:groups[r['phase'],r['profile'],int(r['nominal_lead_h'])].append(r)
 oldtrain={(r['phase'],int(r['horizon_h'])):r for r in rd(B/'training.csv') if r['family']==F[2]}
 train={(r['phase'],int(r['horizon_h'])):r for r in rd(E/'training.csv')}
 coef={(r['phase'],int(r['horizon_h']),int(r['input_column'])):r for r in rd(E/'coefficients.csv')}
 ck('bundle count',len(list((E/'models').glob('*.joblib')))==len(train)==24 and len(coef)==480)
 start,end,stop=map(ep,('2025-10-01T00:00:00-03:00','2026-07-01T00:00:00-03:00','2026-09-21T00:00:00-03:00'))
 trainout=[];replays=[];samplehash=[]
 for h in range(1,13):
  target=np.r_[truth[h:],np.full(h,np.nan)];eligible=np.isfinite(d['base_A'])&np.isfinite(d['base_B'])&np.isfinite(target)&np.isfinite(d['features_A'][:,:24]).all(1)&np.isfinite(d['features_B'][:,:24]).all(1)
  for phase,left,right in (('validation',start,end),('test',end,stop)):
   mask=eligible & ((t+h*3600<start) if phase=='validation' else ((t+h*3600<start)|((t>=start)&(t+h*3600<end))))
   ck(f'{phase}{h}mask',eq(mask,masks[f'{phase}_h{h}']));ix=np.flatnonzero(mask);y=target[ix]-base[ix];w=1+2*(abs(y)>=1)+2*(target[ix]>=9)
   ck(f'{phase}{h}cutoff/order',np.all(t[ix]+h*3600<left) and np.all(np.diff(ix)>0))
   info=train[phase,h];parentinfo=oldtrain[phase,h]
   ck(f'{phase}{h}parenttraining',all(info[k]==v for k,v in parentinfo.items() if k!='family') and int(info['n'])==len(ix) and int(info['weights_sum'])==int(w.sum()))
   b=joblib.load(tr(E/'models'/f'{phase}-{h}.joblib'));parent=joblib.load(tr(B/'models'/f'{phase}-{F[2]}-{h}.joblib'))
   ck(f'{phase}{h}params',eq(b['indices'],C) and b['ridge'].alpha==1000 and b['ridge'].fit_intercept and b['ridge'].solver=='cholesky' and b['ridge'].n_features_in_==20 and b['tree'].n_features_in_==180 and b['tree'].get_params()==parent.get_params() and b['tree'].n_iter_==180)
   slopes=X[ix][:,C];ck(f'{phase}{h}finite slopes',np.isfinite(slopes).all())
   median=np.quantile(slopes,.5,axis=0);mu=np.sum(slopes*w[:,None],axis=0)/sum(w);variance=np.sum(w[:,None]*(slopes-mu)**2,axis=0)/sum(w);scale=np.sqrt(variance);scale[variance==0]=1
   ck(f'{phase}{h}trainstats',eq(median,b['median']) and np.allclose(mu,b['scaler'].mean_,atol=2e-13,rtol=1e-13) and np.allclose(variance,b['scaler'].var_,atol=2e-13,rtol=1e-13) and np.allclose(scale,b['scaler'].scale_,atol=2e-13,rtol=1e-13) and b['scaler'].n_samples_seen_==sum(w))
   # Use independently reconstructed moments, not scaler.transform, for objective.
   z=(slopes-mu)/scale;fitted=z@b['ridge'].coef_+b['ridge'].intercept_;resid=fitted-y
   gradient=z.T@(w*resid)+1000*b['ridge'].coef_;intercept=float(w@resid)
   ck(f'{phase}{h}ridge stationarity',max(abs(gradient))<1e-7 and abs(intercept)<1e-7)
   native=b['ridge'].predict(b['scaler'].transform(slopes));ck(f'{phase}{h}linear train reconstruction',np.allclose(fitted,native,rtol=0,atol=1e-11))
   for j,col in enumerate(C):
    saved=coef[phase,h,int(col)]
    for k,v in dict(median=median[j],mean=mu[j],scale=scale[j],standardized_coefficient=b['ridge'].coef_[j],original_unit_coefficient=b['ridge'].coef_[j]/scale[j]).items():ck(f'{phase}{h}coefficient{col}{k}',abs(float(saved[k])-v)<1e-11)
   trainout.append(dict(phase=phase,horizon_h=h,n=len(ix),weights_sum=int(sum(w)),mean_max_difference=float(max(abs(mu-b['scaler'].mean_))),scale_max_difference=float(max(abs(scale-b['scaler'].scale_))),normal_gradient_max=float(max(abs(gradient))),intercept_gradient=intercept,linear_train_max_difference=float(max(abs(fitted-native)))))
   samplehash.append(dict(phase=phase,horizon_h=h,indices_sha256=hashlib.sha256(ix.tobytes()).hexdigest(),weights_sha256=hashlib.sha256(w.tobytes()).hexdigest(),response_sha256=hashlib.sha256(y.tobytes()).hexdigest(),reconstructed_residual_sha256=hashlib.sha256((y-fitted).tobytes()).hexdigest(),original_tree_input_sha256=hashlib.sha256(X[ix].tobytes()).hexdigest()))
   for profile in ('A','B'):
    rr=groups[phase,profile,h];scheduled=np.flatnonzero((t>=left)&(t+h*3600<right));rowtimes=np.array([ep(r['origin']) for r in rr]);ck(f'{phase}{profile}{h}schedule',eq(t[scheduled],rowtimes))
    bb=d['base_'+profile][scheduled];actual=np.array([num(r['actual_m']) for r in rr]);ck(f'{phase}{profile}{h}target/base',eq(target[scheduled],actual) and eq(bb,np.array([num(r['base_m']) for r in rr])))
    valid=np.isfinite(bb);xx=d['features_'+profile][scheduled[valid]];slopes=xx[:,C];imputed=np.where(np.isfinite(slopes),slopes,median)
    linear=(imputed-b['scaler'].mean_)/b['scaler'].scale_@b['ridge'].coef_+b['ridge'].intercept_
    tree=b['tree'].predict(xx);native_linear=b['ridge'].predict(b['scaler'].transform(imputed))
    for family in F:
     p=np.full(len(rr),np.nan)
     if family in F[:3]:
      m=joblib.load(tr(B/'models'/f'{phase}-{family}-{h}.joblib'));p[valid]=m.predict(xx)+bb[valid]
     elif family==F[3]:p[valid]=bb[valid]+linear
     else:p[valid]=bb[valid]+linear+tree
     saved=np.array([num(r[family+'_m']) for r in rr]);ck(f'{phase}{profile}{h}{family}NaNs',eq(np.isnan(p),np.isnan(saved)))
     diff=float(np.max(abs(p[valid]-saved[valid])))
     ck(f'{phase}{profile}{h}{family}manual prediction',diff==0 if family in F[:3] else diff<1e-10)
     if family in F[3:]:
      nativepred=bb[valid]+native_linear+(tree if family==F[4] else 0)
      ck(f'{phase}{profile}{h}{family}native exact',eq(nativepred,saved[valid]))
     replays.append(dict(phase=phase,profile=profile,horizon_h=h,family=family,scheduled=len(rr),applied=int(valid.sum()),imputed_slope_cells=int((~np.isfinite(slopes)).sum()),manual_max_difference_m=diff,native_exact=True))
 metrics=[]
 for (phase,profile,h),rr in sorted(groups.items()):
  a=np.array([num(r['actual_m']) for r in rr]);complete=np.array([r['complete24']=='True' for r in rr])
  for popname in ('full_schedule','complete24','missing24'):
   pop=np.ones(len(rr),bool) if popname=='full_schedule' else complete if popname=='complete24' else ~complete
   for subset in ('all','level_ge_7m'):
    obs=pop&np.isfinite(a)&(np.ones(len(rr),bool) if subset=='all' else a>=7)
    for family in F:
     p=np.array([num(r[family+'_m']) for r in rr]);pair=obs&np.isfinite(p);err=p[pair]-a[pair];ae=abs(err);nobs=int(obs.sum());n=len(err);hits=int((ae<=.5).sum())
     metrics.append(dict(phase=phase,profile=profile,horizon_h=h,population=popname,subset=subset,family=family,scheduled_rows=int(pop.sum()),missing_truth=int((pop&~np.isfinite(a)).sum()),observed_targets=nobs,pairs=n,failures=nobs-n,hits=hits,paired_hit_fraction=hits/n if n else None,observed_target_hit_fraction=hits/nobs if nobs else None,mae_m=float(ae.mean()) if n else None,bias_m=float(err.mean()) if n else None,p98_abs_m=float(np.quantile(ae,.98)) if n else None,max_abs_m=float(ae.max()) if n else None))
 key=lambda r:(r['phase'],r['profile'],int(r['horizon_h']),r['population'],r['subset'],r['family'])
 saved={key(r):r for r in rd(E/'evaluation.csv')};parentmetrics={key(r):r for r in rd(B/'evaluation.csv')}
 ck('1440metrics240replays',len(metrics)==len(saved)==1440 and len(replays)==240)
 for r in metrics:
  s=saved[key(r)];ok=True
  for k,v in r.items():ok &= s[k]==v if isinstance(v,str) else s[k]=='' if v is None else abs(float(s[k])-v)<1e-12
  ck('metric '+str(key(r)),ok)
  if r['family'] in F[:3]:ck('controlmetric '+str(key(r)),s==parentmetrics[key(r)])
 idx={key(r):r for r in metrics};contrasts=[]
 for r in metrics:
  if r['population']!='full_schedule' or r['family'] not in F[3:]:continue
  for ref in (F[2],F[0] if r['profile']=='A' else F[1]):
   old=idx[(r['phase'],r['profile'],r['horizon_h'],r['population'],r['subset'],ref)]
   contrasts.append(dict(phase=r['phase'],profile=r['profile'],horizon_h=r['horizon_h'],subset=r['subset'],family=r['family'],reference=ref,observed_targets=r['observed_targets'],pairs=r['pairs'],failures=r['failures'],old_hits=old['hits'],new_hits=r['hits'],delta_hits=r['hits']-old['hits'],old_mae_m=old['mae_m'],new_mae_m=r['mae_m'],old_max_m=old['max_abs_m'],new_max_m=r['max_abs_m']))
 for path,digest in inputs.items():ck('unchanged '+path,sha(R/path)==digest)
 save('training-equation-checks.csv',trainout);save('training-sample-hashes.csv',samplehash);save('inference-replay.csv',replays);save('independent-metrics.csv',metrics);save('contrasts.csv',contrasts);dump('input-hashes.json',inputs)
 dump('verification.json',dict(passed=True,checked_at_utc=datetime.now(timezone.utc).isoformat(),checks_count=len(checks),checks=checks,model_bundles=24,control_applications=144,new_output_applications=96,metrics=1440,rows=204168,fit_or_network=False,limits=['Median unweighted; mean/variance weighted. Statistics trained only on complete shared training masks.','No fit performed. HGB serialization does not prove actual sample weights/residual labels used by optimizer; evidence is executed source, hashes and reconstructed declared inputs.','Protocol and pre-fit timestamps are local recorded metadata, not independently authenticated execution timing.','Prior inspected development periods and paired profiles; no independent generalization proof or promotion.']))
 print('PASS',len(checks),'checks',flush=True)
if __name__=='__main__':
 with threadpool_limits(limits=2):main()
