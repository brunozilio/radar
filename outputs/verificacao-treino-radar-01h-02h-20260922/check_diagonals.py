"""Additional explicitly authorized bounded frozen-model replay; no fit/issue."""
from pathlib import Path
from datetime import datetime
import csv,json,hashlib
import numpy as np,joblib
from threadpoolctl import threadpool_limits
P=Path(__file__).resolve().parent;R=P.parents[1];F=[R/'outputs/mucum-hourly-20260922T010016-0300',R/'outputs/mucum-hourly-20260922T020011-0300'];D=R/'outputs/diagnostico-radar-pesos-inputs-fixos-20260922';C=R/'outputs/analise-radar-revisao-mesmo-alvo-20260922';inputs={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tr(p):inputs[str(p.relative_to(R))]=sha(p);return p
def js(p):return json.loads(tr(p).read_text())
for folder in (D,C):
 for r in js(folder/'artifact-hashes.json'):assert sha(tr(folder/r['file']))==r['sha256']
features=[dict(np.load(tr(f/'radar-features.npz'))) for f in F];issues=[js(f/'radar_arvores_live_candidate.json') for f in F]
diagonal=list(csv.DictReader(tr(D/'issued-reproduction.csv').open()));assert len(diagonal)==28
saved={(r['origin'],int(r['horizon_h'])):r for r in diagonal};models={};replayed=[]
with threadpool_limits(limits=2):
 for k,folder in enumerate(F):
  tag=('old','new')[k];d=features[k];issue=issues[k];art={Path(r['path']).name:r['sha256'] for r in issue['model_artifacts']}
  for h in range(1,15):
   p=tr(folder/'models'/f'radar-{h}.joblib');assert sha(p)==art[p.name];m=joblib.load(p);models[k,h]=m
   value=float(m.predict(d['features'][-1:])[0]+d['base'][-1]);point=next(r for r in issue['points'] if r['nominal_lead_h']==h)
   assert value==point['level_m']==float(saved[tag,h]['issued_m'])==float(saved[tag,h]['reproduced_m'])
   replayed.append(dict(origin=tag,horizon_h=h,value_m=value,exact=True))
 target='2026-09-22T07:00:00-03:00';old=next(r for r in issues[0]['points'] if r['valid_at']==target);new=next(r for r in issues[1]['points'] if r['valid_at']==target)
 assert old['nominal_lead_h']==6 and new['nominal_lead_h']==5
 intermediate=float(models[0,5].predict(features[1]['features'][-1:])[0]+features[1]['base'][-1]);joint=intermediate-old['level_m'];refit=new['level_m']-intermediate;total=new['level_m']-old['level_m']
 assert abs(joint+refit-total)<1e-14
 r=next(r for r in csv.DictReader(tr(C/'decomposition.csv').open()) if r['valid_at']==target)
 values=dict(old_issued_m=old['level_m'],reused_old_models_at_new_inputs_m=intermediate,new_issued_m=new['level_m'],joint_new_inputs_base_and_horizon_m=joint,retraining_effect_at_new_inputs_m=refit,total_same_target_revision_m=total)
 assert all(values[k]==float(r[k]) for k in values)
result=dict(passed=True,diagonal_replays=28,additional_unissued_replays=1,diagonals=replayed,target=target,old_nominal_lead_h=6,new_nominal_lead_h=5,**values,input_sha256=inputs,limits=['Ordered computational identity, not causal decomposition or accuracy gain.','Old h5 model on new inputs is unissued counterfactual; old issued forecast for same target used h6.','No new fit or live issue; no other periods checked.'])
(P/'diagonal-and-same-target-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS 28 exact diagonals, 1 counterfactual;',json.dumps(values))
