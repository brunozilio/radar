from pathlib import Path
from datetime import datetime,timezone
import csv,json,hashlib,importlib.metadata
import numpy as np
import joblib
P=Path(__file__).resolve().parent;R=P.parents[1]
checks=[];sources={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(n,v):
 checks.append({'check':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
def inp(p):
 p=R/p;sources[str(p.relative_to(R))]=sha(p);return p
def load(p):return dict(np.load(inp(p)))
def epoch(s):return datetime.fromisoformat(s).timestamp()
def future(a,h):
 out=np.full(len(a),np.nan);out[:-h]=a[h:];return out
def eq(a,b):return np.array_equal(a,b,equal_nan=True)
recent='outputs/radar-matriz-recente-ancora-15min-20260922';new='outputs/radar-matriz-observada-junho2024-20260922';ref='outputs/experimento-radar-observado-120-20260921'
old=load(recent+'/features.npz');add=load(new+'/2024-06-15-features.npz');original=load('outputs/experimento-radar-ausencias-nativas-runtime19-20260921/features.npz');masks=load(ref+'/training-masks.npz')
for x in ['docs/radar-june2024-augmentation-protocol.json','scripts/hydro_radar_june2024_augmentation.py','scripts/hydro_radar_native_missing.py','scripts/hydro_radar_reservoir_features.py','scripts/hydro_routing_fit.py','scripts/hydro_hourly_forecast.py','docs/radar-june2024-observed-features-protocol.json','scripts/hydro_radar_june2024_features.py',recent+'/reference-equivalence.json',new+'/preparation.json']:
 inp(x)
for folder in [recent,new,ref]:
 art=json.loads(inp(folder+'/artifact-hashes.json').read_text())
 for a in art:
  p=R/folder/a['file'];ck(folder+'/'+a['file']+' sealed',sha(p)==a['sha256'])
for x in [recent+'/preparation.json',new+'/preparation.json']:
 d=json.loads(inp(x).read_text())
 for path,digest in d.get('input_sha256',{}).items():ck('preparation source '+path,sha(R/path)==digest)
t,F,b,y=(old[k] for k in ['times','features','base','truth']);nt,NF,nb,ny=(add[k] for k in ['times','features','base','truth'])
start,end,stop,boundary=map(epoch,['2025-10-01T00:00:00-03:00','2026-07-01T00:00:00-03:00','2026-09-21T00:00:00-03:00','2024-06-22T00:00:00-03:00'])
keep=original['times']<stop
ck('fixed120 features exact independent comparison',eq(F,original['features'][keep,:120]))
for k in ['times','base','truth','complete24']:ck(k+' exact original',eq(old[k],original[k][keep]))
ck('recent shape',F.shape==(12912,120));ck('june shape',NF.shape==(168,120));ck('hourly grids',np.all(np.diff(t)==3600) and np.all(np.diff(nt)==3600))
ck('june boundaries',nt[0]==epoch('2024-06-15T00:00:00-03:00') and nt[-1]==boundary-3600)
ck('separate nonoverlapping datasets',nt.max()<t.min());ck('june all bases/truth finite',np.isfinite(nb).all() and np.isfinite(ny).all())
ck('missing Linha Carreiro kept',np.isnan(NF[:,6:12]).all() and np.isnan(NF[:,18:24]).all())
ck('complete24 diagnostic exact',np.array_equal(old['complete24'],np.isfinite(F[:,:24]).all(1)))
ck('june complete24 allfalse',not add['complete24'].any())
meta={(r['phase'],int(r['horizon_h'])):r for r in csv.DictReader(inp(ref+'/training.csv').open())}
rows=list(csv.DictReader(inp(ref+'/predictions.csv').open()));lookup={(r['phase'],r['origin'],int(r['nominal_lead_h'])):r for r in rows}
ck('102084uniqueevaluation keys',len(rows)==len(lookup)==102084)
runtime={n:importlib.metadata.version(n) for n in ('numpy','scipy','scikit-learn','joblib','threadpoolctl')}
ck('runtime same controls',runtime==json.loads(inp(ref+'/experiment.json').read_text())['runtime'])
newcoverage={int(r['horizon_h']):r for r in csv.DictReader(inp(new+'/target-coverage.csv').open())};membership=[];scheduled_count=0
for h in range(1,13):
 target=future(y,h);newtarget=future(ny,h)
 newmask=np.isfinite(nb)&np.isfinite(newtarget)&(nt+h*3600<boundary)
 ck(f'juneh{h} targetcoverage',newmask.sum()==int(newcoverage[h]['pairs'])==168-h)
 ck(f'juneh{h} trailing targetsnan',np.isnan(newtarget[-h:]).all())
 finite=np.isfinite(b)&np.isfinite(target);first=t+h*3600<start;second=(t>=start)&(t+h*3600<end)
 for phase,left,right in [('validation',start,end),('test',end,stop)]:
  mask=finite&(first if phase=='validation' else first|second);m=meta[phase,h]
  ck(f'{phase}h{h} frozenmaskexact',np.array_equal(mask,masks[f'{phase}_h{h}'][keep]) and not masks[f'{phase}_h{h}'][~keep].any())
  ck(f'{phase}h{h} metadata',mask.sum()==int(m['n']))
  ck(f'{phase}h{h} cutoff',np.all(t[mask]+h*3600<epoch(m['cutoff_exclusive'])) and np.all(nt[newmask]+h*3600<epoch(m['cutoff_exclusive'])))
  ck(f'{phase}h{h} allcolumnsfinite somewhere',np.isfinite(np.vstack([NF[newmask],F[mask]])).any(0).all())
  response=np.r_[newtarget[newmask]-nb[newmask],target[mask]-b[mask]];levels=np.r_[newtarget[newmask],target[mask]];weights=1+2*(abs(response)>=1)+2*(levels>=9)
  ck(f'{phase}h{h} targetsfinitemembership',np.isfinite(response).all() and np.isfinite(levels).all())
  ck(f'{phase}h{h} oneorigin',len(set(np.r_[nt[newmask],t[mask]]))==len(response))
  model=joblib.load(inp(ref+f'/models/{phase}-{h}.joblib'));params=model.get_params()
  expected=dict(max_iter=180,max_leaf_nodes=int(m['leaf_nodes']),min_samples_leaf=35,learning_rate=.055,l2_regularization=10,loss=m['loss'],early_stopping=False,random_state=57)
  ck(f'{phase}h{h} params',all(params[k]==v for k,v in expected.items()) and model.n_features_in_==120)
  scheduled=(t>=left)&(t+h*3600<right);idx=np.flatnonzero(scheduled);scheduled_count+=len(idx)
  source=[lookup[(phase,datetime.fromtimestamp(t[i],timezone.utc).astimezone(timezone(__import__('datetime').timedelta(hours=-3))).isoformat(),h)] for i in idx]
  ck(f'{phase}h{h} targetsandbase',all((float(r['actual_m'])==target[i] if np.isfinite(target[i]) else r['actual_m']=='') and (float(r['base_m'])==b[i] if np.isfinite(b[i]) else r['base_m']=='') for i,r in zip(idx,source)))
  ck(f'{phase}h{h} target timestamp',all(epoch(r['target_time'])==t[i]+h*3600 for i,r in zip(idx,source)))
  ck(f'{phase}h{h} frozenavailability',all(bool(r['observed_only_m'])==bool(np.isfinite(b[i])) for i,r in zip(idx,source)))
  membership.append(dict(phase=phase,horizon_h=h,recent=int(mask.sum()),added=int(newmask.sum()),added_ge7=int((newtarget[newmask]>=7).sum()),combined=len(response),weight_sum=int(weights.sum()),added_weight_sum=int(weights[:newmask.sum()].sum()),latest_target_epoch=float((t[mask]+h*3600).max()),schedule=len(idx)))
ck('schedule102084',scheduled_count==102084)
from threadpoolctl import threadpool_limits
import math
E=R/'outputs/experimento-radar-historico-junho2024-20260922'
def jload(p):sources[str(p.relative_to(R))]=sha(p);return json.loads(p.read_text())
def csvload(p):sources[str(p.relative_to(R))]=sha(p);return list(csv.DictReader(p.open()))
def fnum(s):return float(s) if s not in ('',None) else float('nan')
def writecsv(name,data):
 with (P/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=data[0]);w.writeheader();w.writerows(data)
def savejson(name,data):(P/name).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
art=jload(E/'artifact-hashes.json')
for a in art:ck('experiment artifact '+a['file'],sha(E/a['file'])==a['sha256'])
experiment=jload(E/'experiment.json');prefit=jload(E/'prefit-manifest.json')
ck('same prefit and final inputhashes',prefit['input_sha256']==experiment['input_sha256'])
for path,digest in prefit['input_sha256'].items():ck('experiment input '+path,sha(Path(path))==digest)
for name,digest in prefit['artifacts'].items():ck('prefit saved artifact '+name,sha(E/name)==digest)
review=jload(R/'outputs/revisao-protocolo-junho2024-20260922/verification.json')
ck('review before prefit',datetime.fromisoformat(review['reviewed_utc'])<datetime.fromisoformat(prefit['created_at']))
reviewhashes=jload(R/'outputs/revisao-protocolo-junho2024-20260922/input-hashes.json')
ck('executed source reviewed',sha(E/'code/hydro_radar_june2024_augmentation.py')==reviewhashes['scripts/hydro_radar_june2024_augmentation.py'])
ck('protocol reviewed',sha(E/'protocol.json')==reviewhashes['docs/radar-june2024-augmentation-protocol.json'])
ck('modelmtimeafterprefit',all(p.stat().st_mtime>=datetime.fromisoformat(prefit['created_at']).timestamp() for p in (E/'models').glob('*.joblib')))
ck('runtime experiment',experiment['runtime']==runtime)
pm=dict(np.load(inp(str((E/'prefit-masks.npz').relative_to(R)))));finalm=dict(np.load(inp(str((E/'training-masks.npz').relative_to(R)))));pv=dict(np.load(inp(str((E/'prefit-vectors.npz').relative_to(R)))))
ck('36 masks',len(pm)==len(finalm)==36 and set(pm)==set(finalm))
for k in pm:ck('prefit final maskexact '+k,eq(pm[k],finalm[k]))
ck('72vectors',len(pv)==72)
plans={(r['phase'],int(r['horizon_h'])):r for r in csvload(E/'prefit-plan.csv')}
training={(r['phase'],int(r['horizon_h'])):r for r in csvload(E/'training.csv')};ck('24plans24training',len(plans)==len(training)==24)
for h in range(1,13):
 target=future(y,h);newtarget=future(ny,h);nm=np.isfinite(nb)&np.isfinite(newtarget)&(nt+h*3600<boundary)
 ck('independent newmask'+str(h),eq(nm,pm[f'new_h{h}']))
 finite=np.isfinite(b)&np.isfinite(target);first=t+h*3600<start;second=(t>=start)&(t+h*3600<end)
 for phase in ['validation','test']:
  mask=finite&(first if phase=='validation' else first|second);ck('independent recentmask'+phase+str(h),eq(mask,pm[f'{phase}_original_h{h}']))
  response=np.r_[newtarget[nm]-nb[nm],target[mask]-b[mask]];level=np.r_[newtarget[nm],target[mask]];weight=1+2*(abs(response)>=1)+2*(level>=9)
  for field,arr in [('response',response),('level',level),('weight',weight)]:ck('independent vector'+phase+str(h)+field,eq(arr,pv[f'{phase}_h{h}_{field}']))
  plan=plans[phase,h];tr=training[phase,h];metadata=meta[phase,h]
  ck('plan'+phase+str(h),int(plan['recent_n'])==mask.sum() and int(plan['added_n'])==nm.sum() and int(plan['weight_sum'])==weight.sum() and epoch(plan['latest_target'])==(t[mask]+h*3600).max())
  ck('training'+phase+str(h),int(tr['original_n'])==mask.sum() and int(tr['added_n'])==nm.sum() and int(tr['n'])==len(response) and int(tr['features'])==120 and tr['loss']==metadata['loss'] and int(tr['leaf_nodes'])==int(metadata['leaf_nodes']) and tr['latest_training_target']==metadata['latest_training_target'] and tr['cutoff_exclusive']==metadata['cutoff_exclusive'])
  ck('training extrema'+phase+str(h),float(tr['combined_response_min_m'])==response.min() and float(tr['combined_response_max_m'])==response.max() and int(tr['added_targets_ge_7m'])==(newtarget[nm]>=7).sum() and epoch(tr['latest_added_target'])==(nt[nm]+h*3600).max())
  model=joblib.load(inp(str((E/f'models/{phase}-{h}.joblib').relative_to(R))));control=joblib.load(R/ref/f'models/{phase}-{h}.joblib')
  ck('full configcandidate'+phase+str(h),model.get_params()==control.get_params() and model.n_features_in_==120)
# All targets/base/key availability and stored baseline must match the previous experiment exactly.
pr=csvload(E/'predictions.csv');ck('predictions102084',len(pr)==102084)
def rowkey(r):return r['phase'],r['origin'],int(r['nominal_lead_h'])
ck('sameallkeys',list(map(rowkey,pr))==list(map(rowkey,rows)))
for field in ['actual_m','base_m','target_time']:
 ck('reference identity '+field,all(r[field]==s[field] for r,s in zip(pr,rows)))
ck('frozenpredictionsexact',eq(np.array([fnum(r['native_control_m']) for r in pr]),np.array([fnum(r['observed_only_m']) for r in rows])))
ck('sameavailability',all(bool(r['native_control_m'])==bool(r['augmented_m']) for r in pr))
replays=[];bypair={}
with threadpool_limits(limits=2):
 for phase,left,right in [('validation',start,end),('test',end,stop)]:
  for h in range(1,13):
   rr=[r for r in pr if r['phase']==phase and int(r['nominal_lead_h'])==h];bypair[phase,h]=rr
   inds=np.flatnonzero((t>=left)&(t+h*3600<right));ck('originorder'+phase+str(h),np.array_equal(np.array([epoch(r['origin']) for r in rr]),t[inds]))
   ck('complete24'+phase+str(h),np.array_equal(np.array([r['original_complete24']=='True' for r in rr]),old['complete24'][inds]))
   finite=np.isfinite(b[inds]);ap=inds[finite]
   for family,path in [('native_control',R/ref/f'models/{phase}-{h}.joblib'),('augmented',E/f'models/{phase}-{h}.joblib')]:
    model=joblib.load(path);value=model.predict(F[ap])+b[ap];stored=np.array([fnum(r[family+'_m']) for r in rr]);ck('replayexact '+phase+str(h)+family,np.array_equal(value,stored[finite]));ck('replaymissing '+phase+str(h)+family,np.isnan(stored[~finite]).all())
    replays.append(dict(phase=phase,horizon_h=h,family=family,scheduled=len(rr),applied=len(ap),missing_base=int((~finite).sum()),exact=True,max_difference_m=float(np.max(abs(value-stored[finite]))) if len(value) else 0.))
   print('replayed',phase,h,flush=True)
metrics=[];denominators=[]
original_eval=csvload(E/'evaluation.csv');ev={(r['phase'],int(r['horizon_h']),r['subset'],r['population'],r['family']):r for r in original_eval};ck('288unique metrics',len(original_eval)==len(ev)==288)
for (phase,h),rr in bypair.items():
 for population in ['full_schedule','complete24','missing24']:
  group=[r for r in rr if population=='full_schedule' or (r['original_complete24']=='True')==(population=='complete24')]
  truth=np.array([fnum(r['actual_m']) for r in group]);observed=np.isfinite(truth);below=observed&(truth<7);high=observed&(truth>=7)
  denominators.append(dict(phase=phase,horizon_h=h,population=population,scheduled=len(group),unknown_truth=int((~observed).sum()),observed_below7=int(below.sum()),observed_ge7=int(high.sum()),missing_base=int(sum(not r['base_m'] for r in group))))
  ck('denominatorpartition'+phase+str(h)+population,int((~observed).sum()+below.sum()+high.sum())==len(group))
  for subset,mask in [('all',observed),('level_ge_7m',high)]:
   for family in ['native_control','augmented']:
    pred=np.array([fnum(r[family+'_m']) for r in group]);paired=mask&np.isfinite(pred);err=pred[paired]-truth[paired];ae=abs(err);hits=int((ae<=.5).sum());n=int(paired.sum());obs=int(mask.sum())
    row=dict(phase=phase,horizon_h=h,subset=subset,population=population,family=family,scheduled_rows=len(group),observed_targets=obs,n=n,failures=obs-n,hits=hits,hit_fraction=hits/n if n else None,observed_target_hit_fraction=hits/obs if obs else None,mae_m=float(ae.mean()) if n else None,bias_m=float(err.mean()) if n else None,p98_abs_m=float(np.quantile(ae,.98)) if n else None,max_abs_m=float(ae.max()) if n else None)
    saved=ev[phase,h,subset,population,family]
    for k in ['scheduled_rows','observed_targets','n','failures','hits']:ck('metriccount'+str((phase,h,subset,population,family,k)),int(saved[k])==row[k])
    for k in ['hit_fraction','observed_target_hit_fraction','mae_m','bias_m','p98_abs_m','max_abs_m']:ck('metricfloat'+str((phase,h,subset,population,family,k)),saved[k]=='' if row[k] is None else abs(float(saved[k])-row[k])<=1e-12)
    metrics.append(row)
# Verify frozen files again after inference/read operations.
for a in art:ck('end artifacthash'+a['file'],sha(E/a['file'])==a['sha256'])
for path,digest in experiment['input_sha256'].items():ck('end inputhash'+path,sha(Path(path))==digest)
contrasts=[]
mm={(r['phase'],r['horizon_h'],r['subset'],r['population'],r['family']):r for r in metrics}
for phase in ['validation','test']:
 for h in range(1,13):
  a=mm[phase,h,'level_ge_7m','full_schedule','native_control'];z=mm[phase,h,'level_ge_7m','full_schedule','augmented']
  contrasts.append(dict(phase=phase,horizon_h=h,observed=a['observed_targets'],pairs=a['n'],failures=a['failures'],control_hits=a['hits'],augmented_hits=z['hits'],delta_hits=z['hits']-a['hits'],control_mae=a['mae_m'],augmented_mae=z['mae_m'],control_max=a['max_abs_m'],augmented_max=z['max_abs_m']))
for name,data in [('membership.csv',membership),('replay.csv',replays),('metrics-independent.csv',metrics),('denominator-partition.csv',denominators),('flood-contrasts.csv',contrasts)]:writecsv(name,data)
savejson('input-hashes.json',sources)
savejson('verification.json',{'passed':True,'check_count':len(checks),'checks':checks,'exact_replays':len(replays),'metrics_recomputed':len(metrics),'mask_arrays_verified':len(pm),'vectors_verified':len(pv),'plans_verified':len(plans),'artifact_hashes_verified_start_and_end':len(art),'experiment_input_hashes_verified_start_and_end':len(experiment['input_sha256']),'fits':0,'threads':2,'runtime':runtime,'recorded_utc':datetime.now(timezone.utc).isoformat(),'limits':['HGB artifact alone does not prove consumed optimizer weights; evidence combines source, prefit artifacts, config and replay.','Filesystem mtime supports prefit-before-save only; not an independent execution timestamp certificate.','This is reused development data, no promotion or accuracy98 certification.']})
print('PASS',len(checks),'checks;',len(replays),'exact replays;',len(metrics),'metrics',flush=True)
