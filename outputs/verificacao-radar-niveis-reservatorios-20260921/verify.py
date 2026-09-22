"""Frozen-model Radar verification, without refits or HGE execution."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import ast,csv,json,hashlib,importlib.metadata
import numpy as np
import joblib
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
EXP=ROOT/'outputs/experimento-radar-niveis-reservatorios-20260921'
PRIOR=ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921'
LEVELS=ROOT/'outputs/experimento-niveis-reservatorios-20260921'
AUDIT=ROOT/'outputs/auditoria-features-reservatorios-radar-20260921'
TZ=timezone(timedelta(hours=-3))
def ep(s):
    x=datetime.fromisoformat(s);return (x if x.tzinfo else x.replace(tzinfo=TZ)).timestamp()
def iso(t):return datetime.fromtimestamp(float(t),TZ).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p):return list(csv.DictReader(p.open()))
def num(v):return float(v) if v else np.nan
def dump(n,x):(OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
checks=[]
def check(name,ok,**info):checks.append(dict(name=name,passed=bool(ok),**info))
def eq(name,a,b,tol=0):
    a,b=np.asarray(a,float),np.asarray(b,float);same=a.shape==b.shape
    finite=np.isfinite(a)&np.isfinite(b) if same else np.array([],bool)
    error=float(np.max(abs(a[finite]-b[finite]))) if finite.any() else 0.
    check(name,same and np.array_equal(np.isnan(a),np.isnan(b)) and np.array_equal(np.isposinf(a),np.isposinf(b)) and np.array_equal(np.isneginf(a),np.isneginf(b)) and error<=tol,max_abs_difference=error,finite_values=int(finite.sum()),tolerance=tol)
if not (EXP/'experiment.json').exists():raise SystemExit('Experiment not complete; no restart or fit performed.')
meta=json.loads((EXP/'experiment.json').read_text());prior_meta=json.loads((PRIOR/'experiment.json').read_text())
for p,digest in meta['input_sha256'].items():check('input_hash:'+p,sha(Path(p))==digest)
# Only executed core artifacts; reports may still be edited by their owner.
manifest=json.loads((EXP/'artifact-hashes.json').read_text())
core=[r for r in manifest if r['file'].startswith(('models/','code/')) or r['file'] in ['predictions.csv','evaluation.csv','training.csv','features.npz','experiment.json','protocol.json']]
for r in core:check('core_artifact_hash:'+r['file'],sha(EXP/r['file'])==r['sha256'])
check('protocol_snapshot',(EXP/'protocol.json').read_bytes()==(ROOT/'docs/radar-reservoir-features-protocol.json').read_bytes())
check('identical_operational_runtime',meta['runtime']==prior_meta['runtime'] and all(importlib.metadata.version(k)==v for k,v in meta['runtime'].items()))
check('no_promotion_or_live_issue',all(meta[k] is False for k in ['promoted','live_issuance','goal_achieved']))
check('reused_baseline_not_refitted_metadata',meta['baseline_models_refitted']==0)
code=ast.parse((EXP/'code/hydro_radar_reservoir_features.py').read_text())
fit_receivers=[ast.unparse(n.func.value) for n in ast.walk(code) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='fit']
check('only_candidate_fit_in_executed_source',fit_receivers==['candidate'],receivers=fit_receivers)

p=dict(np.load(PRIOR/'features.npz'));e=dict(np.load(EXP/'features.npz'));a=dict(np.load(LEVELS/'additional-features.npz'))
t=p['times'];F=p['features'];extra=a['levels_and_slopes'];X=np.column_stack([F,extra]);H=p['base'];truth=p['truth'];complete=p['complete24']
for name in ['times','base','truth','complete24']:eq('preserved_'+name,e[name],p[name])
eq('reservoir_grid_exact',a['times'],t);eq('204_features_exact',e['features'],X)
check('correct_shapes',F.shape==(len(t),180) and extra.shape==(len(t),24) and X.shape==(len(t),204))
check('no_infinite_features',not np.isinf(X).any())
audit=json.loads((AUDIT/'verification.json').read_text());audit_inputs=json.loads((AUDIT/'artifact-input-manifest.json').read_text())
check('source_provenance_audit_passed',audit['passed'] and audit['columns']==24 and audit['origins']==len(t))
check('source_provenance_same_npz',sha(LEVELS/'additional-features.npz')==next(r['sha256'] for r in audit_inputs if r['path']==str((LEVELS/'additional-features.npz').resolve())))

rows=readcsv(EXP/'predictions.csv');old=readcsv(PRIOR/'predictions.csv')
check('102084_rows',len(rows)==len(old)==102084==meta['rows'])
identity=['phase','origin','target_time','nominal_lead_h','original_complete24','base_m','actual_m']
check('exact_order_keys_targets_base',[[r[k] for k in identity] for r in rows]==[[r[k] for k in identity] for r in old])
eq('baseline_all_rows_exact',[num(r['baseline_m']) for r in rows],[num(r['baseline_m']) for r in old])
index={(r['phase'],r['origin'],int(r['nominal_lead_h'])):r for r in rows}
check('unique_keys',len(index)==len(rows))
training={(r['phase'],int(r['horizon_h'])):r for r in readcsv(EXP/'training.csv')}
oldtrain={(r['phase'],int(r['horizon_h'])):r for r in readcsv(PRIOR/'training.csv') if r['family']=='baseline'}
prior_manifest={r['file']:r['sha256'] for r in json.loads((PRIOR/'artifact-hashes.json').read_text())}
start=ep('2025-10-01T00:00:00-03:00');end=ep('2026-07-01T00:00:00-03:00');stop=ep('2026-09-21T00:00:00-03:00')
coverage=[];membership=[];scheduled_keys=set()
with threadpool_limits(limits=2):
  for h in range(1,13):
    target=np.r_[truth[h:],np.full(h,np.nan)];delta=target-H;finite=np.isfinite(H)&np.isfinite(target)
    first=t+h*3600<start;second=(t>=start)&(t+h*3600<end);weights=1+2*(abs(delta)>=1)+2*(target>=9)
    for phase,left,right in [('validation',start,end),('test',end,stop)]:
      train=np.flatnonzero(finite&complete&(first if phase=='validation' else (first|second)))
      tr=training[phase,h];oldtr=oldtrain[phase,h]
      check(f'training_metadata:{phase}:{h}',len(train)==int(tr['training_n'])==int(oldtr['n']) and iso((t[train]+h*3600).max())==tr['latest_training_target']==oldtr['latest_training_target'] and tr['cutoff_exclusive']==oldtr['cutoff_exclusive'] and (t[train]+h*3600).max()<ep(tr['cutoff_exclusive']) and int(tr['features'])==204 and int(tr['leaf_nodes'])==int(oldtr['leaf_nodes']) and tr['loss']==oldtr['loss'])
      missing=int((~np.isfinite(extra[train]).all(axis=1)).sum())
      check(f'added_NaN_does_not_filter_train:{phase}:{h}',missing==int(tr['training_with_missing_reservoir_input']))
      scheduled=np.flatnonzero((t>=left)&(t+h*3600<right));apply=scheduled[np.isfinite(H[scheduled])];saved=[index[phase,iso(t[i]),h] for i in scheduled]
      scheduled_keys.update((phase,iso(t[i]),h) for i in scheduled)
      check(f'target_and_reservoir_missing_counts:{phase}:{h}',all(ep(r['target_time'])==t[i]+h*3600 and int(r['missing_reservoir_inputs'])==int((~np.isfinite(extra[i])).sum()) for i,r in zip(scheduled,saved)))
      eq(f'actual_targets:{phase}:{h}',[num(r['actual_m']) for r in saved],target[scheduled])
      basename=f'models/{phase}-baseline-{h}.joblib';control_path=PRIOR/basename
      check(f'frozen_baseline_hash:{phase}:{h}',sha(control_path)==prior_manifest[basename]==meta['input_sha256'][str(control_path.resolve())])
      control=joblib.load(control_path);candidate=joblib.load(EXP/f'models/{phase}-{h}.joblib')
      check(f'same_model_configuration:{phase}:{h}',candidate.get_params()==control.get_params() and candidate.n_iter_==control.n_iter_==180 and candidate.n_features_in_==204 and control.n_features_in_==180)
      check(f'candidate_root_counts:{phase}:{h}',all(int(tree[0].nodes[0]['count'])==len(train) for tree in candidate._predictors))
      eq(f'candidate_control_initial_intercept:{phase}:{h}',candidate._baseline_prediction,control._baseline_prediction)
      for family,model,features in [('baseline',control,F),('candidate',candidate,X)]:
        prediction=np.full(len(t),np.nan);prediction[apply]=model.predict(features[apply])+H[apply]
        eq(f'inference:{phase}:{family}:{h}',[num(r[family+'_m']) for r in saved],prediction[scheduled],1e-10)
        check(f'coverage_only_base_missing:{phase}:{family}:{h}',np.array_equal(np.isfinite([num(r[family+'_m']) for r in saved]),np.isfinite(H[scheduled])))
      membership.append(dict(phase=phase,horizon_h=h,n=len(train),added_inputs_missing=missing,indices_sha256=hashlib.sha256(train.tobytes()).hexdigest(),delta_sha256=hashlib.sha256(delta[train].tobytes()).hexdigest(),weights_sha256=hashlib.sha256(weights[train].tobytes()).hexdigest()))
      coverage.append(dict(phase=phase,horizon_h=h,scheduled=len(scheduled),base_missing=int((~np.isfinite(H[scheduled])).sum()),target_missing=int((~np.isfinite(target[scheduled])).sum()),paired=int(finite[scheduled].sum()),missing_target_with_prediction=int((np.isfinite(H)&~np.isfinite(target))[scheduled].sum()),scheduled_with_missing_reservoir_inputs=int((~np.isfinite(extra[scheduled]).all(axis=1)).sum())))
check('exact_all_scheduled_keys',scheduled_keys==set(index))
check('24_candidate_models',len(training)==24==meta['models_fitted'] and len(list((EXP/'models').glob('*.joblib')))==24)
check('identical_family_availability',all(bool(r['baseline_m'])==bool(r['candidate_m']) for r in rows) and meta['identical_candidate_baseline_availability'])
prior_eval={tuple(r[k] for k in ['phase','horizon_h','subset','population','family']):r for r in readcsv(PRIOR/'evaluation.csv')}
evaluation=readcsv(EXP/'evaluation.csv')
baseline_eval_same=True;coverage_eval_same=True
for r in evaluation:
    key=tuple(r[k] for k in ['phase','horizon_h','subset','population','family'])
    baselinekey=key[:-1]+('baseline',)
    if r['family']=='baseline':baseline_eval_same &= r==prior_eval[key]
    coverage_eval_same &= all(r[k]==prior_eval[baselinekey][k] for k in ['scheduled_rows','observed_targets','n','failures'])
check('baseline_evaluation_all_fields_exact',baseline_eval_same)
check('both_families_evaluation_same_coverage',coverage_eval_same)
check('producer_zero_baseline_delta',meta['maximum_baseline_reproduction_difference_m']==0)
dump('membership.json',membership);dump('coverage.json',coverage)
dump('verification.json',dict(passed=all(r['passed'] for r in checks),checks=checks,rows=len(rows),models_inferred=48,candidate_models=24,baseline_models_reused=24,scope='No refits or HGE. Core execution artifacts verified; owner-edited reports intentionally excluded from hash gate.',limitations=['Historical source timestamp/availability and gauge reference assumptions remain those of the 24-feature audit.','Training membership corroborated via code, metadata, tree root counts and initial intercept; tree splits not refitted independently.','Old native-missing candidate is not used: both families retain original complete24 training membership.','Already inspected development, not independent validation, promotion or prospective accuracy evidence.']))
dump('artifact-hashes.json',[dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'])
print(json.dumps(dict(passed=all(r['passed'] for r in checks),checks=len(checks),failed=[r for r in checks if not r['passed']],rows=len(rows)),ensure_ascii=False))
