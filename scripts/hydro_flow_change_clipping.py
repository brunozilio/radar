"""Development trial: bound flow-change feature influence using training-only quantiles."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from hydro_hourly_forecast import ROOT,BASE,epoch,iso,ridge_fit,dump
from hydro_hourly_models import upstream_features
from hydro_upstream_audit import predict_many,metrics,savecsv
from hydro_upstream_tree_experiment import partitions
from hydro_routing_fit import shift

FLOW=ROOT/'outputs/experimento-niveis-reservatorios-20260921'
COLUMNS=[4*g+j for g in range(7) for j in (1,2,3)]

def fit_bounds(X,train,columns=COLUMNS,quantiles=(.005,.995)):
    if not len(train):raise ValueError('No training rows')
    bounds=[]
    for j in columns:
        values=X[train,j];values=values[np.isfinite(values)]
        bounds.append(np.quantile(values,quantiles).tolist() if len(values) else [None,None])
    return bounds


def apply_bounds(X,bounds,columns=COLUMNS):
    if len(bounds)!=len(columns):raise ValueError('Bounds length mismatch')
    result=X.copy()
    for j,(lo,hi) in zip(columns,bounds):
        if lo is None and hi is None:continue
        if lo is None or hi is None or not np.isfinite([lo,hi]).all() or lo>hi:raise ValueError('Invalid clipping bounds')
        finite=np.isfinite(result[:,j]);result[finite,j]=np.clip(result[finite,j],lo,hi)
    return result


def run(out,protocol_path):
    policy=json.loads(protocol_path.read_text())
    if policy['flow_change_columns']!=COLUMNS or policy['quantiles']!=[.005,.995]:raise ValueError('Unsupported protocol')
    paths=[protocol_path,BASE/'dados-roteamento.npz',BASE/'telemetria-latencia.npz',FLOW/'additional-features.npz',FLOW/'frozen-models.json',FLOW/'predictions.csv',FLOW/'artifact-hashes.json',Path(__file__),ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_hourly_models.py',ROOT/'scripts/hydro_upstream_audit.py',ROOT/'scripts/hydro_upstream_tree_experiment.py',ROOT/'scripts/hydro_routing_fit.py']
    hashes={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    manifest=json.loads(paths[6].read_text())
    for p in paths[3:6]:assert hashes[str(p.resolve())]==next(r['sha256'] for r in manifest if r['file']==p.name)
    out.mkdir(parents=True,exist_ok=False);(out/'protocol.json').write_bytes(protocol_path.read_bytes())
    d=dict(np.load(paths[1]));z=dict(np.load(paths[2]));extra=dict(np.load(paths[3]));t=d['times']
    np.testing.assert_array_equal(extra['times'],t)
    F=np.column_stack([upstream_features(z,t),extra['levels_and_slopes']])
    oldmodels=json.loads(paths[4].read_text())
    stored={(r['source'],int(r['lead_h']),r['phase'],r['origin']):float(r['forecast_m3_s']) for r in csv.DictReader(paths[5].open()) if r['family']=='level_and_slopes'}
    evaluations=[];predictions=[];models={};transforms=[];maxdiff=0.
    for source,key in [('julho','julho:Q'),('carreiro','86500000:Q')]:
        known=z[key][np.searchsorted(z['times'],t)]/1000
        threshold=float(np.nanquantile(d[source][t<epoch('2025-10-01T00:00:00-03:00')],.95))
        for lead in range(12):
            target=shift(d[source],-lead);delta=target-known;idx=partitions(t,target,known,lead)
            for phase,train,apply in [('validation',idx['train'],idx['validation']),('test',idx['pretest'],idx['test'])]:
                bounds=fit_bounds(F,train);X=apply_bounds(F,bounds)
                changed=np.any(~((F==X)|(np.isnan(F)&np.isnan(X))),axis=1)
                cutoff=epoch('2025-10-01T00:00:00-03:00' if phase=='validation' else '2026-07-01T00:00:00-03:00')
                assert np.all(t[train]+lead*3600<cutoff)
                transforms.append(dict(source=source,lead_h=lead,phase=phase,training_n=len(train),changed_training_n=int(changed[train].sum()),evaluation_n=len(apply),changed_evaluation_n=int(changed[apply].sum()),latest_training_target=iso(max(t[train]+lead*3600)),cutoff_exclusive=iso(cutoff),bounds=bounds))
                for family in policy['families']:
                    model_key=f'{source}:{lead}:{phase}:{family}'
                    if family=='level_and_slopes':
                        model={k:np.array(v) if isinstance(v,list) else v for k,v in oldmodels[model_key].items()};A=F
                    else:model=ridge_fit(X,delta,train,1000.,1+2*(target>2));A=X
                    pred=np.maximum(known[apply]+predict_many(model,A[apply]),0)
                    models[model_key]={k:v.tolist() if isinstance(v,np.ndarray) else float(v) for k,v in model.items()}
                    if family=='level_and_slopes':
                        expected=np.array([stored[source,lead,phase,iso(t[i])] for i in apply]);diff=float(np.max(abs(pred*1000-expected)));maxdiff=max(maxdiff,diff)
                        if diff>1e-7:raise ValueError('Reference reproduction failed')
                    for subset,result in metrics(pred,target[apply],target[apply]>=threshold).items():evaluations.append(dict(source=source,lead_h=lead,phase=phase,family=family,subset=subset,**result))
                    for i,value in zip(apply,pred):predictions.append(dict(source=source,lead_h=lead,phase=phase,family=family,origin=iso(t[i]),target_time=iso(t[i]+lead*3600),actual_m3_s=float(target[i]*1000),forecast_m3_s=float(value*1000),high_flow=bool(target[i]>=threshold),clipped_predictors=bool(changed[i])))
            print(source,lead,'complete',flush=True)
    savecsv(out/'evaluation.csv',evaluations);savecsv(out/'predictions.csv',predictions)
    dump(out/'frozen-models.json',models);dump(out/'transforms.json',transforms)
    (out/'code').mkdir()
    for p in paths:
        if p.suffix=='.py':(out/'code'/p.name).write_bytes(p.read_bytes())
    for name,expected in hashes.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==expected
    dump(out/'experiment.json',dict(input_sha256=hashes,models_preserved=len(models),models_newly_fitted=48,reference_reproduction_max_difference_m3_s=maxdiff,prediction_rows=len(predictions),historical_availability_verified=False,promoted=False,live_issuance=False,goal_achieved=False))
    print(json.dumps({'output':str(out),'reference_difference':maxdiff,'prediction_rows':len(predictions)}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--protocol',default=ROOT/'docs/upstream-flow-change-clipping-protocol.json',type=Path);a=p.parse_args()
    with threadpool_limits(limits=2):run(a.output,a.protocol)
