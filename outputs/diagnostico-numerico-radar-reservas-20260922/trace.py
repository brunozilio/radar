"""Read-only tree-path explanation of the independently observed largest replay difference."""
from pathlib import Path
from datetime import datetime
import csv,json,hashlib
import joblib,numpy as np
from threadpoolctl import threadpool_limits
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
M=ROOT/'outputs/radar-matrizes-reservadas-2021-2022-20260922/2022/features.npz'
V=ROOT/'outputs/verificacao-radar-matrizes-reservadas-2021-2022-20260922'
F=ROOT/'outputs/congelamento-radar-reserva-2021-2022-20260922/models/candidate120_plus2020-4.joblib'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,value):(P/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def walk(nodes,x):
    current=0;path=[]
    while not nodes[current]['is_leaf']:
        n=nodes[current];assert not n['is_categorical']
        j=int(n['feature_idx']);v=x[j];threshold=float(n['num_threshold'])
        left=bool(n['missing_go_to_left']) if np.isnan(v) else bool(v<=threshold)
        path.append(dict(node=int(current),feature=j,threshold=threshold,value=float(v) if np.isfinite(v) else None,left=left))
        current=int(n['left'] if left else n['right'])
    return float(nodes[current]['value']),current,path

with threadpool_limits(limits=2):
    d=np.load(M);r=np.load(V/'reconstructed-2022.npz');assert np.array_equal(d['times'],r['times'])
    origin='2022-05-29T23:00:00-03:00';t=datetime.fromisoformat(origin).timestamp();ix=np.where(d['times']==t)[0];assert len(ix)==1;i=int(ix[0])
    names={int(v['column']):v['name'] for v in csv.DictReader((V/'feature-catalog.csv').open()) if v['year']=='2022'}
    a=d['features'][i];b=r['features'][i];model=joblib.load(F);base=float(d['base'][i]);totals=[float(model._baseline_prediction.ravel()[0])]*2;changed=[]
    for k,trees in enumerate(model._predictors):
        assert len(trees)==1
        nodes=trees[0].nodes;va,la,pa=walk(nodes,a);vb,lb,pb=walk(nodes,b);totals[0]+=va;totals[1]+=vb
        if la!=lb:
            divergence=None
            for x,y in zip(pa,pb):
                assert x['node']==y['node']
                if x['left']!=y['left']:
                    divergence=dict(node=x['node'],feature=x['feature'],feature_name=names[x['feature']],threshold=x['threshold'],
                        original_value=x['value'],reconstructed_value=y['value'],original_left=x['left'],reconstructed_left=y['left']);break
            assert divergence is not None
            changed.append(dict(tree=k,original_leaf=la,reconstructed_leaf=lb,original_leaf_value=va,reconstructed_leaf_value=vb,contribution_change=vb-va,first_divergence=divergence))
    pred=[float(model.predict(x.reshape(1,-1))[0])+base for x in (a,b)]
    np.testing.assert_allclose(np.array(totals)+base,pred,rtol=0,atol=1e-12)
    target=next(v for v in csv.DictReader((ROOT/'outputs/experimento-radar-reservas-2021-2022-20260922/predictions.csv').open()) if v['origin']==origin and v['nominal_lead_h']=='4')
    assert float(target['candidate120_plus2020_m'])==pred[0]
    result=dict(scope='Post-evaluation numerical diagnostic only; no data/model/score changes.',origin=origin,year=2022,family='candidate120_plus2020',horizon_h=4,
        base_m=base,actual_m=float(target['actual_m']),original_forecast_m=pred[0],reconstructed_forecast_m=pred[1],difference_m=pred[1]-pred[0],
        trees=len(model._predictors),trees_with_different_leaf=len(changed),changed_trees=changed,
        input_sha256={str(p.relative_to(ROOT)):sha(p) for p in (M,V/'reconstructed-2022.npz',V/'feature-catalog.csv',F)},
        inference_role='Audit replay, not a new candidate or forecast issue.',model_modified=False,inputs_modified=False)
    dump('trace.json',result)
    dump('artifact-hashes.json',[dict(file=p.name,sha256=sha(p)) for p in sorted(P.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'])
    print(json.dumps(result,indent=2))
