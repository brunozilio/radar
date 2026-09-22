import ast,csv,json,sys
from pathlib import Path
import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
from hydro_hourly_forecast import BASE,epoch,iso,archive_path,weather_values
from hydro_latency_forecast import telemetry_features
from hydro_routing_fit import shift
z=dict(np.load(BASE/'telemetria-latencia.npz'));t=z.pop('times')
times,X,H,truth,phase,_=telemetry_features(t,{k[4:]:v for k,v in z.items() if k.startswith('raw:')},{k:v for k,v in z.items() if not k.startswith('raw:')})
cols=[]
for name in ('gfs_seamless','ecmwf_ifs025','icon_global'):
    for loc in range(5):
        for window in (3,6,9,12):
            future=times[:,None]+np.arange(1,window+1)*3600
            cols.append(weather_values(archive_path(name),loc,future.ravel(),'precipitation_previous_day1').reshape(future.shape).sum(axis=1))
F=np.column_stack([X,np.column_stack(cols)])
target=shift(truth,-4)[phase];delta=target-H
valid=np.isfinite(H)&np.isfinite(target)&np.isfinite(X[:,:24]).all(axis=1)
start=epoch('2025-10-01T00:00:00-03:00');end=epoch('2026-07-01T00:00:00-03:00');stop=epoch('2026-09-21T00:00:00-03:00')
train=np.r_[np.where(valid&(times+3600<start))[0],np.where(valid&(times>=start)&(times+3600<end))[0]]
test=np.where(valid&(times>=end)&(times+3600<stop))[0]
old={r['origin']:float(r['forecast_m']) for r in csv.DictReader((BASE/'retrospectivas-latencia.csv').open()) if r['model']=='arvores_previsao_chuva' and r['phase']=='test' and r['lead_h']=='1.0'}
expected=np.array([old[iso(times[i])] for i in test])
leaf,loss=ast.literal_eval(next(csv.DictReader((BASE/'previsao-atualizada.csv').open()))['parameters'])
results=[];predictions=[]
for threads in (1,2,4):
    with threadpool_limits(limits=threads):
        model=HistGradientBoostingRegressor(max_iter=180,max_leaf_nodes=leaf,min_samples_leaf=35,learning_rate=.055,l2_regularization=10,loss=loss,early_stopping=False,random_state=57)
        model.fit(F[train],delta[train],sample_weight=(1+2*(abs(delta)>=1)+2*(target>=9))[train])
        p=model.predict(F[test])+H[test]
    predictions.append(p)
    results.append(dict(threads=threads,first_error_m=float(p[0]-expected[0]),max_abs_difference_m=float(max(abs(p-expected))),mae_difference_m=float(abs(p-expected).mean())))
result=dict(numpy=np.__version__,sklearn=sklearn.__version__,train_n=len(train),test_n=len(test),runs=results,
            maximum_between_thread_predictions_m=max(float(max(abs(p-predictions[0]))) for p in predictions))
out=Path(__file__).parent
np.savez_compressed(out/'thread-predictions.npz',expected=expected,predictions=np.array(predictions),times=times[test])
(out/'thread-check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
