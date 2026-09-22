"""Paired sensitivity to audited Monte Claro zeros; never mutates live inputs.

The flagged dates are known retrospectively. This measures sensitivity, not an
independent gain, and does not drop difficult targets from the denominator.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

from hydro_hourly_forecast import BASE, ROOT, dump, epoch, iso, ridge_fit
from hydro_hourly_models import upstream_features
from hydro_routing_fit import shift
from hydro_upstream_audit import metrics, predict_many, savecsv
from hydro_upstream_tree_experiment import partitions, same_time_observation


def masked_inputs(z, policy, variant):
    result={key:value.copy() for key,value in z.items()}
    selected={'original':[], 'Q_missing':['monte:Q'], 'QI_missing':['monte:Q','monte:I']}[variant]
    for window in policy['windows']:
        if window['key'] not in selected:
            continue
        mask=(z['times']>=epoch(window['start']))&(z['times']<epoch(window['end_exclusive']))
        if mask.sum()!=window['expected_slots'] or not np.all(z[window['key']][mask]==window['expected_value']):
            raise ValueError('Audited input mismatch; policy cannot be applied to this snapshot')
        result[window['key']][mask]=np.nan
    return result


def run(source,out,policy_path):
    policy=json.loads(policy_path.read_text())
    frozen=BASE/'telemetria-latencia.npz'
    if hashlib.sha256(frozen.read_bytes()).hexdigest()!=policy['frozen_input_sha256']:
        raise ValueError('Policy requires its exact audited input snapshot')
    out.mkdir(parents=True,exist_ok=False)
    (out/'policy.json').write_bytes(policy_path.read_bytes())
    d=dict(np.load(BASE/'dados-roteamento.npz'));z=dict(np.load(frozen));t=d['times']
    nd=dict(np.load(source/'dados-roteamento.npz'));nz=dict(np.load(source/'telemetria-latencia.npz'))
    features={v:upstream_features(masked_inputs(z,policy,v),t) for v in policy['variants']}
    current=upstream_features(nz,nd['times'])[-1:]
    ref=features['original']
    changed={v:np.any(~((f==ref)|(np.isnan(f)&np.isnan(ref))),axis=1) for v,f in features.items()}
    affected=[]
    for variant,mask in changed.items():
        for i in np.where(mask)[0]:affected.append({'variant':variant,'origin':iso(t[i]),'changed_features':int(np.sum(~((features[variant][i]==ref[i])|(np.isnan(features[variant][i])&np.isnan(ref[i])))))})
    savecsv(out/'affected-origins.csv',affected)
    evaluations=[];live=[];paired=[];models={}
    for station,key in [('julho','julho:Q'),('carreiro','86500000:Q')]:
        known=z[key][np.searchsorted(z['times'],t)]/1000
        latest=float(nz[key][-1]/1000)
        prior=d[station][t<epoch('2025-10-01T00:00:00-03:00')]
        threshold=float(np.nanquantile(prior,.95))
        for lead in range(12):
            target=shift(d[station],-lead);delta=target-known
            idx=partitions(t,target,known,lead);weight=1+2*(target>2)
            for variant,F in features.items():
                for phase,train,apply in [('validation',idx['train'],idx['validation']),('test',idx['pretest'],idx['test']),('current',idx['final'],None)]:
                    model=ridge_fit(F,delta,train,1000.,weight)
                    if phase=='current':
                        inferred=max(0.,latest+float(predict_many(model,current)[0]))
                        observed=same_time_observation(source,nz,key,nd['times'][-1])
                        p=observed if lead==0 and np.isfinite(observed) else inferred
                        live.append({'source':station,'lead_h':lead,'variant':variant,'forecast_m3_s':p*1000,'unanchored_m3_s':inferred*1000})
                        models[f'{station}:{lead}:{variant}']={k:v.tolist() if isinstance(v,np.ndarray) else float(v) for k,v in model.items()}
                        continue
                    pred=np.maximum(0.,known[apply]+predict_many(model,F[apply]))
                    for subset,values in metrics(pred,target[apply],target[apply]>=threshold).items():
                        evaluations.append({'source':station,'lead_h':lead,'variant':variant,'phase':phase,'subset':subset,**values})
                    if phase=='test':
                        for i,p in zip(apply,pred):
                            paired.append({'source':station,'lead_h':lead,'variant':variant,'origin':iso(t[i]),'target_time':iso(t[i]+lead*3600),'actual_m3_s':float(target[i]*1000),'forecast_m3_s':float(p*1000),'input_affected':bool(changed['QI_missing'][i]),'high_flow':bool(target[i]>=threshold)})
            print(station,lead,'done',flush=True)
    for name,rows in [('evaluation',evaluations),('current',live),('test-predictions',paired)]:savecsv(out/f'{name}.csv',rows)
    dump(out/'frozen-ridge-models.json',models)
    code=[Path(__file__),ROOT/'scripts/hydro_upstream_tree_experiment.py',ROOT/'scripts/hydro_upstream_audit.py',ROOT/'scripts/hydro_hourly_models.py',ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_routing_fit.py']
    (out/'code').mkdir()
    for path in code:(out/'code'/path.name).write_bytes(path.read_bytes())
    paths=[frozen,BASE/'dados-roteamento.npz',source/'telemetria-latencia.npz',source/'dados-roteamento.npz',source/'idades-fontes.csv',policy_path,*code]
    dump(out/'experiment.json',{'inputs_sha256':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'policy':policy,'affected_hourly_origins':{k:int(v.sum()) for k,v in changed.items()},'target_membership':'identical across variants, including all affected origins','test_status':'Inspected historical development period; retrospective QC sensitivity, not prospective validation.','current_status':'Frozen historical latency reference; not the active hourly refit.','promoted':False,'live_issuance':False,'goal_achieved':False})
    print(json.dumps({'output':str(out),'affected_origins':{k:int(v.sum()) for k,v in changed.items()}}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--policy',type=Path,default=ROOT/'docs/monte-claro-input-qc-experiment.json')
    args=parser.parse_args()
    with threadpool_limits(limits=2):run(args.source,args.output,args.policy)
