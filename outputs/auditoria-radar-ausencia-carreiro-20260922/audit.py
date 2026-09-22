"""Read-only missingness audit: no estimator, inference, fit or network."""
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
import numpy as np
import csv,json,hashlib
P=Path(__file__).resolve().parent;R=P.parents[1];B=R/'outputs/experimento-radar-mistura-atrasos-20260922'
inputs={};checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tr(p):inputs[str(p.relative_to(R))]=sha(p);return p
def read(p):return list(csv.DictReader(tr(p).open()))
def ck(n,b):checks.append(dict(check=n,passed=bool(b)));assert b,n
def dump(n,v):(P/n).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def save(n,r):
 with (P/n).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(r[0]));w.writeheader();w.writerows(r)
def eq(a,b):return np.array_equal(a,b,equal_nan=True)
def epoch(v):return datetime.fromisoformat(v).timestamp()
def count(block,mask,**labels):
 vals=block[mask];missing=(~np.isfinite(vals)).sum(1);n=len(vals)
 return dict(**labels,rows=n,complete=int((missing==0).sum()),partial_missing=int(((missing>0)&(missing<6)).sum()),all_six_missing=int((missing==6).sum()),any_missing=int((missing>0).sum()),any_missing_fraction=float((missing>0).mean()) if n else None,**{f'column_{18+i}_missing':int((~np.isfinite(vals[:,i])).sum()) for i in range(6)})
def main():
 source=tr(R/'scripts/hydro_latency_forecast.py');text=source.read_text()
 ck('station order and derivative contract',"['86510000','86472000','86472600','86500000']" in text and 'for hours in [.5,1,2,4,8]' in text and '(v-shift(v,int(hours*4)))/hours' in text)
 for r in json.loads(tr(B/'artifact-hashes.json').read_text()):ck('parent hash '+r['file'],sha(tr(B/r['file']))==r['sha256'])
 d=dict(np.load(tr(B/'prepared-inputs.npz')));masks=dict(np.load(tr(B/'training-masks.npz')));t=d['times'];truth=d['truth'];n=len(t)
 ck('assignment',eq(d['assignment'],np.random.Generator(np.random.PCG64(57)).integers(0,2,size=n,dtype=np.int8)))
 blocks={};recon=[]
 for profile,folder in {'A':'mucum-hourly-20260922T000704-0300','B':'mucum-hourly-20260922T010016-0300'}.items():
  folder=R/'outputs'/folder;z=dict(np.load(tr(folder/'history/ana-86500000.npz')));age=next(r for r in read(folder/'idades-fontes.csv') if r['source']=='86500000');delay=float(age['delay_minutes'])*60
  ck(profile+'delay30',delay==1800);ck(profile+'sorted unique',np.all(np.diff(z['times'])>0));sample={}
  for offset in (0,.5,1,2,4,8):
   v=np.full(n,np.nan);pointer=-1
   for i,origin in enumerate(t):
    query=origin-offset*3600-delay
    while pointer+1<len(z['times']) and z['times'][pointer+1]<=query:pointer+=1
    if pointer>=0 and query-z['times'][pointer]<=900:v[i]=z['level'][pointer]
   v[t<t[0]+offset*3600]=np.nan;sample[offset]=v
  reconstructed=np.column_stack([sample[0]]+[(sample[0]-sample[h])/h for h in (.5,1,2,4,8)])
  blocks[profile]=d['features_'+profile][:,18:24];ck(profile+'six columns exact',eq(reconstructed,blocks[profile]));recon.append(dict(profile=profile,rows=n,cells=n*6,delay_minutes=delay/60,exact=True))
 ck('Carreiro blocks identical A/B',eq(blocks['A'],blocks['B']))
 blocks['mixed']=blocks['A'].copy();blocks['mixed'][d['assignment']==1]=blocks['B'][d['assignment']==1]
 start,end,stop=map(epoch,('2025-10-01T00:00:00-03:00','2026-07-01T00:00:00-03:00','2026-09-21T00:00:00-03:00'))
 training=[];evaluation=[];overall=[]
 for profile,block in blocks.items():overall.append(count(block,np.ones(n,bool),profile=profile,population='all_pre_stop_origins'))
 for h in range(1,13):
  target=np.r_[truth[h:],np.full(h,np.nan)]
  common=np.isfinite(d['base_A'])&np.isfinite(d['base_B'])&np.isfinite(target)&np.isfinite(d['features_A'][:,:24]).all(1)&np.isfinite(d['features_B'][:,:24]).all(1)
  for phase,left,right in (('validation',start,end),('test',end,stop)):
   mask=common&((t+h*3600<start) if phase=='validation' else ((t+h*3600<start)|((t>=start)&(t+h*3600<end))))
   ck(f'{phase}{h}mask',eq(mask,masks[f'{phase}_h{h}']))
   for profile,block in blocks.items():
    for subset in ('all','observed_ge_7m'):
     chosen=mask if subset=='all' else mask&(target>=7)
     training.append(count(block,chosen,phase=phase,horizon_h=h,profile=profile,subset=subset))
   scheduled=(t>=left)&(t+h*3600<right)
   for profile in ('A','B'):
    base=d['base_'+profile]
    for subset,select in [('scheduled',scheduled),('truth_observed',scheduled&np.isfinite(target)),('truth_missing',scheduled&~np.isfinite(target)),('paired_base_target',scheduled&np.isfinite(target)&np.isfinite(base)),('observed_ge_7m',scheduled&(target>=7)),('paired_ge_7m',scheduled&(target>=7)&np.isfinite(base))]:
     evaluation.append(count(blocks[profile],select,phase=phase,horizon_h=h,profile=profile,subset=subset))
 ck('no training absence',all(r['any_missing']==0 for r in training))
 ck('all validation high blocks complete',all(r['any_missing']==0 for r in evaluation if r['phase']=='validation' and r['subset']=='observed_ge_7m'))
 rows=read(B/'predictions.csv');groups=defaultdict(list)
 for r in rows:groups[r['phase'],r['profile'],int(r['nominal_lead_h'])].append(r)
 for (phase,profile,h),rr in groups.items():
  scheduled=next(r for r in evaluation if (r['phase'],r['profile'],r['horizon_h'],r['subset'])==(phase,profile,h,'scheduled'))
  ck('schedulecount'+str((phase,profile,h)),len(rr)==scheduled['rows'])
  ix=np.array([np.flatnonzero(t==epoch(r['origin']))[0] for r in rr]);ck('scheduledorigins'+str((phase,profile,h)),eq(t[ix],t[(t>=(start if phase=='validation' else end))&(t+h*3600<(end if phase=='validation' else stop))]))
 for path,digest in inputs.items():ck('unchanged '+path,sha(R/path)==digest)
 save('training-missingness.csv',training);save('evaluation-missingness.csv',evaluation);save('overall-missingness.csv',overall);dump('column-reconstruction.json',recon);dump('input-hashes.json',inputs)
 dump('verification.json',dict(passed=True,checked_at_utc=datetime.now(timezone.utc).isoformat(),checks_count=len(checks),checks=checks,columns=[dict(index=i,name=name,units='m' if i==18 else 'm/hour_nominal') for i,name in zip(range(18,24),('86500000:H','86500000:dH0.5','86500000:dH1','86500000:dH2','86500000:dH4','86500000:dH8'))],training_groups=len(training),evaluation_groups=len(evaluation),candidate_inspected=False,inference_fit_network=False))
 print('PASS',len(checks),'checks');print(json.dumps(overall,indent=2))
if __name__=='__main__':main()
