"""Independent paired-HQ curve audit. No optimizers, refits or performance scoring."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import ast,csv,hashlib,json,math
import numpy as np
ROOT=Path('/Users/brunozilio/Documents/radar');OUT=ROOT/'outputs/verificacao-curva-pares-hq-20260921'
RUN=ROOT/'outputs/experimento-curva-pares-hq-20260921';PRIOR=ROOT/'outputs/experimento-proxy-carreiro-20260921';BASE=ROOT/'outputs/mucum-atualizacao-15h-2026-09-21'
checks=[];hashes={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):hashes[str(p)]=sha(p);return p
def js(p):return json.loads(read(p).read_text())
def rows(p):return list(csv.DictReader(read(p).open()))
def ep(s):return datetime.fromisoformat(s).timestamp()
def val(s):return float(s) if s else np.nan
def eq(a,b):return (not a and not b) or bool(a and b and float(a)==float(b))
def check(k,v,d=None):checks.append(dict(check=k,passed=bool(v),detail=d))
def key(r):return r['origin'],r['target_time'],int(r.get('nominal_lead_h',r.get('horizon_h')))
def stage(q,p):return p[0]*(q/1000)**p[1]+p[2]
def run():
 if not (RUN/'experiment.json').exists():print('WAITING_EXPERIMENT');return
 OUT.mkdir(parents=True,exist_ok=True);meta=js(RUN/'experiment.json');policy=js(RUN/'protocol.json');prior=js(PRIOR/'experiment.json')
 for name,digest in meta['input_sha256'].items():
  p=Path(name);check('input hash '+name,sha(read(p))==digest)
  if p.suffix=='.py':check('executed source '+p.name,sha(read(RUN/'code'/p.name))==digest)
 check('protocol source match',sha(read(ROOT/'docs/rating-paired-only-protocol.json'))==sha(RUN/'protocol.json'))
 for name in ['dados-roteamento.npz','telemetria-latencia.npz','conferencia-balanco.json']:
  p=BASE/name;check('prior frozen input '+name,sha(read(p))==prior['input_sha256'][str(p)])
 check('prior predictions unchanged',sha(read(PRIOR/'predictions.csv'))==js(PRIOR/'artifact-hashes.json')['predictions.csv'])
 d=dict(np.load(read(BASE/'dados-roteamento.npz')));z=dict(np.load(read(BASE/'telemetria-latencia.npz')));t=d['times'];q=d['q'];h=d['h']
 ix=np.searchsorted(z['times'],t)
 check('fit H/Q equal exact raw grid',np.array_equal(t,z['times'][ix]) and np.array_equal(h,z['raw:86510000:H'][ix],equal_nan=True) and np.allclose(q*1000,z['raw:86510000:Q'][ix],equal_nan=True,rtol=0,atol=1e-9))
 paired=np.isfinite(h)&np.isfinite(q);routing=paired&np.isfinite(d['X']).all(axis=1)
 check('all finite paired Q nonnegative',np.all(q[paired]>=0))
 curves=js(RUN/'curves.json');tr={(r['phase'],r['family']):r for r in rows(RUN/'training.csv')}
 fitpairs=rows(RUN/'curve-fit-pairs.csv');fitmap={(r['phase'],r['family'],float(r['epoch'])):r for r in fitpairs}
 check('curve evaluation no duplicates',len(fitmap)==len(fitpairs))
 cutoffs=[ep('2025-10-01T00:00:00-03:00'),ep('2026-07-01T00:00:00-03:00'),ep('2026-09-21T00:00:00-03:00')]
 trainings=[];evalkeys=set();maxcost=0.;maxstage=0.
 for phase,cut,end in [('validation',cutoffs[0],cutoffs[1]),('test',cutoffs[1],cutoffs[2])]:
  ev=np.flatnonzero(paired&(t>=cut)&(t<end))
  for fam,valid in [('original_membership',routing),('all_paired_hq',paired)]:
   idx=np.flatnonzero(valid&(t<cut));p=np.array(curves[phase+':'+fam]);r=tr[phase,fam]
   check(phase+'/'+fam+': strict membership and cutoff',int(r['training_n'])==len(idx) and int(r['training_high_n'])==int((h[idx]>=7).sum()) and float(r['latest_training_epoch'])==float(t[idx].max()) and float(r['cutoff_exclusive_epoch'])==cut and np.all(t[idx]<cut))
   check(phase+'/'+fam+': max Q and bounds',abs(float(r['training_qmax_m3_s'])-q[idx].max()*1000)<1e-8 and np.all(p>=[.01,.1,-10]) and np.all(p<=[20,1.2,10]) and r['success']=='True')
   residual=p[0]*q[idx]**p[1]+p[2]-h[idx];cost=float(np.sum(np.sqrt(1+residual**2)-1));err=abs(cost-float(r['cost']));maxcost=max(maxcost,err)
   check(phase+'/'+fam+': preserved soft_l1 cost',err<1e-9,{'difference':err,'cost_recomputed':cost})
   trainings.append({'phase':phase,'family':fam,'n':len(idx),'high_n':int((h[idx]>=7).sum()),'latest_training_epoch':float(t[idx].max()),'indices_sha256':hashlib.sha256(idx.astype('<i8').tobytes()).hexdigest()})
   for i in ev:
    k=phase,fam,float(t[i]);evalkeys.add(k);r=fitmap.get(k)
    if r is None:continue
    checkfields=float(r['reported_q_m3_s'])==float(q[i]*1000) and float(r['observed_h_m'])==float(h[i])
    if not checkfields:check('curve eval source row '+str(k),False)
    maxstage=max(maxstage,abs(float(r['stage_m'])-stage(q[i]*1000,p)))
 check('curve evaluation same paired population exactly',evalkeys==set(fitmap))
 check('curve evaluation values reproduce',maxstage<1e-10,{'max_difference_m':maxstage})
 expected={(r['phase'],r['family']):(r['n'],r['high_n']) for r in trainings}
 check('preJuly8880to10890 high128to256',expected['test','original_membership']==(8880,128) and expected['test','all_paired_hq']==(10890,256))
 old=np.array(js(BASE/'conferencia-balanco.json')['rating_parameters']);new=np.array(curves['test:all_paired_hq'])
 difference=float(np.max(abs(np.array(curves['test:original_membership'])-old)))
 check('old control parameters reproduced',difference<1e-7 and abs(difference-meta['reference_parameters_max_difference'])<1e-14,{'max_difference':difference})
 # Review exact optimizer arguments from preserved AST, without running least_squares.
 source=(RUN/'code/hydro_rating_paired_fit.py').read_text();tree=ast.parse(source)
 fitter=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fit_curve')
 calls=[n for n in ast.walk(fitter) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='least_squares']
 call=calls[0];kw={x.arg:ast.literal_eval(x.value) for x in call.keywords}
 check('same initial bounds loss no optimizer search',len(calls)==1 and ast.literal_eval(call.args[1])==[4.5,.64,.4] and kw=={'bounds':([.01,.1,-10],[20,1.2,10]),'loss':'soft_l1'})
 check('fit residual only indexed H/Q',ast.dump(call.args[0],include_attributes=False)==ast.dump(ast.parse('lambda p:p[0]*q[indices]**p[1]+p[2]-h[indices]',mode='eval').body,include_attributes=False))
 replace=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='replace_curve')
 check('candidate pure inputs exclude target', [x.arg for x in replace.args.args]==['base_h','anchor_h','anchor_q','old','new'])
 candidate_calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='replace_curve']
 check('candidate call contains no future target',all(all(isinstance(x,ast.Name) and x.id in {'base','ah','aq','old','new'} for x in c.args) for c in candidate_calls))
 baseline=rows(PRIOR/'predictions.csv');result=rows(RUN/'predictions.csv');decomp=rows(RUN/'error-decomposition.csv');demap={key(r):r for r in decomp}
 check('23538 rows keys order unchanged',len(result)==23538 and len({key(r) for r in result})==23538 and [key(r) for r in baseline]==[key(r) for r in result])
 check('baseline targets anchors status preserved',all(eq(a['actual_m'],b['actual_m']) and eq(a['reference_m'],b['julho_levels_m']) and a['anchor_at']==b['anchor_at'] and a['previous_status']==b['status'] for a,b in zip(result,baseline)))
 maxq=0.;maxcandidate=0.;maxdecomp=0.;roundtrip=0.;bad=[];exclusions=Counter();expecteddec=set();records=[]
 for r in result:
  base=val(r['reference_m']);actual=val(r['actual_m']);ai=int(np.searchsorted(z['times'],ep(r['anchor_at'])));ti=int(np.searchsorted(z['times'],ep(r['target_time'])))
  assert z['times'][ai]==ep(r['anchor_at']) and z['times'][ti]==ep(r['target_time'])
  ah=z['raw:86510000:H'][ai];aq=z['raw:86510000:Q'][ai];tq=z['raw:86510000:Q'][ti];pq=np.nan;candidate=np.nan
  if np.isfinite([base,ah,aq]).all():
   offset=ah-stage(aq,old);domain=base-offset-old[2];assert domain>=-1e-10
   pq=1000*(max(domain,0)/old[0])**(1/old[1]);candidate=stage(pq,new)+ah-stage(aq,new);roundtrip=max(roundtrip,abs(stage(pq,old)+offset-base))
  sq=val(r['preserved_predicted_q_m3_s']);sc=val(r['candidate_m'])
  if np.isfinite(pq)!=np.isfinite(sq) or np.isfinite(candidate)!=np.isfinite(sc):bad.append((key(r),'missing pattern'))
  if np.isfinite(pq):maxq=max(maxq,abs(sq-pq));maxcandidate=max(maxcandidate,abs(sc-candidate))
  status='missing_exact_anchor' if r['previous_status']=='missing_exact_anchor' else 'missing_or_invalid_forecast_input' if not np.isfinite(candidate) else 'missing_exact_target' if not np.isfinite(actual) else 'paired'
  if r['candidate_status']!=status:bad.append((key(r),'status'))
  if not np.isfinite(actual):exclusions['missing_target_H']+=1
  elif not np.isfinite([base,aq,ah,pq]).all():exclusions['missing_baseline_or_anchor']+=1
  elif not np.isfinite(tq):exclusions['missing_reported_target_Q']+=1
  else:
   expecteddec.add(key(r));dr=demap.get(key(r));flow=stage(pq,old)-stage(tq,old);other=ah-stage(aq,old)-(actual-stage(tq,old));total=base-actual
   values={'actual_m':actual,'total_error_m':total,'flow_conversion_error_m':flow,'anchor_curve_error_m':other,'reported_target_q_m3_s':tq,'predicted_q_m3_s':pq}
   if dr is not None:
    maxdecomp=max(maxdecomp,*[abs(float(dr[k])-float(v)) for k,v in values.items()],abs(flow+other-total))
   exclusions['decomposed']+=1
  records.append({'origin':r['origin'],'target_time':r['target_time'],'horizon':r['nominal_lead_h'],'predicted_q_independent_m3_s':float(pq) if np.isfinite(pq) else None,'candidate_independent_m':float(candidate) if np.isfinite(candidate) else None,'candidate_status_expected':status})
 check('candidate preserves inferred flow and only changes curve/offset',not bad and maxq<1e-8 and maxcandidate<1e-10,{'max_q_difference_m3_s':maxq,'max_level_difference_m':maxcandidate,'row_errors':bad[:10]})
 check('old-curve roundtrip',roundtrip<1e-9,{'max_difference_m':roundtrip})
 check('decomposition exact eligibility and unique rows',len(decomp)==len(demap)==len(expecteddec)==meta['decomposed_rows'] and set(demap)==expecteddec)
 check('decomposition components and identity',maxdecomp<1e-8,{'max_difference_across_stored_components_m_or_m3s':maxdecomp})
 check('no promotion',not meta['promoted'] and not meta['live_issuance'] and not meta['goal_achieved'])
 check('all audited inputs unchanged',all(sha(Path(k))==v for k,v in hashes.items()))
 with (OUT/'independent-predictions.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
 failures=[r['check'] for r in checks if not r['passed']]
 report={'passed':not failures,'failures':failures,'checks':checks,'input_sha256':hashes,'training_membership':trainings,'rows':len(result),'decomposition_exclusion_priority':['missing_target_H','missing_baseline_or_anchor','missing_reported_target_Q','decomposed'],'decomposition_population':dict(exclusions),'same_q_max_difference_m3_s':maxq,'candidate_max_difference_m':maxcandidate,'reference_parameters_max_difference':difference,'decomposition_max_difference':maxdecomp,'optimizers_run':0,'performance_metrics_computed':False,'causality_certified':False,'limitations':['Reported ANA Q is not certified independent physical gauging.','Components are algebraic and may compensate; they are not independent physical causes.','Decomposition requires reported target Q, reducing population and potentially excluding flood times.','Same reconstructed totalQ is preserved; no full HGE rerun performed.','All inspected dates remain historical development, not independent evaluation.'],'created_at_utc':datetime.now(timezone.utc).isoformat()}
 (OUT/'verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
 print(json.dumps({k:report[k] for k in ['passed','failures','training_membership','rows','decomposition_population','same_q_max_difference_m3_s','candidate_max_difference_m','reference_parameters_max_difference','decomposition_max_difference']},indent=2))
 if failures:raise SystemExit(1)
if __name__=='__main__':run()

