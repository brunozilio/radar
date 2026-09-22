"""Development trial of jointly fitted ridge intercept through weighted centering."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import solve
from threadpoolctl import threadpool_limits
from hydro_hourly_forecast import BASE,ROOT,epoch,iso,dump,ridge_fit
from hydro_hourly_models import upstream_features
from hydro_routing_fit import shift
from hydro_upstream_audit import predict_many,metrics,savecsv
from hydro_upstream_tree_experiment import partitions,same_time_observation


def weighted_fit(X,y,train,alpha,weights):
    med=np.array([np.nanmedian(X[train,j]) if np.isfinite(X[train,j]).any() else 0 for j in range(X.shape[1])])
    filled=np.column_stack([np.where(np.isfinite(X[train]),X[train],med),~np.isfinite(X[train])])
    w=weights[train]/weights[train].mean()
    mean=np.average(filled,axis=0,weights=w)
    scale=filled.std(axis=0);scale[scale<1e-8]=1
    x=(filled-mean)/scale;ym=np.average(y[train],weights=w)
    H=np.einsum('ni,n,nj->ij',x,w,x)+alpha*np.eye(x.shape[1]);g=np.einsum('ni,n,n->i',x,w,y[train]-ym)
    beta=solve(H,g,assume_a='pos')
    normal_error=float(np.max(abs(H@beta-g))/max(1.,np.max(abs(g))))
    mean_error=float(np.average(x@beta+ym-y[train],weights=w))
    if normal_error>1e-8 or abs(mean_error)>1e-8:raise ValueError('Joint ridge optimality failed')
    return {'median':med,'mean':mean,'scale':scale,'beta':beta,'intercept':ym}


def run(out):
    policy_path=ROOT/'docs/weighted-centering-protocol.json';policy=json.loads(policy_path.read_text())
    source=ROOT/policy['current_source'];d=dict(np.load(BASE/'dados-roteamento.npz'));z=dict(np.load(BASE/'telemetria-latencia.npz'));t=d['times']
    nd=dict(np.load(source/'dados-roteamento.npz'));nz=dict(np.load(source/'telemetria-latencia.npz'))
    F=upstream_features(z,t);NF=upstream_features(nz,nd['times'])[-1:]
    out.mkdir(parents=True,exist_ok=False);(out/'protocol.json').write_bytes(policy_path.read_bytes())
    evaluation=[];current=[];predictions=[];training=[];models={}
    for station,key in [('julho','julho:Q'),('carreiro','86500000:Q')]:
        known=z[key][np.searchsorted(z['times'],t)]/1000;latest=nz[key][-1]/1000
        high=float(np.nanquantile(d[station][t<epoch('2025-10-01T00:00:00-03:00')],.95))
        for lead in range(12):
            target=shift(d[station],-lead);delta=target-known;idx=partitions(t,target,known,lead);w=1+2*(target>2)
            for family in policy['families']:
                is_delta=family.endswith('_delta');y=delta if is_delta else target
                fitter=weighted_fit if family.startswith('weighted_') else ridge_fit
                for phase,tr,apply in [('validation',idx['train'],idx['validation']),('test',idx['pretest'],idx['test']),('current',idx['final'],None)]:
                    model=fitter(F,y,tr,1000.,w)
                    residual=predict_many(model,F[tr])-y[tr]
                    training.append({'source':station,'lead_h':lead,'family':family,'phase':phase,'training_n':len(tr),'weighted_mean_residual_m3_s_before_clipping':float(np.average(residual,weights=w[tr])*1000)})
                    pred=predict_many(model,NF if apply is None else F[apply])
                    if is_delta:pred+=latest if apply is None else known[apply]
                    pred=np.maximum(pred,0)
                    if phase=='current':
                        observed=same_time_observation(source,nz,key,nd['times'][-1])
                        if lead==0 and np.isfinite(observed):pred[0]=observed
                        current.append({'source':station,'lead_h':lead,'family':family,'forecast_m3_s':float(pred[0]*1000)})
                        models[f'{station}:{family}:{lead}']={k:v.tolist() if isinstance(v,np.ndarray) else float(v) for k,v in model.items()}
                    else:
                        for subset,v in metrics(pred,target[apply],target[apply]>=high).items():evaluation.append({'source':station,'lead_h':lead,'family':family,'phase':phase,'subset':subset,**v})
                        for i,p in zip(apply,pred):predictions.append({'source':station,'lead_h':lead,'family':family,'phase':phase,'origin':iso(t[i]),'target_time':iso(t[i]+lead*3600),'actual_m3_s':float(target[i]*1000),'forecast_m3_s':float(p*1000),'high_flow':bool(target[i]>=high)})
            print(station,lead,'complete',flush=True)
    for name,r in [('evaluation',evaluation),('current',current),('predictions',predictions),('training-residuals',training)]:savecsv(out/f'{name}.csv',r)
    dump(out/'frozen-models.json',models)
    code=[Path(__file__),*[ROOT/'scripts'/name for name in ['hydro_hourly_forecast.py','hydro_hourly_models.py','hydro_routing_fit.py','hydro_upstream_audit.py','hydro_upstream_tree_experiment.py']]]
    (out/'code').mkdir()
    for p in code:(out/'code'/p.name).write_bytes(p.read_bytes())
    paths=[policy_path,BASE/'dados-roteamento.npz',BASE/'telemetria-latencia.npz',source/'dados-roteamento.npz',source/'telemetria-latencia.npz',source/'idades-fontes.csv',*code]
    dump(out/'experiment.json',{'source_sha256':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'status':'Completed development experiment; previously inspected periods are not independent holdouts','promoted':False,'live_issuance':False,'goal_achieved':False})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    with threadpool_limits(limits=2):run(a.output)
