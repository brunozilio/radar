"""Chronological development trial for nonlinear upstream-flow predictors.

No model promotion or live issuance. Evaluate against the same fixed latency
features, and never treat inspected historical periods as a fresh holdout.
"""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from hydro_hourly_models import upstream_features
from hydro_hourly_forecast import BASE,ROOT,epoch,dump,ridge_fit,ridge_predict
from hydro_routing_fit import shift
from hydro_upstream_audit import metrics,predict_many,savecsv

def partitions(times,target,known,lead):
    good=np.isfinite(target)&np.isfinite(known);a=epoch('2025-10-01T00:00:00-03:00');b=epoch('2026-07-01T00:00:00-03:00');c=epoch('2026-09-21T00:00:00-03:00')
    result={'train':np.where(good&(times+lead*3600<a))[0],'validation':np.where(good&(times>=a)&(times+lead*3600<b))[0],'pretest':np.where(good&(times+lead*3600<b))[0],'test':np.where(good&(times>=b)&(times+lead*3600<c))[0],'final':np.where(good&(times+lead*3600<c))[0]}
    for key,boundary in [('train',a),('pretest',b),('final',c)]:
        if np.any(times[result[key]]+lead*3600>=boundary):raise ValueError('Training target crosses cutoff')
    return result

def run(source,out):
    out.mkdir(parents=True,exist_ok=False)
    d=dict(np.load(BASE/'dados-roteamento.npz'));z=dict(np.load(BASE/'telemetria-latencia.npz'))
    nd=dict(np.load(source/'dados-roteamento.npz'));nz=dict(np.load(source/'telemetria-latencia.npz'))
    t=d['times'];F=upstream_features(z,t);currentF=upstream_features(nz,nd['times'])[-1:]
    evals=[];live=[];validation=[];rows=[]
    params=dict(max_iter=180,max_leaf_nodes=7,min_samples_leaf=35,learning_rate=.055,l2_regularization=10,loss='absolute_error',early_stopping=False,random_state=57)
    for source_id,key in [('julho','julho:Q'),('carreiro','86500000:Q')]:
        known=z[key][np.searchsorted(z['times'],t)]/1000;current_known=float(nz[key][-1]/1000)
        prior=d[source_id][t<epoch('2025-10-01T00:00:00-03:00')];threshold=float(np.quantile(prior[np.isfinite(prior)],.95))
        for lead in range(12):
            target=shift(d[source_id],-lead);delta=target-known;idx=partitions(t,target,known,lead);weights=1+2*(target>2)
            for family in ['ridge_reference','tree_delta','tree_level']:
                latest=None
                for phase,train,apply in [('validation',idx['train'],idx['validation']),('test',idx['pretest'],idx['test']),('current',idx['final'],None)]:
                    X=currentF if apply is None else F[apply];base=current_known if apply is None else known[apply]
                    if family=='ridge_reference':
                        model=ridge_fit(F,delta,train,1000.,weights);pred=predict_many(model,X)+base
                    else:
                        model=HistGradientBoostingRegressor(**params);response=delta if family=='tree_delta' else target
                        model.fit(F[train],response[train],sample_weight=weights[train]);pred=model.predict(X)+(base if family=='tree_delta' else 0)
                    pred=np.maximum(pred,0)
                    if phase=='current':
                        # A same-time value already received is an observation,
                        # not an opportunity to replace it by model inference.
                        observed=float(nz['raw:'+key][-1]/1000)
                        original=float(pred[0])
                        if lead==0 and np.isfinite(observed):pred[0]=observed
                        live.append({'source':source_id,'lead_h':lead,'family':family,'forecast_m3_s':float(pred[0]*1000),'unanchored_model_m3_s':original*1000,'current_observation_used':bool(lead==0 and np.isfinite(observed))})
                    else:
                        m=metrics(pred,target[apply],target[apply]>=threshold)
                        for subset,values in m.items():evals.append({'source':source_id,'lead_h':lead,'family':family,'phase':phase,'subset':subset,**values})
                        if phase=='validation':validation.append({'source':source_id,'lead_h':lead,'family':family,'score':m['all']['mae_m3_s']+.5*m['high_flow']['mae_m3_s']})
                        if phase=='test':
                            for i,value in zip(apply,pred):rows.append({'source':source_id,'lead_h':lead,'family':family,'origin_epoch':int(t[i]),'target_epoch':int(t[i]+lead*3600),'actual_m3_s':float(target[i]*1000),'forecast_m3_s':float(value*1000),'high_flow':bool(target[i]>=threshold)})
            print(source_id,lead,'done',flush=True)
    selection={}
    for source_id in ['julho','carreiro']:
        scores={f:float(np.mean([r['score'] for r in validation if r['source']==source_id and r['family']==f])) for f in ['ridge_reference','tree_delta','tree_level']}
        selection[source_id]={'family':min(scores,key=scores.get),'validation_scores':scores}
    for name,value in [('evaluation',evals),('current',live),('test-predictions',rows),('validation',validation)]:savecsv(out/f'{name}.csv',value)
    code=[Path(__file__),ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_hourly_models.py',ROOT/'scripts/hydro_upstream_audit.py',ROOT/'scripts/hydro_flow_diagnostics.py',ROOT/'scripts/hydro_routing_fit.py']
    (out/'code').mkdir()
    for p in code:(out/'code'/p.name).write_bytes(p.read_bytes())
    inputs=[BASE/'dados-roteamento.npz',BASE/'telemetria-latencia.npz',source/'dados-roteamento.npz',source/'telemetria-latencia.npz',*code]
    dump(out/'experiment.json',{'selection_by_validation_only':selection,'parameters':params,'source_snapshot':str(source),'input_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'alpha_reference':1000.,'comparison':'All methods share the frozen 15h historical latency features; this ridge is not claimed to reproduce the refitted hourly live model.','test_status':'Previously inspected July–September2026 development period; not independent new holdout.','live_issuance':False,'promoted':False,'goal_achieved':False})
    print(json.dumps(selection),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    with threadpool_limits(limits=2):run(args.source,args.output)
