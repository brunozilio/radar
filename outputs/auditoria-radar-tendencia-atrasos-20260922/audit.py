"""Independent frozen stratification audit. No fit, inference or network."""
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
import csv, json, hashlib
import numpy as np
from verify_contract import reconstruct

P=Path(__file__).resolve().parent; R=P.parents[1]
D=R/'outputs/diagnostico-radar-tendencia-atrasos-20260922'
E=R/'outputs/experimento-radar-idade-ancora-20260922'
B=R/'outputs/experimento-radar-mistura-atrasos-20260922'
F=('profile_A_control','profile_B_control','mixed_profile_candidate','age_mixed_candidate')
inputs={}; checks=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def track(p): inputs[str(p.relative_to(R))]=sha(p); return p
def read(p): return list(csv.DictReader(track(p).open()))
def js(p): return json.loads(track(p).read_text())
def ck(name,b): checks.append(dict(check=name,passed=bool(b))); assert b,name
def num(v): return float(v) if v not in ('',None) else np.nan
def ep(s): return datetime.fromisoformat(s).timestamp()
def dump(name,v): (P/name).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def save(name,rows):
 with (P/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def compare(name,actual,expected):
 ok=set(actual)==set(expected)
 for k,v in expected.items():
  if isinstance(v,str): ok &= actual.get(k)==v
  elif v is None: ok &= actual.get(k)==''
  else: ok &= np.isclose(num(actual.get(k)),v,rtol=0,atol=1e-10 if k.startswith('sum_') else 1e-12)
 ck(name,ok)
def direction(v,bound):
 # Explicit predicates preserve inclusive thresholds and unknowns.
 a=np.full(len(v),'unknown',dtype='<U8'); finite=np.isfinite(v)
 a[finite & (v > -bound) & (v < bound)]='stable'
 a[finite & (v >= bound)]='rising'; a[finite & (v <= -bound)]='falling'
 return a

def main():
 for folder in (D,E,B):
  for item in js(folder/'artifact-hashes.json'):
   ck('hash '+folder.name+'/'+item['file'],sha(track(folder/item['file']))==item['sha256'])
 diagnostic=js(D/'diagnostic.json'); plan=js(D/'diagnostic-plan.json')
 for meta in (diagnostic,plan):
  for path,digest in meta['input_sha256'].items(): ck('sourcehash '+path,sha(track(R/path))==digest)
 trend,contract,sourcehashes=reconstruct(); inputs.update(sourcehashes)
 z=dict(np.load(track(B/'prepared-inputs.npz'))); masks=dict(np.load(track(B/'training-masks.npz')))
 t=z['times']; truth=z['truth']; n=len(t)
 ck('assignment fixed',np.array_equal(z['assignment'],np.random.Generator(np.random.PCG64(57)).integers(0,2,size=n,dtype=np.int8)))
 base_mix=z['base_A'].copy(); base_mix[z['assignment']==1]=z['base_B'][z['assignment']==1]
 bases={F[0]:z['base_A'],F[1]:z['base_B'],F[2]:base_mix,F[3]:base_mix}
 train_saved={(r['phase'],int(r['horizon_h']),r['family']):r for r in read(D/'training-response-support.csv')}
 training=[]; supports={}; start,end,stop=map(ep,('2025-10-01T00:00:00-03:00','2026-07-01T00:00:00-03:00','2026-09-21T00:00:00-03:00'))
 for h in range(1,13):
  target=np.r_[truth[h:],np.full(h,np.nan)]
  available=np.isfinite(z['base_A']) & np.isfinite(z['base_B']) & np.isfinite(target)
  available &= np.isfinite(z['features_A'][:,:24]).all(axis=1) & np.isfinite(z['features_B'][:,:24]).all(axis=1)
  for phase in ('validation','test'):
   mask=available & ((t+h*3600<start) if phase=='validation' else ((t+h*3600<start)|((t>=start)&(t+h*3600<end))))
   ck(f'mask {phase} {h}',np.array_equal(mask,masks[f'{phase}_h{h}']))
   for family in F:
    delta=target[mask]-bases[family][mask]; ck(f'finite training {phase} {h} {family}',np.isfinite(delta).all())
    lo=float(min(delta)); hi=float(max(delta)); supports[phase,h,family]=(lo,hi)
    row=dict(phase=phase,horizon_h=h,family=family,rows=int(mask.sum()),response_min_m=lo,response_max_m=hi)
    compare('training '+str((phase,h,family)),train_saved[phase,h,family],row); training.append(row)
 predictions=read(E/'predictions.csv'); groups=defaultdict(list)
 for r in predictions: groups[r['phase'],r['profile'],int(r['nominal_lead_h'])].append(r)
 ck('204168 rows48groups',len(predictions)==204168 and len(groups)==48)
 sk=lambda r:(r['phase'],r['profile'],int(r['horizon_h']),r['family'],r['subset'],r['partition'],r['category'])
 tk=lambda r:(r['phase'],r['profile'],int(r['horizon_h']),r['subset'],r['partition'],r['category'])
 saved={sk(r):r for r in read(D/'strata.csv')}; trans_saved={tk(r):r for r in read(D/'age-hit-transitions.csv')}
 parent={(r['phase'],r['profile'],int(r['horizon_h']),r['family'],r['subset']):r for r in read(E/'evaluation.csv') if r['population']=='full_schedule'}
 metrics=[]; transitions=[]; reconciliations=[]; lookup={float(v):i for i,v in enumerate(t)}
 for (phase,profile,h),rows in sorted(groups.items()):
  ix=np.array([lookup[ep(r['origin'])] for r in rows]); actual=np.array([num(r['actual_m']) for r in rows]); base=np.array([num(r['base_m']) for r in rows])
  ck(f'{phase}{profile}{h}base/truth',np.array_equal(actual,truth[ix+h],equal_nan=True) and np.array_equal(base,z['base_'+profile][ix],equal_nan=True))
  future=actual-base; labels={'known_trend':direction(trend[profile+'_column2'][ix],.10),'future_response':direction(future,.50)}
  preds={f:np.array([num(r[f+'_m']) for r in rows]) for f in F}
  for subset in ('all','level_ge_7m'):
   included=np.full(len(rows),True) if subset=='all' else (~np.isfinite(actual)|(actual>=7))
   observed=included & np.isfinite(actual)
   for family in F:
    lo,hi=supports[phase,h,family]; label=np.full(len(rows),'unknown',dtype='<U8'); finite=np.isfinite(future)
    label[finite & (future<lo)]='below'; label[finite & (future>hi)]='above'; label[finite & (future>=lo)&(future<=hi)]='within'
    for partition,lab in dict(labels,training_response_support=label).items():
     cats=('below','within','above','unknown') if partition=='training_response_support' else ('rising','falling','stable','unknown'); block=[]
     for cat in cats:
      selected=included & (lab==cat); obs=selected & observed; paired=obs & np.isfinite(preds[family]); e=preds[family][paired]-actual[paired]; ae=np.abs(e)
      count=int(obs.sum()); hits=int(np.count_nonzero(ae<=.5))
      row=dict(phase=phase,profile=profile,horizon_h=h,family=family,subset=subset,partition=partition,category=cat,classified_rows=int(selected.sum()),unknown_truth=int(np.count_nonzero(selected & ~np.isfinite(actual))),observed_targets=count,pairs=len(e),failures=count-len(e),hits=hits,observed_hit_fraction=hits/count if count else None,sum_abs_error_m=float(sum(ae)),sum_error_m=float(sum(e)),mae_m=float(ae.mean()) if len(e) else None,bias_m=float(e.mean()) if len(e) else None,max_abs_m=float(max(ae)) if len(e) else None,under_by_more_than_0_5m=int(np.count_nonzero(e<-.5)),over_by_more_than_0_5m=int(np.count_nonzero(e>.5)))
      compare('metric '+str(sk(row)),saved[sk(row)],row); metrics.append(row); block.append(row)
     ref=parent[phase,profile,h,family,subset]
     for field in ('observed_targets','pairs','failures','hits'): ck('reconcile '+str((phase,profile,h,family,subset,partition,field)),sum(r[field] for r in block)==int(ref[field]))
     ck('unknown/selection '+str((phase,profile,h,family,subset,partition)),sum(r['unknown_truth'] for r in block)==int(ref['missing_truth']) and sum(r['classified_rows'] for r in block)==int(included.sum()))
     pairs=int(ref['pairs'])
     if pairs:
      ck('weighted error '+str((phase,profile,h,family,subset,partition)),abs(sum(r['sum_abs_error_m'] for r in block)/pairs-float(ref['mae_m']))<1e-12 and abs(sum(r['sum_error_m'] for r in block)/pairs-float(ref['bias_m']))<1e-12)
     reconciliations.append(dict(phase=phase,profile=profile,horizon_h=h,family=family,subset=subset,partition=partition,scheduled_parent=int(ref['scheduled_rows']),classified_rows=int(included.sum()),observed_targets=int(observed.sum()),unknown_truth=int((included & ~np.isfinite(actual)).sum())))
   p0=preds[F[2]]; p1=preds[F[3]]; pair=observed & np.isfinite(p0)&np.isfinite(p1); hit0=np.abs(p0-actual)<=.5; hit1=np.abs(p1-actual)<=.5
   for partition,lab in labels.items():
    for cat in ('rising','falling','stable','unknown'):
     m=pair & (lab==cat); counts=np.bincount((hit0[m].astype(int)*2+hit1[m].astype(int)),minlength=4)
     row=dict(phase=phase,profile=profile,horizon_h=h,subset=subset,partition=partition,category=cat,pairs=int(m.sum()),gained=int(counts[1]),lost=int(counts[2]),both_hit=int(counts[3]),both_miss=int(counts[0]),net_hits=int(counts[1]-counts[2]))
     compare('transition '+str(tk(row)),trans_saved[tk(row)],row); transitions.append(row)
 ck('4608metric768transition96support',len(metrics)==len(saved)==4608 and len(transitions)==len(trans_saved)==768 and len(training)==len(train_saved)==96)
 for path,digest in inputs.items(): ck('unchanged '+path,sha(R/path)==digest)
 save('independent-strata.csv',metrics); save('independent-transitions.csv',transitions); save('independent-training-support.csv',training); save('parent-reconciliation.csv',reconciliations)
 dump('input-hashes.json',inputs); dump('contract-verification.json',dict(passed=True,columns=contract,input_sha256=sourcehashes,diagnostic_outputs_not_yet_audited=False))
 dump('verification.json',dict(passed=True,checked_at_utc=datetime.now(timezone.utc).isoformat(),checks_count=len(checks),checks=checks,metrics=4608,transitions=768,training_support=96,rows=204168,fit_or_inference_or_network=False,limits=['Future response and training support require future observed truth: diagnostic labels only.','Origin trend uses nominal time between delayed queries, not actual measurement intervals.','High subset retains unknown truth separately, not as known flood observations.','Profiles are paired alternative views, not independent events.','All evaluation periods were already inspected development; no selection or promotion.']))
 print('PASS',len(checks),'checks')

if __name__=='__main__': main()
