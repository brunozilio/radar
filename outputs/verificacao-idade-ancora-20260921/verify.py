"""Read-only audit of completed anchor-age runs; writes only this directory."""
from pathlib import Path
from datetime import datetime,timezone
import ast,csv,hashlib,json,math
import numpy as np
ROOT=Path('/Users/brunozilio/Documents/radar')
OUT=ROOT/'outputs/verificacao-idade-ancora-20260921'
BASE=ROOT/'outputs/experimento-proxy-carreiro-20260921'
RUNS={d:ROOT/f'outputs/experimento-idade-ancora-{d}min-20260921' for d in (15,30,45)}
TOL=1e-10
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p):return json.loads(p.read_text())
def rows(p):return list(csv.DictReader(p.open()))
def key(r):return r['origin'],r['target_time'],int(r['nominal_lead_h'])
def stamp(s):return datetime.fromisoformat(s).timestamp()
def expr(s):return ast.dump(ast.parse(s,mode='eval').body,include_attributes=False)
checks=[];errors=[];inputhashes={}
def check(label,ok,detail=None):
 checks.append({'check':label,'passed':bool(ok),'detail':detail})
 if not ok:errors.append(label)
def readhash(p):
 inputhashes[str(p)]=sha(p);return p
def compare_npz(a,b,label):
 with np.load(readhash(a)) as x,np.load(readhash(b)) as y:
  check(label+': keys',set(x.files)==set(y.files),{'keys_a':x.files,'keys_b':y.files})
  for k in x.files:
   if k not in y:continue
   u,v=x[k],y[k]
   same=u.shape==v.shape and u.dtype==v.dtype and np.array_equal(u,v,equal_nan=True)
   check(label+': '+k,same,{'shape':list(u.shape),'dtype':str(u.dtype)})
def run():
 missing=[str(p/'experiment.json') for p in RUNS.values() if not (p/'experiment.json').exists()]
 if missing:
  print(json.dumps({'waiting_for':missing}));return
 OUT.mkdir(parents=True,exist_ok=True)
 old=rows(readhash(BASE/'predictions.csv'));oldkeys=[key(r) for r in old];oldmap={key(r):r for r in old}
 check('baseline rows and unique keys',len(old)==len(oldmap)==23538)
 oldmeta=js(readhash(BASE/'experiment.json'));oldmodels=js(readhash(BASE/'proxy-models.json'))
 metas={};data={};codehashes={}
 for d,p in RUNS.items():
  m=js(readhash(p/'experiment.json'));metas[d]=m
  r=rows(readhash(p/'predictions.csv'));data[d]=r
  check(f'{d}: 23538 unique rows',len(r)==len({key(x) for x in r})==23538)
  check(f'{d}: origin-target keys and order unchanged',[key(x) for x in r]==oldkeys)
  check(f'{d}: actual targets unchanged',all(x['actual_m']==oldmap[key(x)]['actual_m'] for x in r))
  check(f'{d}: horizon equals target-origin',all(stamp(x['target_time'])-stamp(x['origin'])==int(x['nominal_lead_h'])*3600 for x in r))
  check(f'{d}: anchor timestamp and row age',all(stamp(x['origin'])-stamp(x['anchor_at'])==d*60 and int(x['anchor_delay_minutes'])==d for x in r))
  check(f'{d}: rain state ends origin-1h',all(stamp(x['origin'])-stamp(x['state_rain_observations_end_at'])==3600 for x in r))
  check(f'{d}: proxy-use flags unchanged',all(all(x[k]==oldmap[key(x)][k] for k in ['modeled_car_history_inputs','modeled_car_future_inputs','uses_missing_flow_proxy','upstream_target_observation_missing']) for x in r))
  check(f'{d}: metadata age',m['anchor_delay_minutes']==d)
  check(f'{d}: unchanged proxy models by parsed content',js(readhash(p/'proxy-models.json'))==oldmodels)
  compare_npz(BASE/'modeled-carreiro-inputs.npz',p/'modeled-carreiro-inputs.npz',f'{d}: frozen proxy arrays')
  check(f'{d}: proxy training records unchanged',rows(readhash(p/'proxy-training.csv'))==rows(readhash(BASE/'proxy-training.csv')))
  protocol=js(readhash(p/'protocol.json'));check(f'{d}: protocol copy exact',sha(p/'protocol.json')==sha(readhash(ROOT/f'docs/anchor-delay-{d}min-protocol.json')))
  check(f'{d}: protocol anchor age',protocol['anchor_delay_minutes']==d)
  changes=[]
  original_paths=set(oldmeta['input_sha256'])-{str(ROOT/'docs/carreiro-missing-flow-proxy-protocol.json')}
  scenario_paths=set(m['input_sha256'])-{str(ROOT/f'docs/anchor-delay-{d}min-protocol.json')}
  check(f'{d}: same input path set except protocol',original_paths==scenario_paths)
  for name,digest in m['input_sha256'].items():
   path=Path(name);actual=sha(readhash(path))
   check(f'{d}: input hash matches {name}',actual==digest)
   prior=oldmeta['input_sha256'].get(name)
   if prior is not None and prior!=digest:
    changes.append(name)
    check(f'{d}: allowed baseline input change {name}',name==str(ROOT/'scripts/hydro_reservoir_mucum_experiment.py'))
  saved=p/'code/hydro_reservoir_mucum_experiment.py';readhash(saved);codehashes[d]=sha(saved)
  check(f'{d}: executed source snapshot exact',sha(saved)==m['input_sha256'][str(ROOT/'scripts/hydro_reservoir_mucum_experiment.py')])
  check(f'{d}: source copies match input hashes',all(sha(p/'code'/Path(name).name)==digest for name,digest in m['input_sha256'].items() if Path(name).suffix=='.py'))
  if d==15:
   check('15: baseline statuses identical',all(x['status']==oldmap[key(x)]['status'] for x in r))
   for field in ['reference_m','julho_levels_m']:
    diffs=[];bad=[];missing_same=True
    for x in r:
     a,b=x[field],oldmap[key(x)][field]
     if not a or not b:
      missing_same &= a==b;continue
     av,bv=float(a),float(b)
     if not math.isfinite(av) or not math.isfinite(bv):bad.append(key(x));continue
     diffs.append(abs(av-bv))
    check('15: '+field+' missing pattern',missing_same)
    check('15: '+field+' finite equivalence',not bad and max(diffs,default=0)<=TOL,{'compared_finite':len(diffs),'max_absolute_difference_m':max(diffs,default=0),'nonfinite_numeric_rows':len(bad),'tolerance_m':TOL})
 check('all3: identical executed code',len(set(codehashes.values()))==1)
 # Across scenarios only the protocol path/hash differs in recorded inputs.
 norm={d:{k:v for k,v in m['input_sha256'].items() if not k.endswith(f'anchor-delay-{d}min-protocol.json')} for d,m in metas.items()}
 check('all3: same non-protocol input hashes',norm[15]==norm[30]==norm[45])
 protocols={d:js(RUNS[d]/'protocol.json') for d in RUNS}
 allowed={'experiment_id','anchor','initial_correction','anchor_delay_minutes'}
 normalized={d:{k:v for k,v in p.items() if k not in allowed} for d,p in protocols.items()}
 check('all3: no other protocol change',normalized[15]==normalized[30]==normalized[45])
 source=(RUNS[15]/'code/hydro_reservoir_mucum_experiment.py').read_text();tree=ast.parse(source)
 nodes={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
 # Execute only two pure functions extracted from the preserved AST, not the pipeline.
 pure=ast.Module(body=[nodes[k] for k in ['anchor_delay_hours','reconstruct_anchor']],type_ignores=[])
 env={};exec(compile(pure,'preserved-pure-anchor-functions','exec'),env)
 for d in RUNS:
  f=env['anchor_delay_hours'](d)
  check(f'{d}: delay conversion',f==d/60)
  check(f'{d}: interpolation weights',env['reconstruct_anchor'](100.,200.,f)==f*100+(1-f)*200)
  check(f'{d}: constant-flow interpolation',env['reconstruct_anchor'](123.,123.,f)==123.)
  check(f'{d}: linear-flow interpolation',env['reconstruct_anchor'](40.,100.,f)==100-d)
 for invalid in [0,60,-15,16,True,None,'15',15.0]:
  try:env['anchor_delay_hours'](invalid);rejected=False
  except (ValueError,TypeError):rejected=True
  # Float15 acceptance depends on explicit implementation; do not impose unrequested type restriction.
  if invalid!=15.0:check('invalid delay rejected '+repr(invalid),rejected)
 expected=[
 'delay_h * previous_q + (1 - delay_h) * origin_q',
 'np.exp(-(horizon + delay_h) / 6)',
 'anchor_index(z["times"], t[i], delay_minutes * 60)',
 'reconstruct_anchor(previous_q, origin_q, delay_h)',
 'iso(t[i] - delay_minutes * 60)']
 expressions={ast.dump(n,include_attributes=False) for n in ast.walk(tree) if isinstance(n,ast.expr)}
 for e in expected:check('source formula '+e,expr(e) in expressions)
 # Need snapshot, not assumptions about current source text.
 (OUT/'executed-hydro_reservoir_mucum_experiment.py').write_text(source)
 result={'passed':not errors,'check_count':len(checks),'failures':errors,'checks':checks,'input_sha256':inputhashes,'scope':'Artifact invariance and source/pure-function formula verification, not full rerun or retrospective publication proof','causality_certified':False,'metrics_compared':False,'tolerance_15min_m':TOL,'created_at_utc':datetime.now(timezone.utc).isoformat()}
 (OUT/'verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
 print(json.dumps({'passed':not errors,'checks':len(checks),'failures':errors,'15min_values':[c for c in checks if c['check'].startswith('15: ') and 'finite equivalence' in c['check']]},indent=2))
 if errors:raise SystemExit(1)
if __name__=='__main__':run()
