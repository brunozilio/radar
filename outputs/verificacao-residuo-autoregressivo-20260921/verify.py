"""Independent artifact verification; no fitting, HGE run, or source mutation."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import csv, hashlib, json
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
EXP = ROOT/'outputs/experimento-residuo-autoregressivo-20260921'
BASE = ROOT/'outputs/experimento-correcao-tau-6h-20260921'
DATA = ROOT/'outputs/mucum-atualizacao-15h-2026-09-21'
checks=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p): return list(csv.DictReader(p.open()))
def epoch(s): return datetime.fromisoformat(s).timestamp()
def num(s): return float(s) if s != '' else np.nan
def check(name, passed, **detail):
    checks.append(dict(name=name,passed=bool(passed),**detail))
def eq(name,a,b,tol=0):
    a,b=np.asarray(a,dtype=float),np.asarray(b,dtype=float)
    same=a.shape==b.shape
    finite=np.isfinite(a)&np.isfinite(b) if same else np.array([],dtype=bool)
    diff=float(np.max(abs(a[finite]-b[finite]))) if finite.any() else 0.
    missing=same and np.array_equal(np.isnan(a),np.isnan(b)) and np.array_equal(np.isposinf(a),np.isposinf(b)) and np.array_equal(np.isneginf(a),np.isneginf(b))
    check(name,same and missing and diff<=tol,max_abs_difference=diff,finite_values=int(finite.sum()),tolerance=tol)
def dump(name,value): (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

meta=json.loads((EXP/'experiment.json').read_text())
for name,digest in meta['input_sha256'].items(): check('input_hash:'+name,sha(Path(name))==digest)
for item in json.loads((EXP/'artifact-hashes.json').read_text()):
    check('artifact_hash:'+item['file'],sha(EXP/item['file'])==item['sha256'])
check('protocol_snapshot', (EXP/'protocol.json').read_bytes()==(ROOT/'docs/residual-autoregression-protocol.json').read_bytes())
check('code_snapshot',(EXP/'code/hydro_residual_autoregression.py').read_bytes()==(ROOT/'scripts/hydro_residual_autoregression.py').read_bytes())
s=dict(np.load(EXP/'residual-series.npz'))
d=dict(np.load(DATA/'dados-roteamento.npz')); z=dict(np.load(DATA/'telemetria-latencia.npz'))
p=dict(np.load(BASE/'modeled-carreiro-inputs.npz'))
t=s['times'];n=len(t);cutoff=epoch('2026-07-01T00:00:00-03:00')
eq('times_source',t,d['times']);eq('times_proxy',t,p['times'])
check('hourly_grid',np.all(np.diff(t)==3600))
zi=np.searchsorted(z['times'],t);eq('exact_raw_ANA_timestamps',z['times'][zi],t)
qraw=z['raw:86510000:Q'][zi]
kernels=rows(DATA/'roteamento-vazao-pesos.csv')
route=np.zeros(n);used=[]
for source,label,lags in [('julho','14 de Julho',range(1,13)),('carreiro','Passo Carreiro',range(4,25))]:
    q=d[source]*1000
    if source=='carreiro': q=np.where(np.isfinite(q),q,p['estimated_q_m3_s'][:,0])
    weights=[float(r['weight']) for r in kernels if r['source']==label]
    check('positive_lags:'+source,all(lag>0 for lag in lags) and len(weights)==len(lags))
    check('nonnegative_normalized_weights:'+source,min(weights)>=0 and abs(sum(weights)-1)<1e-6)
    partial=np.zeros(n)
    for lag,w in zip(lags,weights):
        if w==0: continue
        shifted=np.r_[np.full(lag,np.nan),q[:n-lag]]
        partial+=w*shifted;used.append(dict(source=source,lag=lag,weight=w))
    route+=partial
eq('routed_independent_sum',route,s['routed'],1e-8)
final=qraw-route-s['local_q']
eq('finalized_residual_raw_Q_minus_route_minus_saved_local',final,s['finalized_residual'],1e-8)
X=np.full((n,4),np.nan);X[:,0]=s['anchor_residual']
for j,lag in enumerate([1,3,6],1): X[lag:,j]=final[:-lag]
eq('feature_alignment',X,s['X'],1e-8)
# The first 25 origins intentionally lack an anchor in the producer.
for k,source in [('anchor_h','raw:86510000:H'),('anchor_q','raw:86510000:Q')]:
    expected=np.full(n,np.nan)
    for i in range(25,n):
        j=int(np.searchsorted(z['times'],t[i]-900))
        if j<len(z['times']) and z['times'][j]==t[i]-900: expected[i]=z[source][j]
    eq(k+'_exact_source',expected,s[k])

models=json.loads((EXP/'models.json').read_text());training={int(r['horizon_h']):r for r in rows(EXP/'training.csv')}
check('twelve_models',set(models)==set(map(str,range(1,13))) and set(training)==set(range(1,13)))
prediction={};train_audit=[]
for h in range(1,13):
    y=np.r_[final[h:],np.full(h,np.nan)]
    targets=t+h*3600
    mask=np.isfinite(X).all(axis=1)&np.isfinite(y)&(targets<cutoff)
    tr=training[h];model=models[str(h)];m=np.array(model['mean']);sc=np.array(model['scale']);b=np.array(model['beta']);inter=model['intercept']
    eq(f'mean_train_only_h{h}',m,X[mask].mean(axis=0),1e-10)
    expected_scale=X[mask].std(axis=0);expected_scale[expected_scale<1e-8]=1
    eq(f'std_train_only_h{h}',sc,expected_scale,1e-10)
    eq(f'intercept_train_only_h{h}',inter,y[mask].mean(),1e-10)
    check(f'train_membership_h{h}',int(mask.sum())==int(tr['n']) and targets[mask].max()==epoch(tr['latest_target']) and t[mask].max()==epoch(tr['latest_origin']) and targets[mask].max()<cutoff)
    zz=(X[mask]-m)/sc
    gram=np.einsum('ni,nj->ij',zz,zz)+1000*np.eye(4)
    rhs=np.einsum('ni,n->i',zz,y[mask]-inter)
    residual=gram@b-rhs
    rel=float(np.linalg.norm(residual,np.inf)/max(1,np.linalg.norm(rhs,np.inf)))
    check(f'ridge_normal_equation_no_refit_h{h}',rel<1e-10,relative_residual=rel)
    prediction[h]=np.einsum('ni,i->n',(X-m)/sc,b)+inter
    train_audit.append(dict(horizon=h,n=int(mask.sum()),first_target=datetime.fromtimestamp(targets[mask].min(),timezone.utc).isoformat(),last_target=tr['latest_target'],normal_equation_relative_residual=rel))

old=rows(BASE/'predictions.csv');new=rows(EXP/'predictions.csv')
check('row_count',len(old)==len(new)==23538)
keys=['origin','target_time','nominal_lead_h','anchor_at','actual_m']
check('identical_keys_targets_anchors',[tuple(r[k] for k in keys) for r in old]==[tuple(r[k] for k in keys) for r in new])
check('unique_origin_horizon',len({(r['origin'],r['nominal_lead_h']) for r in new})==len(new))
rating=json.loads((DATA/'conferencia-balanco.json').read_text())['rating_parameters']
def stage(q): return rating[0]*(q/1000)**rating[1]+rating[2]
results={};detail=[];statuses={};mask_anomalies=0;target_missing_with_prediction=Counter()
for family in ('reference','julho_levels'):
    expected=[];actual=[];correction_expect=[];correction_actual=[];old_calc=[];old_levels=[];anchors=[];old_anchors=[];counts=Counter();matches=True;flags=True;timestamps=True;reasons=True;unchanged_fallback=True
    for a,b in zip(old,new):
        origin=epoch(a['origin']);i=int(np.searchsorted(t,origin));h=int(a['nominal_lead_h'])
        timestamps &= t[i]==origin and epoch(b['target_time'])==origin+h*3600 and epoch(b['anchor_at'])==origin-900 and epoch(b['latest_finalized_feature_at'])==origin-3600
        correction=prediction[h][i];apply=np.isfinite(X[i]).all() and np.isfinite(correction)
        flags &= (b['residual_model_applied']=='True')==apply
        reasons &= b['fallback_reason']==('' if apply else 'missing_residual_feature')
        anchors.append(s['anchor_residual'][i]);old_anchors.append(num(a['anchor_residual_q_m3_s']))
        qbase=num(a[family+'_uncorrected_q_m3_s']);base=num(a[family+'_m']);offset=s['anchor_h'][i]-stage(s['anchor_q'][i])
        oq=qbase+s['anchor_residual'][i]*np.exp(-(h+.25)/6)
        old_calc.append(stage(oq)+offset if np.isfinite(oq) and oq>=0 else np.nan);old_levels.append(base)
        correction_expect.append(correction if apply else np.nan);correction_actual.append(num(b['correction_q_m3_s']))
        if not np.isfinite(base): value=np.nan;status='baseline_missing'
        elif not apply: value=base;status='fallback_original_tau6'
        else:
            q=qbase+correction
            if not np.isfinite(q) or q<0: value=np.nan;status='invalid_candidate_flow'
            else: value=stage(q)+offset;status='candidate_applied'
        counts[status]+=1;matches &= status==b[family+'_status']
        expected.append(value);actual.append(num(b[family+'_candidate_m']))
        if status=='fallback_original_tau6':unchanged_fallback &= num(b[family+'_candidate_m'])==base
        if a['actual_m']=='' and np.isfinite(value):target_missing_with_prediction[family]+=1
        if family=='reference' and apply and status=='baseline_missing':mask_anomalies+=1
        if status=='invalid_candidate_flow':detail.append(dict(family=family,origin=a['origin'],horizon=h,uncorrected_q=qbase,correction=float(correction),corrected_q=float(qbase+correction)))
    eq(f'anchor_reproduction:{family}',anchors,old_anchors,1e-8)
    eq(f'baseline_level_components:{family}',old_calc,old_levels,1e-10)
    eq(f'preserved_baseline:{family}',[num(r[family+'_baseline_m']) for r in new],old_levels)
    eq(f'correction_inference:{family}',correction_expect,correction_actual,1e-8)
    eq(f'candidate_recombination:{family}',expected,actual,1e-10)
    check(f'candidate_status:{family}',matches)
    check(f'apply_flag:{family}',flags);check(f'feature_target_anchor_times:{family}',timestamps);check(f'fallback_reason:{family}',reasons);check(f'fallback_exact:{family}',unchanged_fallback)
    check(f'invalid_flow_summary:{family}',counts['invalid_candidate_flow']==meta['invalid_candidate_flow'][family])
    statuses[family]=dict(counts)
check('apply_summary',sum(r['residual_model_applied']=='True' for r in new)==meta['applied_rows'])
check('fallback_summary',sum(r['residual_model_applied']=='False' for r in new)==meta['fallback_rows'])
check('no_promotion',all(meta[k] is False for k in ['promoted','live_issuance','goal_achieved']))
dump('training-verification.json',train_audit)
dump('negative-candidate-flows.json',detail)
dump('verification.json',dict(passed=all(c['passed'] for c in checks),checks=checks,source_experiment=str(EXP),rows=len(new),status_counts=statuses,model_computable_but_baseline_missing_rows=mask_anomalies,target_missing_but_prediction_retained=dict(target_missing_with_prediction),limitations=[
  'No HGE rerun or refitting. local_q and anchor forecast-rain simulation checked by source review and preserved-baseline agreement; parent owns prefix-state verification.',
  'Training residuals are in-sample to frozen pre-July components, not out-of-fold forecasts.',
  'Finalized labels use subsequently known upstream/rain; correction is not full origin-issued forecast error.',
  'Finalized rainfall includes archived-forecast fill of missing spatial coverage. Upstream grid may contain asof values; Carreiro may use frozen proxy.',
  'Publication availability, legacy timezone and vertical reference remain unverified assumptions.',
  'residual_model_applied denotes a computable correction, not necessarily an applied family forecast; inspect family status.',
  'Already inspected development; no promotion or 98 percent claim.'
]))
dump('artifact-hashes.json',[dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'])
print(json.dumps(dict(passed=all(c['passed'] for c in checks),checks=len(checks),failed=[c for c in checks if not c['passed']],statuses=statuses,model_computable_but_baseline_missing_rows=mask_anomalies,target_missing_but_prediction_retained=dict(target_missing_with_prediction)),ensure_ascii=False))
