"""Radar-only complete-case versus native-missing training, full-origin audit."""
import ast
import importlib.metadata
import csv
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from hydro_hourly_forecast import ROOT, BASE, epoch, iso, weather_values, archive_path
from hydro_latency_forecast import telemetry_features
from hydro_routing_fit import shift


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p,rows):
    with p.open('w') as s:
        w=csv.DictWriter(s,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def training_masks(times,base,target,complete,horizon,start,end):
    finite=np.isfinite(base)&np.isfinite(target)
    # Preserve the original historical audit's two chronological blocks.
    first=times+horizon*3600<start
    second=(times>=start)&(times+horizon*3600<end)
    return {('validation','baseline'):finite&complete&first,
            ('validation','candidate'):finite&first,
            ('test','baseline'):finite&complete&(first|second),
            ('test','candidate'):finite&(first|second)}


def run():
    protocol=ROOT/'docs/radar-native-missing-runtime19-protocol.json'
    paths=[protocol,BASE/'telemetria-latencia.npz',BASE/'previsao-atualizada.csv',BASE/'retrospectivas-latencia.csv',
           Path(__file__),ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_latency_forecast.py',ROOT/'scripts/hydro_routing_fit.py']
    hashes={str(p.resolve()):sha(p) for p in paths}
    z=dict(np.load(paths[1]));t=z.pop('times')
    raw={k[4:]:v for k,v in z.items() if k.startswith('raw:')}
    delayed={k:v for k,v in z.items() if not k.startswith('raw:')}
    times,X,H,truth,phase,_=telemetry_features(t,raw,delayed)
    assert X.shape[1]==120 and np.all(np.diff(times)==3600)
    cols=[]
    for model in ('gfs_seamless','ecmwf_ifs025','icon_global'):
        p=archive_path(model);paths.append(p);hashes[str(p.resolve())]=sha(p)
        for loc in range(5):
            for window in (3,6,9,12):
                future=times[:,None]+np.arange(1,window+1)*3600
                a=weather_values(p,loc,future.ravel(),'precipitation_previous_day1').reshape(future.shape)
                cols.append(a.sum(axis=1))
    F=np.column_stack([X,np.column_stack(cols)]);assert F.shape[1]==180
    complete=np.isfinite(X[:,:24]).all(axis=1)
    configs=list(csv.DictReader(paths[2].open()))
    old={(r['origin'],int(float(r['lead_h']))):r for r in csv.DictReader(paths[3].open()) if r['model']=='arvores_previsao_chuva' and r['phase']=='test'}
    start=epoch('2025-10-01T00:00:00-03:00');end=epoch('2026-07-01T00:00:00-03:00');stop=epoch('2026-09-21T00:00:00-03:00')
    out=ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921';out.mkdir(exist_ok=False);(out/'models').mkdir()
    predictions=[];training=[];max_reproduction=0.;reproduced=0;runtime_differences=[]
    for h in range(1,13):
        target=shift(truth,-h*4)[phase];delta=target-H
        masks=training_masks(times,H,target,complete,h,start,end)
        leaf,loss=ast.literal_eval(configs[h-1]['parameters'])
        assert configs[h-1]['model']=='arvores_previsao_chuva'
        for split,left,right in [('validation',start,end),('test',end,stop)]:
            scheduled=np.where((times>=left)&(times+h*3600<right))[0]
            apply=scheduled[np.isfinite(H[scheduled])]
            values={}
            for family in ('baseline','candidate'):
                train=np.where(masks[split,family])[0]
                model=HistGradientBoostingRegressor(max_iter=180,max_leaf_nodes=leaf,min_samples_leaf=35,
                    learning_rate=.055,l2_regularization=10,loss=loss,early_stopping=False,random_state=57)
                weights=1+2*(abs(delta)>=1)+2*(target>=9)
                model.fit(F[train],delta[train],sample_weight=weights[train])
                pred=np.full(len(times),np.nan);pred[apply]=model.predict(F[apply])+H[apply]
                assert np.isfinite(pred[apply]).all()
                if split=='test' and family=='baseline':
                    for i in scheduled:
                        key=(iso(times[i]),h)
                        if key in old:
                            r=old[key]
                            assert target[i]==float(r['actual_m']) and H[i]==float(r['base_m'])
                            error=abs(pred[i]-float(r['forecast_m']))
                            max_reproduction=max(max_reproduction,error);reproduced+=1
                            runtime_differences.append(dict(origin=key[0],horizon_h=h,
                                archived_runtime_forecast_m=float(r['forecast_m']),
                                current_runtime_refit_m=float(pred[i]),abs_difference_m=float(error)))
                values[family]=pred
                joblib.dump(model,out/'models'/f'{split}-{family}-{h}.joblib')
                training.append(dict(phase=split,family=family,horizon_h=h,n=len(train),
                                     with_missing_first24=int((~complete[train]).sum()),
                                     latest_training_target=iso((times[train]+h*3600).max()),
                                     cutoff_exclusive=iso(start if split=='validation' else end),leaf_nodes=leaf,loss=loss))
            for i in scheduled:
                predictions.append(dict(phase=split,origin=iso(times[i]),target_time=iso(times[i]+h*3600),nominal_lead_h=h,
                                        original_complete24=bool(complete[i]),base_m=float(H[i]) if np.isfinite(H[i]) else None,
                                        actual_m=float(target[i]) if np.isfinite(target[i]) else None,
                                        baseline_m=float(values['baseline'][i]) if np.isfinite(values['baseline'][i]) else None,
                                        candidate_m=float(values['candidate'][i]) if np.isfinite(values['candidate'][i]) else None))
        print('completed horizon',h,flush=True)
    assert reproduced==len(old)
    metrics=[]
    for split in ('validation','test'):
        for h in range(1,13):
            for subset in ('all','level_ge_7m'):
                for population in ('full_schedule','complete24','missing24'):
                    group=[r for r in predictions if r['phase']==split and r['nominal_lead_h']==h
                           and (population=='full_schedule' or r['original_complete24']==(population=='complete24'))]
                    observed=[r for r in group if r['actual_m'] is not None and (subset=='all' or r['actual_m']>=7)]
                    for family in ('baseline','candidate'):
                        pairs=[r for r in observed if r[family+'_m'] is not None]
                        error=np.array([r[family+'_m']-r['actual_m'] for r in pairs]);ae=abs(error)
                        metrics.append(dict(phase=split,horizon_h=h,subset=subset,population=population,family=family,
                                            scheduled_rows=len(group),observed_targets=len(observed),n=len(ae),failures=len(observed)-len(ae),
                                            hits=int((ae<=.5).sum()),hit_fraction=float((ae<=.5).mean()) if len(ae) else None,
                                            mae_m=float(ae.mean()) if len(ae) else None,bias_m=float(error.mean()) if len(ae) else None,
                                            p98_abs_m=float(np.quantile(ae,.98)) if len(ae) else None,max_abs_m=float(ae.max()) if len(ae) else None))
    predictions.sort(key=lambda r:(r['phase'],r['origin'],r['nominal_lead_h']))
    save(out/'predictions.csv',predictions);save(out/'evaluation.csv',metrics);save(out/'training.csv',training)
    save(out/'runtime-comparison.csv',runtime_differences)
    np.savez_compressed(out/'features.npz',times=times,features=F,base=H,truth=truth[phase],complete24=complete)
    (out/'protocol.json').write_bytes(protocol.read_bytes());(out/'code').mkdir()
    for p in paths:
        if p.suffix=='.py':(out/'code'/p.name).write_bytes(p.read_bytes())
    for name,digest in hashes.items():assert sha(Path(name))==digest
    summary=dict(input_sha256=hashes,rows=len(predictions),models_fitted=48,
                 historical_test_predictions_compared=reproduced,max_runtime_difference_m=max_reproduction,
                 historical_test_predictions_exactly_reproduced=bool(max_reproduction==0),
                 runtime={name:importlib.metadata.version(name) for name in ('numpy','scipy','scikit-learn','joblib','threadpoolctl')},
                 original_test_auxiliary_missing_rows_excluded=True,complete24_filter_retained_in_baseline_training=True,
                 promoted=False,live_issuance=False,goal_achieved=False,
                 limitations=json.loads(protocol.read_text())['limits'])
    (out/'experiment.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'artifact-hashes.json').write_text(json.dumps([dict(file=str(p.relative_to(out)),sha256=sha(p)) for p in sorted(out.rglob('*')) if p.is_file()],indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    with threadpool_limits(limits=2):run()
