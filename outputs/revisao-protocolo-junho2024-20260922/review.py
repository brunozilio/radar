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
with (P/'membership-review.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=membership[0]);w.writeheader();w.writerows(membership)
(P/'input-hashes.json').write_text(json.dumps(sources,indent=2)+'\n')
(P/'verification.json').write_text(json.dumps({'passed':True,'checks':len(checks),'check_details':checks,'runtime':runtime,'fits':0,'predictions_executed':0,'models_config_only_inspected':24,'blocking_bug_found':False,'reviewed_utc':datetime.now(timezone.utc).isoformat()},indent=2)+'\n')
print('Passed',len(checks),'checks; nofit/noinference;24configs inspected.')
