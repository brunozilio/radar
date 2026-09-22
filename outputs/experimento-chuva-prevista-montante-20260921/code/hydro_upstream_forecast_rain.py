"""Frozen-split upstream discharge experiment with archived forecast rain."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from hydro_hourly_forecast import ROOT,BASE,epoch,iso,ridge_fit,dump
from hydro_hourly_models import upstream_features,historical_weather
from hydro_upstream_audit import predict_many,metrics,savecsv
from hydro_upstream_tree_experiment import partitions
from hydro_routing_fit import shift
from hydro_upstream_weather_features import future_rain_features

FLOW=ROOT/'outputs/experimento-niveis-reservatorios-20260921'


def run(out,policy_path):
    policy=json.loads(policy_path.read_text())
    if policy['families']!=['level_and_slopes','levels_forecast_rain'] or policy['windows_h']!=[3,6,9,12]:raise ValueError('Unsupported protocol')
    weatherpaths=[ROOT/'outputs/mucum-propagacao-2026-09-21/raw'/f'chuva-previsao-historica-{m}.json' for m in ['gfs_seamless','ecmwf_ifs025']]+[BASE/'nwp-historical-icon.json']
    code=[Path(__file__),ROOT/'scripts/hydro_upstream_weather_features.py',ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_hourly_models.py',ROOT/'scripts/hydro_upstream_audit.py',ROOT/'scripts/hydro_upstream_tree_experiment.py',ROOT/'scripts/hydro_routing_fit.py']
    paths=[policy_path,BASE/'dados-roteamento.npz',BASE/'telemetria-latencia.npz',FLOW/'additional-features.npz',FLOW/'frozen-models.json',FLOW/'predictions.csv',FLOW/'artifact-hashes.json',*weatherpaths,*code]
    hashes={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    manifest=json.loads(paths[6].read_text())
    for p in paths[3:6]:assert hashes[str(p.resolve())]==next(r['sha256'] for r in manifest if r['file']==p.name)
    out.mkdir(parents=True,exist_ok=False);(out/'protocol.json').write_bytes(policy_path.read_bytes())
    d=dict(np.load(paths[1]));z=dict(np.load(paths[2]));extra=dict(np.load(paths[3]));t=d['times']
    np.testing.assert_array_equal(t,extra['times'])
    F=np.column_stack([upstream_features(z,t),extra['levels_and_slopes']])
    R,counts,names=future_rain_features(historical_weather(),t);X=np.column_stack([F,R])
    assert F.shape[1]==77 and X.shape[1]==97
    np.savez_compressed(out/'forecast-rain-features.npz',times=t,values=R,complete_model_counts=counts)
    dump(out/'rain-features.json',dict(names=names,units='100mm',location_role='Existing five sampled gridpoints, not catchment area averages',complete_model_counts={str(n):int((counts==n).sum()) for n in range(4)}))
    oldmodels=json.loads(paths[4].read_text())
    stored={(r['source'],int(r['lead_h']),r['phase'],r['origin']):float(r['forecast_m3_s']) for r in csv.DictReader(paths[5].open()) if r['family']=='level_and_slopes'}
    evaluations=[];predictions=[];models={};training=[];maxdiff=0.
    for source,key in [('julho','julho:Q'),('carreiro','86500000:Q')]:
        known=z[key][np.searchsorted(z['times'],t)]/1000
        threshold=float(np.nanquantile(d[source][t<epoch('2025-10-01T00:00:00-03:00')],.95))
        for lead in range(12):
            target=shift(d[source],-lead);delta=target-known;idx=partitions(t,target,known,lead)
            for phase,train,apply in [('validation',idx['train'],idx['validation']),('test',idx['pretest'],idx['test'])]:
                cutoff=epoch('2025-10-01T00:00:00-03:00' if phase=='validation' else '2026-07-01T00:00:00-03:00')
                assert np.all(t[train]+lead*3600<cutoff)
                training.append(dict(source=source,lead_h=lead,phase=phase,training_n=len(train),evaluation_n=len(apply),latest_training_target=iso(max(t[train]+lead*3600)),cutoff_exclusive=iso(cutoff),rain_features_missing_training=int((~np.isfinite(R[train])).any(axis=1).sum()),rain_features_missing_evaluation=int((~np.isfinite(R[apply])).any(axis=1).sum())))
                for family in policy['families']:
                    model_key=f'{source}:{lead}:{phase}:{family}'
                    if family=='level_and_slopes':model={k:np.array(v) if isinstance(v,list) else v for k,v in oldmodels[model_key].items()};A=F
                    else:model=ridge_fit(X,delta,train,1000.,1+2*(target>2));A=X
                    pred=np.maximum(known[apply]+predict_many(model,A[apply]),0)
                    models[model_key]={k:v.tolist() if isinstance(v,np.ndarray) else float(v) for k,v in model.items()}
                    if family=='level_and_slopes':
                        expected=np.array([stored[source,lead,phase,iso(t[i])] for i in apply]);diff=float(np.max(abs(pred*1000-expected)));maxdiff=max(maxdiff,diff)
                        if diff>1e-7:raise ValueError('Reference reproduction failed')
                    for subset,result in metrics(pred,target[apply],target[apply]>=threshold).items():evaluations.append(dict(source=source,lead_h=lead,phase=phase,family=family,subset=subset,**result))
                    for i,value in zip(apply,pred):predictions.append(dict(source=source,lead_h=lead,phase=phase,family=family,origin=iso(t[i]),target_time=iso(t[i]+lead*3600),actual_m3_s=float(target[i]*1000),forecast_m3_s=float(value*1000),high_flow=bool(target[i]>=threshold)))
            print(source,lead,'complete',flush=True)
    for name,rows in [('evaluation',evaluations),('predictions',predictions),('training',training)]:savecsv(out/(name+'.csv'),rows)
    dump(out/'frozen-models.json',models)
    (out/'code').mkdir()
    for p in code:(out/'code'/p.name).write_bytes(p.read_bytes())
    for name,expected in hashes.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==expected
    dump(out/'experiment.json',dict(input_sha256=hashes,models_preserved=len(models),models_newly_fitted=48,reference_reproduction_max_difference_m3_s=maxdiff,prediction_rows=len(predictions),historical_availability_verified=False,live_weather_distribution_matches=False,promoted=False,live_issuance=False,goal_achieved=False))
    print(json.dumps({'output':str(out),'reference_difference':maxdiff,'prediction_rows':len(predictions)}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--protocol',default=ROOT/'docs/upstream-forecast-rain-protocol.json',type=Path);a=p.parse_args()
    with threadpool_limits(limits=2):run(a.output,a.protocol)
