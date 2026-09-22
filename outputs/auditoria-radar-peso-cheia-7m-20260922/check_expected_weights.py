"""Pre-candidate counts only: no fitting, prediction, or network."""
from pathlib import Path
from datetime import datetime,timezone
import csv,json,hashlib
import numpy as np
P=Path(__file__).resolve().parent;R=P.parents[1];B=R/'outputs/experimento-radar-mistura-atrasos-20260922';inputs={};checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tr(p):inputs[str(p.relative_to(R))]=sha(p);return p
def ck(n,b):checks.append(dict(check=n,passed=bool(b)));assert b,n
def dump(n,v):(P/n).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def main():
 for item in json.loads(tr(B/'artifact-hashes.json').read_text()):ck('parenthash '+item['file'],sha(tr(B/item['file']))==item['sha256'])
 d=dict(np.load(tr(B/'prepared-inputs.npz')));masks=dict(np.load(tr(B/'training-masks.npz')));t=d['times'];truth=d['truth'];assignment=d['assignment'];n=len(t)
 ck('PCG64(57)',np.array_equal(assignment,np.random.Generator(np.random.PCG64(57)).integers(0,2,size=n,dtype=np.int8)))
 base=d['base_A'].copy();base[assignment==1]=d['base_B'][assignment==1]
 start,end=[datetime.fromisoformat(s).timestamp() for s in ('2025-10-01T00:00:00-03:00','2026-07-01T00:00:00-03:00')]
 meta={(r['phase'],int(r['horizon_h'])):r for r in csv.DictReader(tr(B/'training.csv').open()) if r['family']=='mixed_profile_candidate'}
 out=[];vectors={}
 for h in range(1,13):
  target=np.r_[truth[h:],np.full(h,np.nan)];admissible=np.isfinite(d['base_A'])&np.isfinite(d['base_B'])&np.isfinite(target)&np.isfinite(d['features_A'][:,:24]).all(1)&np.isfinite(d['features_B'][:,:24]).all(1)
  for phase in ('validation','test'):
   mask=admissible&((t+h*3600<start) if phase=='validation' else ((t+h*3600<start)|((t>=start)&(t+h*3600<end))))
   ck(f'{phase}h{h}mask',np.array_equal(mask,masks[f'{phase}_h{h}']));ix=np.flatnonzero(mask);y=target[ix];delta=y-base[ix]
   low=y<7;middle=(y>=7)&(y<9);high=y>=9;w9=1+2*(abs(delta)>=1)+2*high;w7=1+2*(abs(delta)>=1)+2*(y>=7)
   ck(f'{phase}h{h}partition',np.isfinite(y).all() and np.all(low.astype(int)+middle.astype(int)+high.astype(int)==1))
   ck(f'{phase}h{h}increments',np.array_equal(w7-w9,2*middle) and np.array_equal(w9[~middle],w7[~middle]))
   ck(f'{phase}h{h}oldsummary',len(ix)==int(meta[phase,h]['n']) and int(w9.sum())==int(meta[phase,h]['weights_sum']))
   ck(f'{phase}h{h}one row/cutoff',len(np.unique(t[ix]))==len(ix) and np.all(np.diff(ix)>0) and np.all(t[ix]+h*3600<(start if phase=='validation' else end)))
   row=dict(phase=phase,horizon_h=h,rows=len(ix),target_below7=int(low.sum()),target_ge7_lt9=int(middle.sum()),target_ge9=int(high.sum()),target_exactly7=int((y==7).sum()),target_exactly9=int((y==9).sum()),middle_abs_delta_ge1=int((middle&(abs(delta)>=1)).sum()),middle_abs_delta_lt1=int((middle&(abs(delta)<1)).sum()),old_weights_sum=int(w9.sum()),new_weights_sum=int(w7.sum()),expected_increment=int(2*middle.sum()),relative_total_weight_increase=float((w7.sum()-w9.sum())/w9.sum()),middle_old_weight_sum=int(w9[middle].sum()),middle_new_weight_sum=int(w7[middle].sum()),indices_sha256=hashlib.sha256(ix.tobytes()).hexdigest(),response_sha256=hashlib.sha256(delta.tobytes()).hexdigest(),old_weights_sha256=hashlib.sha256(w9.tobytes()).hexdigest(),new_weights_sha256=hashlib.sha256(w7.tobytes()).hexdigest())
   out.append(row);vectors[f'{phase}_h{h}_indices']=ix;vectors[f'{phase}_h{h}_delta']=delta;vectors[f'{phase}_h{h}_weights9']=w9;vectors[f'{phase}_h{h}_weights7']=w7
 for path,digest in inputs.items():ck('unchanged '+path,sha(R/path)==digest)
 with (P/'expected-training-weights.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
 np.savez_compressed(P/'expected-training-vectors.npz',**vectors)
 dump('expected-input-hashes.json',inputs);dump('expected-weight-verification.json',dict(passed=True,checked_at_utc=datetime.now(timezone.utc).isoformat(),checks_count=len(checks),checks=checks,masks=24,candidate_inspected=False,fit_prediction_network=False,limits=['7m is the analytical subset definition, not an official flood or alert threshold.','Rows repeat across horizons and folds; counts must not be summed as independent physical observations.','Changing relative sample weights affects the whole fitted function; per-row increase is not a guaranteed accuracy gain.']))
 print('PASS',len(checks),'checks')
 for r in out:
  if r['horizon_h'] in (1,6,12):print({k:r[k] for k in ('phase','horizon_h','rows','target_below7','target_ge7_lt9','target_ge9','old_weights_sum','new_weights_sum','expected_increment')})
if __name__=='__main__':main()
