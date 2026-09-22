"""Bounded-coefficient ridge sensitivity, not a physical routing model."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import cholesky,solve_triangular
from scipy.optimize import lsq_linear
from threadpoolctl import threadpool_limits
from hydro_hourly_forecast import BASE,ROOT,epoch,iso,dump,ridge_fit
from hydro_hourly_models import upstream_features
from hydro_routing_fit import shift
from hydro_upstream_audit import predict_many,metrics,savecsv
from hydro_upstream_tree_experiment import partitions,same_time_observation


def level_features(z,times):
    original=upstream_features(z,times);columns=[]
    for j in range(7):
        current=original[:,j*4]
        columns.extend([current,shift(current,1),shift(current,3),shift(current,6)])
    return np.column_stack([*columns,original[:,28:]])


def positive_ridge_fit(X,y,train,alpha,weights):
    state=ridge_fit(X,y,train,alpha,weights)
    filled=np.column_stack([np.where(np.isfinite(X[train]),X[train],state['median']),~np.isfinite(X[train])])
    x=(filled-state['mean'])/state['scale'];w=weights[train]/weights[train].mean()
    H=np.einsum('ni,n,nj->ij',x,w,x)+alpha*np.eye(x.shape[1])
    g=np.einsum('ni,n,n->i',x,w,y[train]-state['intercept'])
    # Explicitly isolate the selected triangle before transposing or multiplying.
    # Unused factor storage must never enter the least-squares design matrix.
    lower=np.tril(cholesky(H,lower=True))
    if not np.allclose(lower@lower.T,H,rtol=1e-10,atol=1e-8):
        raise ValueError('Cholesky factor does not reconstruct ridge objective')
    # ||L.T beta - solve(L,g)||² has the same variable objective as
    # beta.T H beta -2 g.T beta, avoiding repeated tall-matrix decompositions.
    b=solve_triangular(lower,g,lower=True)
    bounds=np.r_[np.zeros(X.shape[1]),np.full(X.shape[1],-np.inf)]
    solution=lsq_linear(lower.T,b,bounds=(bounds,np.inf),method='bvls',tol=1e-10,max_iter=10000)
    gradient=H@solution.x-g
    violation=np.abs(gradient)
    pinned=np.r_[solution.x[:X.shape[1]]<=1e-9,np.zeros(X.shape[1],dtype=bool)]
    violation[pinned]=np.maximum(-gradient[pinned],0)
    kkt_relative=float(violation.max()/max(1.,np.abs(g).max()))
    if not solution.success or np.min(solution.x[:X.shape[1]]) < -1e-9 or kkt_relative>1e-7:
        raise ValueError('Nonnegative ridge solver did not converge')
    state['beta']=solution.x
    return state,{'iterations':solution.nit,'optimality':float(solution.optimality),'kkt_relative':kkt_relative,'success':bool(solution.success),'minimum_numeric_coefficient':float(np.min(solution.x[:X.shape[1]]))}


def run(out):
    policy_path=ROOT/'docs/nonnegative-upstream-protocol.json';policy=json.loads(policy_path.read_text())
    source=ROOT/policy['source_snapshot']
    d=dict(np.load(BASE/'dados-roteamento.npz'));z=dict(np.load(BASE/'telemetria-latencia.npz'));t=d['times']
    nd=dict(np.load(source/'dados-roteamento.npz'));nz=dict(np.load(source/'telemetria-latencia.npz'))
    F=upstream_features(z,t);L=level_features(z,t);NF=upstream_features(nz,nd['times'])[-1:];NL=level_features(nz,nd['times'])[-1:]
    known=z['julho:Q'][np.searchsorted(z['times'],t)]/1000;latest=nz['julho:Q'][-1]/1000
    high=float(np.nanquantile(d['julho'][t<epoch('2025-10-01T00:00:00-03:00')],.95))
    out.mkdir(parents=True,exist_ok=False);(out/'protocol.json').write_bytes(policy_path.read_bytes())
    evaluation=[];current=[];predictions=[];diagnostics=[];models={}
    for lead in range(12):
        target=shift(d['julho'],-lead);delta=target-known;indexes=partitions(t,target,known,lead);w=1+2*(target>2)
        for family in policy['families']:
            X=F if family=='reference_delta_full' else L;y=delta if family=='reference_delta_full' else target
            for phase,train,apply in [('validation',indexes['train'],indexes['validation']),('test',indexes['pretest'],indexes['test']),('current',indexes['final'],None)]:
                if family=='level_ridge_nonnegative':
                    model,diag=positive_ridge_fit(X,y,train,1000.,w);diagnostics.append({'lead_h':lead,'phase':phase,**diag})
                else:model=ridge_fit(X,y,train,1000.,w)
                features=(NF if family=='reference_delta_full' else NL) if apply is None else X[apply]
                pred=predict_many(model,features)
                if family=='reference_delta_full':pred+=latest if apply is None else known[apply]
                pred=np.maximum(pred,0)
                if phase=='current':
                    observed=same_time_observation(source,nz,'julho:Q',nd['times'][-1])
                    if lead==0 and np.isfinite(observed):pred[0]=observed
                    current.append({'lead_h':lead,'family':family,'forecast_m3_s':float(pred[0]*1000)})
                    models[f'{family}:{lead}']={k:v.tolist() if isinstance(v,np.ndarray) else float(v) for k,v in model.items()}
                else:
                    for subset,m in metrics(pred,target[apply],target[apply]>=high).items():evaluation.append({'lead_h':lead,'family':family,'phase':phase,'subset':subset,**m})
                    for i,p in zip(apply,pred):predictions.append({'lead_h':lead,'family':family,'phase':phase,'origin':iso(t[i]),'target_time':iso(t[i]+lead*3600),'actual_m3_s':float(target[i]*1000),'forecast_m3_s':float(p*1000),'high_flow':bool(target[i]>=high)})
        print(lead,'complete',flush=True)
    for name,r in [('evaluation',evaluation),('current',current),('predictions',predictions),('solver-diagnostics',diagnostics)]:savecsv(out/f'{name}.csv',r)
    dump(out/'frozen-models.json',models)
    code=[Path(__file__),*[ROOT/'scripts'/name for name in ['hydro_hourly_forecast.py','hydro_hourly_models.py','hydro_routing_fit.py','hydro_upstream_audit.py','hydro_upstream_tree_experiment.py']]]
    (out/'code').mkdir()
    for p in code:(out/'code'/p.name).write_bytes(p.read_bytes())
    inputs=[policy_path,BASE/'dados-roteamento.npz',BASE/'telemetria-latencia.npz',source/'dados-roteamento.npz',source/'telemetria-latencia.npz',source/'idades-fontes.csv',*code]
    dump(out/'experiment.json',{'source_sha256':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'high_flow_threshold_m3_s':high*1000,'solver_successes':sum(d['success'] for d in diagnostics),'promoted':False,'live_issuance':False,'goal_achieved':False,'limitations':['Inspected development periods, not new independent holdout.','Monotonic regression is not water balance or a guarantee of bounded river levels.','Frozen15h historical feature latency, not an exact reproduction of hourly live refits.']})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    with threadpool_limits(limits=2):run(args.output)
