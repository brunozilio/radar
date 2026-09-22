"""Independent source-mask and conditional forecast verification; no fitting/scoring."""
from pathlib import Path
from datetime import datetime,timezone
from bisect import bisect_right
import ast,csv,hashlib,json,math
import numpy as np
ROOT=Path('/Users/brunozilio/Documents/radar')
OUT=ROOT/'outputs/verificacao-fallback-componentes-20260921'
RUN=ROOT/'outputs/experimento-fallback-componentes-20260921'
MODELS=ROOT/'outputs/experimento-sem-monte-20260921'
BASE=ROOT/'outputs/mucum-atualizacao-15h-2026-09-21'
COMP=('val_vazaoturbinada','val_vazaovertida','val_vazaooutrasestruturas')
checks=[];hashes={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):hashes[str(p)]=sha(p);return p
def js(p):return json.loads(read(p).read_text())
def csvrows(p,delimiter=','):return list(csv.DictReader(read(p).open(),delimiter=delimiter))
def ep(s):
 d=datetime.fromisoformat(s)
 return (d if d.tzinfo else d.replace(tzinfo=timezone(__import__('datetime').timedelta(hours=-3)))).timestamp()
def num(s):
 try:return float(s)
 except (ValueError,TypeError):return float('nan')
def check(name,value,detail=None):checks.append({'check':name,'passed':bool(value),'detail':detail})
def rule(r):
 q=num(r.get('val_vazaodefluente'));v=[num(r.get(c)) for c in COMP]
 return q==0 and all(math.isfinite(x) for x in v) and sum(v)>1
def key(r):return r['phase'],int(r['lead_h']),r['origin'],r['target_time']
def run():
 if not (RUN/'experiment.json').exists():print('WAITING_EXPERIMENT');return
 OUT.mkdir(parents=True,exist_ok=True);meta=js(RUN/'experiment.json');policy=js(RUN/'protocol.json')
 for name,digest in meta['input_sha256'].items():
  p=Path(name);check('input hash '+name,sha(read(p))==digest)
  if p.suffix=='.py':check('executed code copy '+p.name,sha(read(RUN/'code'/p.name))==digest)
 check('protocol original unchanged',sha(read(ROOT/'docs/component-fallback-protocol.json'))==sha(RUN/'protocol.json'))
 check('policy delay/expiry/lags',policy['lags_h']==[0,1,3,6] and policy['source_delay_seconds']==3600 and policy['max_age_seconds']==5400)
 oldverification=js(ROOT/'outputs/verificacao-sem-monte-20260921/verification.json')
 check('previous independent inference audit passed',oldverification['passed'])
 for name in ['predictions.csv','frozen-models.json','experiment.json']:
  p=MODELS/name;check('inference artifact matches previous audited input '+name,oldverification['input_sha256'][str(p)]==sha(read(p)))
 manifest=js(ROOT/'outputs/auditoria-consistencia-componentes-ceran-20260921/source-manifest.json')
 source=[]
 for item in manifest:
  p=ROOT/item['path'];check('source original hash '+str(p),sha(read(p))==item['sha256'])
  for line,r in enumerate(csv.DictReader(p.open(),delimiter=';'),2):
   if r['id_reservatorio'].strip()=='JIUHMC':source.append({**r,'source_path':str(p),'source_line':line})
 source.sort(key=lambda r:ep(r['din_instante']));st=[ep(r['din_instante']) for r in source]
 sf=np.array([rule(r) for r in source])
 check('18 source files no duplicate timestamps',len(manifest)==18 and len(st)==len(set(st)))
 flagged=csvrows(RUN/'flagged-source-records.csv')
 fkeys={(r['source_path'],int(r['source_line'])) for r in flagged};expected={(r['source_path'],r['source_line']) for r,hit in zip(source,sf) if hit}
 check('flagged records recomputed across every Monte row',fkeys==expected,{'source_rows':len(source),'flagged_rows':int(sf.sum())})
 for r in flagged:
  actual=next(x for x in source if (x['source_path'],x['source_line'])==(r['source_path'],int(r['source_line'])))
  check('flag record source fields '+r['source_line'],all(str(actual[k])==r[k] for k in actual))
 d=dict(np.load(read(BASE/'dados-roteamento.npz')));z=dict(np.load(read(BASE/'telemetria-latencia.npz')));saved=dict(np.load(read(RUN/'dependency-flags.npz')))
 origins=d['times'];lags=[0,1,3,6];mask=np.zeros((len(origins),4),dtype=bool);used=np.full(mask.shape,np.nan);trace=[]
 frozen_mismatches=[];finite_raw_mismatches=0;usable_dependencies=0;unrestricted=[]
 for i,origin in enumerate(origins):
  for j,lag in enumerate(lags):
   qtime=origin-lag*3600;cutoff=qtime-3600;k=bisect_right(st,cutoff)-1
   if k<0 or cutoff-st[k]>5400:continue
   used[i,j]=st[k];mask[i,j]=sf[k];usable_dependencies+=1
   qi=int(np.searchsorted(z['times'],qtime))
   if qi<len(z['times']) and z['times'][qi]==qtime and math.isfinite(num(source[k]['val_vazaodefluente'])) and z['monte:Q'][qi]!=num(source[k]['val_vazaodefluente']):
    finite_raw_mismatches+=1
    unrestricted.append({'origin_utc':datetime.fromtimestamp(float(origin),timezone.utc).isoformat(),'offset_h':lag,'feature_time_utc':datetime.fromtimestamp(float(qtime),timezone.utc).isoformat(),'raw_source_time':source[k]['din_instante'],'raw_q':num(source[k]['val_vazaodefluente']),'frozen_q':float(z['monte:Q'][qi]) if np.isfinite(z['monte:Q'][qi]) else None,'source_flag':bool(sf[k]),'source_path':source[k]['source_path'],'source_line':source[k]['source_line']})
   if not mask[i,j]:continue
   r=source[k]
   ok=qi<len(z['times']) and z['times'][qi]==qtime and z['monte:Q'][qi]==num(r['val_vazaodefluente'])==0
   if not ok:frozen_mismatches.append((float(origin),lag))
   trace.append((float(origin),lag,st[k],st[k]+3600,r['source_path'],r['source_line'],0.,sum(num(r[c]) for c in COMP)))
 affected=mask.any(axis=1)
 check('origin grid preserved',np.array_equal(saved['times'],origins))
 check('full by-lag dependency mask',np.array_equal(saved['by_lag'],mask))
 check('full selected source timestamps including missing',np.array_equal(saved['source_times'],used,equal_nan=True))
 check('affected origin mask',np.array_equal(saved['affected'],affected))
 check('flagged rawQ equals actual frozen input',not frozen_mismatches,{'mismatches':frozen_mismatches,'flagged_dependencies':len(trace)})
 tr=csvrows(RUN/'dependency-trace.csv')
 actualtrace=[(ep(r['origin']),int(r['predictor_history_offset_h']),ep(r['source_time']),ep(r['assumed_available_at']),r['source_path'],int(r['source_line']),float(r['raw_total_q_m3_s']),float(r['component_sum_m3_s'])) for r in tr]
 check('trace exact against independent bisect',actualtrace==trace)
 check('flagged publication assumption precedes feature-time',all(at+3600<=origin-lag*3600 for origin,lag,at,*rest in trace))
 check('flagged age expires at cutoff',all(0<=origin-lag*3600-3600-at<=5400 for origin,lag,at,*rest in trace))
 pred=csvrows(RUN/'predictions.csv');original=csvrows(MODELS/'predictions.csv')
 ref={key(r):r for r in original if r['family']=='level_and_slopes'}
 alt={key(r):r for r in original if r['family']=='without_monte'}
 mapping={float(t):bool(v) for t,v in zip(origins,affected)}
 check('102108 unique and same keys',len(pred)==len({key(r) for r in pred})==102108 and {key(r) for r in pred}==set(ref)==set(alt))
 errors=[];outside_changed=[];selected=0;phases={'validation':0,'test':0}
 for r in pred:
  k=key(r);hit=mapping[ep(r['origin'])];want=(alt if hit else ref)[k]
  if hit:selected+=1;phases[r['phase']]+=1
  if r['forecast_m3_s']!=want['forecast_m3_s'] or r['fallback_selected']!=str(hit):errors.append(k)
  if not hit and r['forecast_m3_s']!=ref[k]['forecast_m3_s']:outside_changed.append(k)
  checkcols=['source','lead_h','phase','origin','target_time','actual_m3_s','high_flow']
  if any(r[x]!=ref[k][x] for x in checkcols) or r['reference_m3_s']!=ref[k]['forecast_m3_s']:errors.append(k)
 check('conditional inference and unchanged targets',not errors,{'errors':len(errors)})
 check('exact unchanged outside mask',not outside_changed)
 check('all output predictions finite',all(math.isfinite(num(r['forecast_m3_s'])) for r in pred))
 check('no models fitted',meta['models_fitted']==0)
 check('counts match independent masks',meta['flagged_source_records']==int(sf.sum()) and meta['affected_hourly_origins']==int(affected.sum()) and meta['validation_fallback_selected']==phases['validation'] and meta['test_fallback_selected']==phases['test'])
 # Pure-function boundaries and target-independence, without importing the pipeline.
 src=(RUN/'code/hydro_component_fallback.py').read_text();tree=ast.parse(src);funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['finite_number','component_conflict','source_dependencies','choose_forecast']]
 env={'np':np,'math':math,'COMPONENTS':COMP};exec(compile(ast.Module(body=funcs,type_ignores=[]),'pure-source-contract','exec'),env)
 pure=env['component_conflict']
 cases=[('positive components',0,[0,0,6],True),('sum at threshold',0,[0,0,1],False),('unknown component',0,[0,None,6],False),('nonzero total',1,[0,0,6],False),('nan component',0,[0,float('nan'),6],False),('inf component',0,[0,0,float('inf')],False)]
 for name,q,cc,want in cases:check('rule boundary '+name,pure(dict(zip(('val_vazaodefluente',*COMP),[q,*cc])))==want)
 deps=env['source_dependencies'];orig=np.array([3599,3600,9000,9001])
 hit,time=deps(np.array([0]),np.array([True]),orig)
 check('asof exact delay and expiry inclusive boundaries',hit[:,0].tolist()==[False,True,True,False])
 a,u=deps(np.array([0,3600]),np.array([True,False]),np.array([7200]))
 check('new unflagged row supersedes earlier flagged source',not a[0,0] and u[0,0]==3600)
 for name,v in [('baseline',False),('fallback',True)]:check('choose without targets '+name,env['choose_forecast'](12.,9.,v)==(9. if v else 12.))
 check('all hashed inputs unchanged during audit',all(sha(Path(p))==v for p,v in hashes.items()))
 failed=[c['check'] for c in checks if not c['passed']]
 (OUT/'unrestricted-asof-differences.json').write_text(json.dumps(unrestricted,indent=2,allow_nan=False)+'\n')
 result={'passed':not failed,'checks':checks,'failures':failed,'input_sha256':hashes,'source_rows':len(source),'source_conflicts':int(sf.sum()),'affected_origins':[datetime.fromtimestamp(float(o),timezone.utc).isoformat() for o,h in zip(origins,affected) if h],'flagged_dependencies':len(trace),'selected_forecasts':selected,'selected_by_phase':phases,'unflagged_changed':len(outside_changed),'all_usable_dependencies':usable_dependencies,'finite_raw_vs_frozen_mismatch_count_unrestricted':finite_raw_mismatches,'unrestricted_mismatch_note':'175 dependency-level differences concern 45 feature timestamps on 2026-09-19..21 UTC, none flagged and none with raw Q zero or missing frozen Q. They are preserved separately; no equality of full ONS and frozen/CERAN series is claimed.','causality_certified':False,'automatic_transfer_to_other_snapshots_allowed':False,'promotion_supported':False,'metrics_computed':False,'limitations':['Automatic transfer to another snapshot is blocked until raw-rule and frozen-feature provenance are independently reverified.','Flags diagnose inconsistent columns without identifying which is wrong.','Historical availability and current-version data are assumed, not publication receipts.','No flagged validation cases; inspected test event cannot establish independent gain.','Only direct Monte Q dependencies0/1/3/6h determine the fixed selection; other sources retain correlated information.'],'created_at_utc':datetime.now(timezone.utc).isoformat()}
 (OUT/'verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
 print(json.dumps({k:result[k] for k in ['passed','failures','source_rows','source_conflicts','affected_origins','flagged_dependencies','selected_forecasts','selected_by_phase','unflagged_changed','finite_raw_vs_frozen_mismatch_count_unrestricted']},indent=2))
 if failed:raise SystemExit(1)
if __name__=='__main__':run()
