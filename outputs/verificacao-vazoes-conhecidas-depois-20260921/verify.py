"""PRELIMINARY ASOF GRID ONLY. Superseded by verify_exact.py; no exact-observation claim."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import ast,csv,json,hashlib,math
import numpy as np
from threadpoolctl import threadpool_limits
ROOT=Path('/Users/brunozilio/Documents/radar');OUT=ROOT/'outputs/verificacao-vazoes-conhecidas-depois-20260921'
RUN=ROOT/'outputs/diagnostico-vazoes-conhecidas-depois-20260921';PRIOR=ROOT/'outputs/experimento-proxy-carreiro-20260921';FLOW=ROOT/'outputs/experimento-niveis-reservatorios-20260921';BASE=ROOT/'outputs/mucum-atualizacao-15h-2026-09-21'
checks=[];hashes={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):hashes[str(p)]=sha(p);return p
def js(p):return json.loads(read(p).read_text())
def rows(p):return list(csv.DictReader(read(p).open()))
def ep(s):return datetime.fromisoformat(s).timestamp()
def val(s):return float(s) if s else np.nan
def equal(a,b):return (not a and not b) or bool(a and b and float(a)==float(b))
def check(k,v,d=None):checks.append(dict(check=k,passed=bool(v),detail=d))
def key(r):return r['origin'],r['target_time'],int(r['nominal_lead_h'])
def shift(v,k):
 a=np.full(v.shape,np.nan);a[k:]=v[:-k];return a
def predict(m,x):
 filled=np.column_stack([np.where(np.isfinite(x),x,m['median']),~np.isfinite(x)])
 return (filled-m['mean'])/m['scale']@m['beta']+m['intercept']
def run():
 if not (RUN/'diagnostic.json').exists():print('WAITING_DIAGNOSTIC');return
 OUT.mkdir(parents=True,exist_ok=True)
 meta=js(RUN/'diagnostic.json');policy=js(RUN/'protocol.json')
 for name,digest in meta['input_sha256'].items():
  p=Path(name);check('input hash '+name,sha(read(p))==digest)
  if p.suffix=='.py':check('executed code '+p.name,sha(read(RUN/'code'/p.name))==digest)
 check('nonforecast explicit exclusions',meta['uses_information_unavailable_at_issuance'] and not meta['valid_operational_forecast'] and not meta['eligible_for_goal'] and not meta['promoted'] and not meta['goal_achieved'] and meta['models_fitted']==0)
 check('protocol matches source',sha(RUN/'protocol.json')==sha(read(ROOT/'docs/future-flow-diagnostic-protocol.json')))
 prior=js(PRIOR/'experiment.json')
 for name in ['dados-roteamento.npz','telemetria-latencia.npz','conferencia-balanco.json','roteamento-vazao-pesos.csv']:
  p=BASE/name;check('baseline frozen data '+name,sha(read(p))==prior['input_sha256'][str(p)])
 manifest=js(PRIOR/'artifact-hashes.json')
 for name in ['predictions.csv','modeled-carreiro-inputs.npz']:check('baseline original artifact '+name,sha(read(PRIOR/name))==manifest[name])
 d=dict(np.load(read(BASE/'dados-roteamento.npz')));z=dict(np.load(read(BASE/'telemetria-latencia.npz')));extra=dict(np.load(read(FLOW/'additional-features.npz')));proxy=dict(np.load(read(PRIOR/'modeled-carreiro-inputs.npz')));saved=dict(np.load(read(RUN/'reference-estimated-flows.npz')));t=d['times']
 check('all grids identical',all(np.array_equal(t,a['times']) for a in [extra,proxy,saved]))
 ix=np.searchsorted(z['times'],t);check('exact telemetry origin grid',np.array_equal(z['times'][ix],t))
 columns=[]
 for source in ['julho:Q','julho:I','monte:Q','monte:I','castro:Q','castro:I','86500000:Q']:
  v=z[source][ix]/1000;columns.extend([v,v-shift(v,1),(v-shift(v,3))/3,(v-shift(v,6))/6])
 for g in ['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']:
  for w in [3,6,12,24,48]:columns.append(z[g+f':P{w}'][ix]/100)
 F=np.column_stack(columns);F77=np.column_stack([F,extra['levels_and_slopes']]);models=js(FLOW/'frozen-models.json');flows={}
 for s,k,family,x in [('julho','julho:Q','level_and_slopes',F77),('carreiro','86500000:Q','reference',F)]:
  known=z[k][ix]/1000
  v=np.column_stack([np.maximum(known+predict({a:np.array(b) if isinstance(b,list) else b for a,b in models[f'{s}:{lead}:test:{family}'].items()},x),0)*1000 for lead in range(12)])
  if s=='carreiro':v=np.where(np.isfinite(v),v,proxy['estimated_q_m3_s'])
  flows[s]=v;error=float(np.nanmax(abs(v-saved[s])))
  check(s+': independent frozen inference',np.array_equal(np.isfinite(v),np.isfinite(saved[s])) and error<1e-7,{'max_difference_m3_s':error})
 old=rows(PRIOR/'predictions.csv');new=rows(RUN/'reconstructions-not-forecasts.csv')
 check('23538 same keys/order/unique',len(new)==23538 and len({key(r) for r in new})==23538 and [key(r) for r in old]==[key(r) for r in new])
 check('baseline/targets/status/anchor invariant',all(equal(a['actual_m'],b['actual_m']) and equal(a['reference_m'],b['julho_levels_m']) and a['reference_status']==b['status'] and a['anchor_at']==b['anchor_at'] for a,b in zip(new,old)))
 kernel=rows(BASE/'roteamento-vazao-pesos.csv');kernels={s:[(int(r['lag_h']),float(r['weight'])) for r in kernel if r['source']==label] for s,label in [('julho','14 de Julho'),('carreiro','Passo Carreiro')]}
 for s,kk in kernels.items():check(s+': causal historical anchor kernel',all(l>=1 and math.isfinite(w) and w>=0 for l,w in kk) and abs(sum(w for l,w in kk)-1)<1e-6)
 a,b,c=js(BASE/'conferencia-balanco.json')['rating_parameters'];check('invertible rating',a>0 and b>0 and all(math.isfinite(v) for v in [a,b,c]))
 output=[];delta_errors=[];stage_errors=[];status_errors=[];missing_errors=[];counts=Counter();missing_cases=Counter();nofuture=0
 for r in new:
  at=ep(r['origin']);i=int(np.searchsorted(t,at));assert t[i]==at;h=int(r['nominal_lead_h']);ds={};needs={};missing={}
  for s in ['julho','carreiro']:
   # Enumerate all needed terms first; exact zero skipped, tiny positive retained.
   terms=[(h-l,w) for l,w in kernels[s] if w!=0 and h-l>=0]
   needs[s]=len(terms);bad=[k for k,w in terms if not np.isfinite(d[s][i+k]) or not np.isfinite(flows[s][i,k])]
   missing[s]=bad
   ds[s]=np.nan if bad else math.fsum(w*(float(d[s][i+k])*1000-float(flows[s][i,k])) for k,w in terms)
   got=val(r['delta_'+s+'_m3_s'])
   if np.isfinite(ds[s])!=np.isfinite(got):missing_errors.append((r['origin'],h,s))
   elif np.isfinite(got):delta_errors.append(abs(ds[s]-got))
  ai=int(np.searchsorted(z['times'],ep(r['anchor_at'])));assert z['times'][ai]==ep(r['anchor_at'])
  base=val(r['reference_m']);ah=z['raw:86510000:H'][ai];aq=z['raw:86510000:Q'][ai]
  row={'origin':r['origin'],'horizon':h}
  for s in ds:row.update({s+'_delta_direct_m3_s':float(ds[s]) if np.isfinite(ds[s]) else None,s+'_required_terms':needs[s],s+'_missing_relative_leads':','.join(map(str,missing[s]))})
  for family,sources in [('observed_julho',['julho']),('observed_carreiro',['carreiro']),('observed_both',['julho','carreiro'])]:
   dq=sum(ds[s] for s in sources);want=np.nan
   if not np.isfinite(base):status='baseline_unavailable'
   elif not np.isfinite(dq):status='missing_required_upstream_observation';missing_cases[family]+=1
   elif all(needs[s]==0 for s in sources):status='no_future_input_in_kernel';want=base;nofuture+=1
   else:
    offset=ah-(a*(aq/1000)**b+c);domain=base-offset-c
    assert domain>=-1e-10
    qbase=1000*(max(domain,0)/a)**(1/b);qnew=qbase+dq
    if not all(math.isfinite(v) for v in [ah,aq,qnew]) or qnew<0:status='invalid_reconstructed_flow'
    else:want=a*(qnew/1000)**b+c+offset;status='reconstructed_with_unavailable_information'
   counts[family+':'+status]+=1;got=val(r[family+'_m'])
   if r[family+'_status']!=status:status_errors.append((r['origin'],h,family,status,r[family+'_status']))
   if np.isfinite(want)!=np.isfinite(got):missing_errors.append((r['origin'],h,family))
   elif np.isfinite(got):stage_errors.append(abs(got-want))
   if status=='no_future_input_in_kernel':check('exact no-future value '+r['origin']+'/'+str(h)+'/'+family,r[family+'_m']==r['reference_m'])
   row[family+'_expected_status']=status
  output.append(row)
 check('all direct source deltas match',max(delta_errors,default=0)<=1e-8 and not missing_errors,{'max_difference_m3_s':max(delta_errors,default=0),'missing_pattern_errors':len(missing_errors)})
 check('all independent transformed values match',max(stage_errors,default=0)<=1e-10 and not missing_errors,{'max_difference_m':max(stage_errors,default=0)})
 check('all scenario statuses match',not status_errors,{'errors':status_errors[:10]})
 # Edge cases in exact executed pure delta function; no pipeline invocation.
 tree=ast.parse((RUN/'code/hydro_future_flow_diagnostic.py').read_text());fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='observed_delta');env={'np':np};exec(compile(ast.Module(body=[fun],type_ignores=[]),'observed-delta-pure','exec'),env);fn=env['observed_delta']
 nans=np.full(20,np.nan);est=np.ones(12)
 check('past terms require no future observation',fn(est,nans,2,1,[1.],[4])==(0.,0))
 check('zero weight needs no observation',fn(est,nans,2,1,[0.,1.],[1,4])==(0.,0))
 check('tiny positive weight still requires observation',math.isnan(fn(est,nans,2,1,[1e-20,1.],[1,4])[0]))
 check('missing observed value never proxy-filled',math.isnan(fn(est,nans,2,1,[1.],[1])[0]))
 truth=np.arange(20,dtype=float)
 check('lead zero uses origin observation',fn(est,truth,2,1,[1.],[1])==(1.,1))
 check('past/future changes outside required term irrelevant',fn(est,truth,2,1,[1.],[1])==fn(est,np.array([np.nan,np.nan,2.]+[np.nan]*17),2,1,[1.],[1]))
 with (OUT/'direct-deltas-and-status.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(output[0]));w.writeheader();w.writerows(output)
 check('inputs unchanged during audit',all(sha(Path(p))==v for p,v in hashes.items()))
 failed=[x['check'] for x in checks if not x['passed']]
 result={'passed':not failed,'checks':checks,'failures':failed,'input_sha256':hashes,'rows':len(new),'max_delta_difference_m3_s':max(delta_errors,default=0),'max_stage_difference_m':max(stage_errors,default=0),'expected_status_counts':dict(counts),'missing_upstream_observation_with_baseline':dict(missing_cases),'no_future_input_values_exact':nofuture,'fits_performed':0,'performance_metrics_computed':False,'nonforecast':True,'eligible_for_goal':False,'upper_bound_claim':False,'limitation':'All source deltas and statuses verified. Stage is independently transformed from preserved baseline; this is not a full HGE rerun. Uses observations unavailable at issuance and cannot count as forecast evidence.','created_at_utc':datetime.now(timezone.utc).isoformat()}
 (OUT/'preliminary-arithmetic-verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
 print(json.dumps({k:result[k] for k in ['passed','failures','rows','max_delta_difference_m3_s','max_stage_difference_m','expected_status_counts']},indent=2))
 if failed:raise SystemExit(1)
if __name__=='__main__':
 with threadpool_limits(limits=2):run()

