"""Independent tau artifact/inference audit, no fit or HGE execution."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import ast,csv,hashlib,json,math
import numpy as np
ROOT=Path('/Users/brunozilio/Documents/radar');OUT=ROOT/'outputs/verificacao-correcao-tau-20260921';BASE=ROOT/'outputs/mucum-atualizacao-15h-2026-09-21'
PRIOR=ROOT/'outputs/experimento-proxy-carreiro-20260921';RUNS={tau:ROOT/f'outputs/experimento-correcao-tau-{tau}h-20260921' for tau in [6,2,12]}
checks=[];hashes={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):hashes[str(p)]=sha(p);return p
def js(p):return json.loads(read(p).read_text())
def rows(p):return list(csv.DictReader(read(p).open()))
def check(k,v,d=None):checks.append(dict(check=k,passed=bool(v),detail=d))
def ep(s):return datetime.fromisoformat(s).timestamp()
def val(s):return float(s) if s else np.nan
def key(r):return r['origin'],r['target_time'],int(r['nominal_lead_h'])
def equal(a,b):return (not a and not b) or bool(a and b and float(a)==float(b))
def run():
 missing=[str(p/'experiment.json') for p in RUNS.values() if not (p/'experiment.json').exists()]
 if missing:print(json.dumps({'waiting':missing}));return
 OUT.mkdir(parents=True,exist_ok=True);oldrows=rows(PRIOR/'predictions.csv');oldmeta=js(PRIOR/'experiment.json');oldproxy=js(PRIOR/'proxy-models.json')
 oldkeys=[key(r) for r in oldrows];oldmap={key(r):r for r in oldrows};data={};metas={};policies={};codehash={}
 for tau,p in RUNS.items():
  meta=js(p/'experiment.json');metas[tau]=meta;policy=js(p/'protocol.json');policies[tau]=policy
  check(f'{tau}: completed metadata',meta['correction_tau_hours']==tau and meta['anchor_delay_minutes']==15)
  check(f'{tau}: protocol copied',sha(read(ROOT/f'docs/residual-tau-{tau}h-protocol.json'))==sha(p/'protocol.json') and policy['correction_tau_hours']==tau and policy['anchor_delay_minutes']==15)
  for name,digest in meta['input_sha256'].items():
   path=Path(name);check(f'{tau}: input hash '+name,sha(read(path))==digest)
   if path.suffix=='.py':check(f'{tau}: executed source '+path.name,sha(read(p/'code'/path.name))==digest)
   if name in oldmeta['input_sha256'] and name!=str(ROOT/'scripts/hydro_reservoir_mucum_experiment.py'):check(f'{tau}: original input '+name,digest==oldmeta['input_sha256'][name])
  source=p/'code/hydro_reservoir_mucum_experiment.py';codehash[tau]=sha(source)
  check(f'{tau}: frozen proxy models unchanged',js(p/'proxy-models.json')==oldproxy)
  check(f'{tau}: proxy training records unchanged',rows(p/'proxy-training.csv')==rows(PRIOR/'proxy-training.csv'))
  with np.load(read(p/'modeled-carreiro-inputs.npz')) as candidate,np.load(read(PRIOR/'modeled-carreiro-inputs.npz')) as old:
   check(f'{tau}: proxy NPZ same keys',set(candidate.files)==set(old.files))
   for k in old.files:check(f'{tau}: proxy NPZ '+k,candidate[k].shape==old[k].shape and candidate[k].dtype==old[k].dtype and np.array_equal(candidate[k],old[k],equal_nan=True))
  r=rows(p/'predictions.csv');data[tau]=r
  check(f'{tau}:23538 keys/order/uniqueness',len(r)==23538 and len({key(x) for x in r})==23538 and [key(x) for x in r]==oldkeys)
  invariant=['actual_m','anchor_at','state_rain_observations_end_at','upstream_target_observation_missing','modeled_car_history_inputs','modeled_car_future_inputs','uses_missing_flow_proxy']
  check(f'{tau}: targets anchors and proxy-use exact',all(all(x[k]==oldmap[key(x)][k] for k in invariant) for x in r))
  check(f'{tau}: row tau and anchor age',all(int(x['correction_tau_hours'])==tau and int(x['anchor_delay_minutes'])==15 and ep(x['origin'])-ep(x['anchor_at'])==900 for x in r))
 check('all three same executed code',len(set(codehash.values()))==1)
 normalized={tau:{k:v for k,v in m['input_sha256'].items() if k!=str(ROOT/f'docs/residual-tau-{tau}h-protocol.json')} for tau,m in metas.items()}
 check('all three same non-protocol input hashes',normalized[6]==normalized[2]==normalized[12])
 allowed={'experiment_id','hge','initial_correction','correction_tau_hours'}
 norm={tau:{k:v for k,v in p.items() if k not in allowed} for tau,p in policies.items()}
 check('protocols differ only documented tau fields',norm[6]==norm[2]==norm[12])
 refs={key(r):r for r in data[6]}
 compfields=['reference_uncorrected_q_m3_s','julho_levels_uncorrected_q_m3_s','anchor_residual_q_m3_s']
 for tau in [2,12]:check(f'{tau}: uncorrected components and anchor residual invariant',all(all(r[k]==refs[key(r)][k] for k in compfields) for r in data[tau]))
 check('tau6 statuses identical original',all(r['status']==oldmap[key(r)]['status'] for r in data[6]))
 for family in ['reference','julho_levels']:
  errs=[];missingok=True
  for r in data[6]:
   x,y=r[family+'_m'],oldmap[key(r)][family+'_m']
   if not x or not y:missingok &= x==y
   else:errs.append(abs(float(x)-float(y)))
  check('tau6 baseline reproduction '+family,missingok and max(errs,default=0)<=1e-10,{'finite_pairs':len(errs),'max_difference_m':max(errs,default=0)})
 z=dict(np.load(read(BASE/'telemetria-latencia.npz')));rating=js(BASE/'conferencia-balanco.json')['rating_parameters'];a,b,c=rating
 maximums={};statuses={};negatives={};failures=[];outrows=[]
 for tau,rr in data.items():
  corrmax=qmax=hmax=0.;negative=0;bad=0;residual_by_origin={};missinganchor=0
  for r in rr:
   h=int(r['nominal_lead_h']);res=val(r['anchor_residual_q_m3_s']);expected=res*math.exp(-(h+.25)/tau);saved=val(r['decayed_correction_q_m3_s'])
   if np.isfinite(expected)!=np.isfinite(saved):bad+=1
   elif np.isfinite(expected):corrmax=max(corrmax,abs(expected-saved))
   if r['origin'] in residual_by_origin and residual_by_origin[r['origin']]!=r['anchor_residual_q_m3_s']:bad+=1
   residual_by_origin[r['origin']]=r['anchor_residual_q_m3_s']
   ai=int(np.searchsorted(z['times'],ep(r['anchor_at'])));assert z['times'][ai]==ep(r['anchor_at'])
   ah=z['raw:86510000:H'][ai];aq=z['raw:86510000:Q'][ai];finite_anchor=np.isfinite([ah,aq]).all()
   values=[];row={'tau_h':tau,'origin':r['origin'],'horizon_h':h,'independent_correction_m3_s':expected if np.isfinite(expected) else None}
   for family in ['reference','julho_levels']:
    q=val(r[family+'_uncorrected_q_m3_s'])+expected;qstored=val(r[family+'_corrected_q_m3_s'])
    if np.isfinite(q)!=np.isfinite(qstored):bad+=1
    elif np.isfinite(q):qmax=max(qmax,abs(q-qstored))
    if np.isfinite(q) and q<0:negative+=1
    level=a*(q/1000)**b+c+ah-(a*(aq/1000)**b+c) if finite_anchor and np.isfinite(q) and q>=0 else np.nan
    stored=val(r[family+'_m']);values.append(level)
    if np.isfinite(level)!=np.isfinite(stored):bad+=1
    elif np.isfinite(level):hmax=max(hmax,abs(level-stored))
    row[family+'_q_m3_s']=q if np.isfinite(q) else None;row[family+'_m']=level if np.isfinite(level) else None
   expectedstatus='missing_exact_anchor' if not finite_anchor else 'missing_or_invalid_forecast_input' if not np.isfinite(values).all() else 'missing_exact_target' if not r['actual_m'] else 'paired'
   if not finite_anchor:missinganchor+=1
   if r['status']!=expectedstatus:bad+=1
   row['expected_status']=expectedstatus;outrows.append(row)
  maximums[tau]={'correction_difference_m3_s':corrmax,'corrected_q_difference_m3_s':qmax,'level_difference_m':hmax,'row_or_missing_errors':bad}
  statuses[tau]=dict(Counter(r['status'] for r in rr));negatives[tau]=negative
  check(f'{tau}: complete independent exponential/q/stage/status replay',bad==0 and corrmax<=1e-8 and qmax<=1e-8 and hmax<=1e-10,maximums[tau])
  check(f'{tau}: original missing anchors preserved',all(r['status']=='missing_exact_anchor' for r in rr if oldmap[key(r)]['status']=='missing_exact_anchor'),{'missing_anchor_rows':missinganchor})
 source=(RUNS[6]/'code/hydro_reservoir_mucum_experiment.py').read_text();tree=ast.parse(source);fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='residual_correction');env={'np':np}
 exec(compile(ast.Module(body=[fun],type_ignores=[]),'pure-residual-correction','exec'),env);fn=env['residual_correction']
 for tau in [2,6,12]:
  for r in [-100.,0.,100.]:
   for elapsed in [0.,1.25,12.25]:check(f'pure signed residual {tau}/{r}/{elapsed}',abs(fn(r,elapsed,tau)-r*math.exp(-elapsed/tau))<=1e-12)
 for tau in [0,1,True,float('nan')]:
  try:fn(1.,1.,tau);ok=False
  except (ValueError,TypeError):ok=True
  check('invalid tau '+repr(tau),ok)
 for elapsed in [-1.,float('nan'),float('inf')]:
  try:fn(1.,elapsed,6);ok=False
  except ValueError:ok=True
  check('invalid elapsed '+repr(elapsed),ok)
 calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='residual_correction']
 check('source call uses h+anchor age',any(ast.dump(n,include_attributes=False)==ast.dump(ast.parse('residual_correction(residual,horizon+delay_h,tau_hours)',mode='eval').body,include_attributes=False) for n in calls))
 check('no promotion in any scenario',all(not m['promoted'] and not m['live_issuance'] for m in metas.values()) if all('promoted' in m for m in metas.values()) else all(not p['promotion'] and not p['live_issuance'] for p in policies.values()))
 check('all audited inputs unchanged',all(sha(Path(p))==v for p,v in hashes.items()))
 with (OUT/'independent-component-replay.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(outrows[0]));w.writeheader();w.writerows(outrows)
 failed=[r['check'] for r in checks if not r['passed']]
 result={'passed':not failed,'failures':failed,'checks':checks,'input_sha256':hashes,'rows_each':23538,'maximum_replay_differences':maximums,'status_counts':statuses,'negative_corrected_q_counts_across_both_families':negatives,'fits_performed':0,'performance_metrics_computed':False,'full_hge_rerun':False,'causality_certified':False,'limitations':['Recombination uses preserved uncorrected components and anchor residual, not an independent full HGE simulation.','Changing tau is a statistical correction sensitivity; not a physical water-balance statement.','Historical source availability remains assumed, and previously inspected periods do not support promotion.'],'created_at_utc':datetime.now(timezone.utc).isoformat()}
 (OUT/'verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
 print(json.dumps({k:result[k] for k in ['passed','failures','maximum_replay_differences','status_counts','negative_corrected_q_counts_across_both_families']},indent=2))
 if failed:raise SystemExit(1)
if __name__=='__main__':run()

