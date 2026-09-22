"""Fixed rain representation experiment; no tuning, promotion or live issuance."""
import csv,importlib.metadata,json
from datetime import datetime,timezone
from pathlib import Path
import joblib,numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from hydro_hourly_forecast import ROOT,epoch,iso
from hydro_radar_2024_features import sha,verify
from hydro_radar_numeric import normalize_observed_features
from hydro_routing_fit import shift

B=ROOT/'outputs/experimento-radar-observado-120-20260921'
C=ROOT/'outputs/experimento-radar-historico-2020-20260921'
N=ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921'
A=ROOT/'outputs/radar-matriz-observada-2020-20260921'
M=ROOT/'outputs/radar-matrizes-reservadas-2021-2022-20260922'
V=ROOT/'outputs/verificacao-radar-matrizes-reservadas-2021-2022-20260922'
G=ROOT/'outputs/auditoria-normalizacao-radar-20260922'
R=ROOT/'outputs/experimento-radar-reservas-2021-2022-20260922'
OUT=ROOT/'outputs/experimento-radar-estabilidade-numerica-20260922'
PROTOCOL=ROOT/'docs/radar-numeric-stability-protocol.json'
FAMILIES=('raw_original','raw_plus2020','normalized_original','normalized_plus2020')
def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def save(p,rows):
    with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def key(r):return r['phase'],r['origin'],int(r['nominal_lead_h'])
def number(v):return float(v) if np.isfinite(v) else None
def metrics(rows,periods,field):
    result=[]
    for period in periods:
        for h in range(1,13):
            for population in ('full_schedule','complete24','missing24'):
                pop=[r for r in rows if (period=='pooled' or str(r[field])==period) and r['nominal_lead_h']==h and (population=='full_schedule' or r['complete24']==(population=='complete24'))]
                for subset in ('all','level_ge_7m'):
                    observed=[r for r in pop if r['actual_m'] is not None and (subset=='all' or r['actual_m']>=7)]
                    for family in FAMILIES:
                        pairs=[r for r in observed if r[family+'_m'] is not None];e=np.array([r[family+'_m']-r['actual_m'] for r in pairs]);ae=abs(e);hits=int((ae<=.5).sum())
                        result.append(dict(period=period,horizon_h=h,population=population,subset=subset,family=family,scheduled_rows=len(pop),
                            missing_truth=sum(r['actual_m'] is None for r in pop),observed_targets=len(observed),pairs=len(pairs),failures=len(observed)-len(pairs),hits=hits,
                            paired_hit_fraction=hits/len(pairs) if pairs else None,observed_target_hit_fraction=hits/len(observed) if observed else None,
                            mae_m=float(ae.mean()) if pairs else None,bias_m=float(e.mean()) if pairs else None,p98_abs_m=float(np.quantile(ae,.98)) if pairs else None,max_abs_m=float(ae.max()) if pairs else None))
    return result

def run():
    assert not OUT.exists(),'Never overwrite a started experiment.'
    for folder in (B,C,A,M,V,G,R):verify(folder)
    gate=json.loads((G/'verification.json').read_text());assert gate['pre_fit_gate_passed'] is True
    rawdata=dict(np.load(N/'features.npz'));newdata=dict(np.load(A/'features.npz'))
    t,F,base,truth,complete=(rawdata[k] for k in ('times','features','base','truth','complete24'));F=F[:,:120];X=normalize_observed_features(F)
    nt,NF,nb,ny=(newdata[k] for k in ('times','features','base','truth'));NX=normalize_observed_features(NF)
    masks=dict(np.load(C/'training-masks.npz'));meta={(r['phase'],int(r['horizon_h'])):r for r in csv.DictReader((C/'training.csv').open())}
    original=list(csv.DictReader((C/'predictions.csv').open()));lookup={key(r):r for r in original};assert len(lookup)==len(original)==102084
    reserved=[]
    for year,n in ((2021,744),(2022,1464)):
        d=dict(np.load(M/str(year)/'features.npz'));v=dict(np.load(V/f'reconstructed-{year}.npz'))
        xx=normalize_observed_features(d['features']);vv=normalize_observed_features(v['features'])
        np.testing.assert_array_equal(xx,vv)
        assert d['features'].shape==(n,120)
        reserved.append((year,d,xx,vv))
    paths={PROTOCOL,ROOT/'docs/radar-numeric-stability-registration.json',Path(__file__),ROOT/'scripts/hydro_radar_numeric.py',N/'features.npz',A/'features.npz',C/'training-masks.npz',C/'training.csv',C/'predictions.csv',B/'training.csv',R/'predictions.csv',R/'evaluation.csv',
        ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_routing_fit.py'}
    for folder in (G,V,M):paths.update(p for p in folder.rglob('*') if p.is_file())
    for folder in (B,C):
        exp=json.loads((folder/'experiment.json').read_text())
        for name,digest in exp['input_sha256'].items():
            path=Path(name);path=path if path.is_absolute() else ROOT/path;assert sha(path)==digest,name;paths.add(path)
        paths.update(folder/'models'/f'{phase}-{h}.joblib' for phase in ('validation','test') for h in range(1,13))
    runtime={name:importlib.metadata.version(name) for name in ('numpy','scipy','scikit-learn','joblib','threadpoolctl')}
    assert runtime==json.loads((C/'experiment.json').read_text())['runtime']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)}
    OUT.mkdir();(OUT/'models').mkdir();(OUT/'code').mkdir();(OUT/'protocol.json').write_bytes(PROTOCOL.read_bytes())
    for p in (Path(__file__),ROOT/'scripts/hydro_radar_numeric.py'):(OUT/'code'/p.name).write_bytes(p.read_bytes())
    np.savez_compressed(OUT/'normalized-inputs.npz',original=X,added2020=NX,year2021=reserved[0][2],year2022=reserved[1][2])
    normalized_hash=sha(OUT/'normalized-inputs.npz')
    dump(OUT/'pre-fit-manifest.json',dict(registered_at_utc=datetime.now(timezone.utc).isoformat(),input_sha256=hashes,normalized_inputs_sha256=normalized_hash,runtime=runtime,normalization_gate_passed=True,planned_models=48,training_started=False))
    start,end,stop=[epoch(s) for s in ('2025-10-01T00:00:00-03:00','2026-07-01T00:00:00-03:00','2026-09-21T00:00:00-03:00')]
    predictions=[];training=[];reproduction=[];newmodels={}
    for h in range(1,13):
        target=shift(truth,-h);delta=target-base;newtarget=shift(ny,-h);newdelta=newtarget-nb
        add=np.flatnonzero(masks[f'new_h{h}'])
        for phase,left,right in (('validation',start,end),('test',end,stop)):
            train=np.flatnonzero(masks[f'{phase}_original_h{h}']);info=meta[phase,h]
            assert len(train)==int(info['original_n']) and len(add)==int(info['added_n'])
            assert np.all(t[train]+h*3600<epoch(info['cutoff_exclusive'])) and np.all(nt[add]+h*3600<epoch(info['cutoff_exclusive']))
            scheduled=np.flatnonzero((t>=left)&(t+h*3600<right));apply=scheduled[np.isfinite(base[scheduled])];pred={}
            for family,folder,field in (('original',B,'observed_control_m'),('plus2020',C,'augmented_m')):
                rawmodel=joblib.load(folder/'models'/f'{phase}-{h}.joblib');rawpred=rawmodel.predict(F[apply])+base[apply]
                np.testing.assert_array_equal(rawpred,np.array([float(lookup[phase,iso(t[i]),h][field]) for i in apply]))
                reproduction.append(dict(phase=phase,family=family,horizon_h=h,predictions=len(apply),maximum_difference_m=0.0))
                if family=='plus2020':xf=np.vstack([NX[add],X[train]]);yf=np.r_[newdelta[add],delta[train]];levels=np.r_[newtarget[add],target[train]]
                else:xf=X[train];yf=delta[train];levels=target[train]
                model=HistGradientBoostingRegressor(**rawmodel.get_params());model.fit(xf,yf,sample_weight=1+2*(abs(yf)>=1)+2*(levels>=9))
                values=np.full(len(t),np.nan);values[apply]=model.predict(X[apply])+base[apply];assert np.isfinite(values[apply]).all();pred[family]=values
                path=OUT/'models'/f'{phase}-{family}-{h}.joblib';joblib.dump(model,path);newmodels[phase,family,h]=model
                training.append(dict(phase=phase,family=family,horizon_h=h,original_n=len(train),added_n=len(add) if family=='plus2020' else 0,n=len(yf),
                    leaf_nodes=model.max_leaf_nodes,loss=model.loss,latest_training_target=info['latest_training_target'],cutoff_exclusive=info['cutoff_exclusive']))
            for i in scheduled:
                r=lookup[phase,iso(t[i]),h];assert (float(r['actual_m'])==target[i]) if np.isfinite(target[i]) else not r['actual_m']
                predictions.append(dict(phase=phase,origin=r['origin'],target_time=r['target_time'],nominal_lead_h=h,complete24=bool(complete[i]),
                    base_m=number(base[i]),actual_m=number(target[i]),raw_original_m=float(r['observed_control_m']) if r['observed_control_m'] else None,
                    raw_plus2020_m=float(r['augmented_m']) if r['augmented_m'] else None,normalized_original_m=number(pred['original'][i]),normalized_plus2020_m=number(pred['plus2020'][i])))
            print('trained numeric',phase,h,flush=True)
    predictions.sort(key=key);assert [key(r) for r in predictions]==[key(r) for r in original]
    oldreserved=list(csv.DictReader((R/'predictions.csv').open()));rlookup={(int(r['year']),r['origin'],int(r['nominal_lead_h'])):r for r in oldreserved}
    diagnostic=[];stability=[]
    for year,d,xx,vv in reserved:
        rt,rb,ry,rc=(d[k] for k in ('times','base','truth','complete24'));n=len(rt)
        for h in range(1,13):
            apply=np.flatnonzero(np.isfinite(rb[:n-h]));out={}
            for family in ('original','plus2020'):
                model=newmodels['test',family,h];one=model.predict(xx[apply])+rb[apply];two=model.predict(vv[apply])+rb[apply];np.testing.assert_array_equal(one,two)
                z=np.full(n-h,np.nan);z[apply]=one;out[family]=z;stability.append(dict(year=year,family=family,horizon_h=h,predictions=len(apply),maximum_difference_m=0.0))
            for i in range(n-h):
                r=rlookup[year,iso(rt[i]),h];assert (float(r['actual_m'])==ry[i+h]) if np.isfinite(ry[i+h]) else not r['actual_m']
                diagnostic.append(dict(year=year,origin=r['origin'],target_time=r['target_time'],nominal_lead_h=h,complete24=bool(rc[i]),base_m=number(rb[i]),actual_m=number(ry[i+h]),
                    raw_original_m=float(r['control120_m']) if r['control120_m'] else None,raw_plus2020_m=float(r['candidate120_plus2020_m']) if r['candidate120_plus2020_m'] else None,
                    normalized_original_m=number(out['original'][i]),normalized_plus2020_m=number(out['plus2020'][i])))
    diagnostic.sort(key=lambda r:(r['year'],r['origin'],r['nominal_lead_h']));assert len(diagnostic)==26340
    evaluation=metrics(predictions,('validation','test'),'phase');development=metrics(diagnostic,('2021','2022','pooled'),'year');assert len(evaluation)==576 and len(development)==864
    for name,rows in [('predictions.csv',predictions),('evaluation.csv',evaluation),('reused-2021-2022-predictions.csv',diagnostic),('reused-2021-2022-evaluation.csv',development),('training.csv',training),('control-reproduction.csv',reproduction),('reconstruction-stability.csv',stability)]:save(OUT/name,rows)
    for name,digest in hashes.items():assert sha(ROOT/name)==digest,name
    assert sha(OUT/'normalized-inputs.npz')==normalized_hash
    dump(OUT/'experiment.json',dict(finished_at_utc=datetime.now(timezone.utc).isoformat(),runtime=runtime,models_fitted=48,controls_reproduced=48,
        original_evaluation_rows=len(predictions),reused_development_rows=len(diagnostic),metric_rows=len(evaluation)+len(development),
        reconstruction_applications_identical=len(stability),input_sha256=hashes,training_membership_changed=False,
        heldout_status='2021/2022 explicitly reused development diagnostics; not a new independent test.',promoted=False,live_issuance=False,goal_achieved=False))
    dump(OUT/'artifact-hashes.json',[dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file()])
    print(json.dumps(dict(output=str(OUT),models=48,metrics=1440,goal_achieved=False)))

if __name__=='__main__':
    with threadpool_limits(limits=2):run()
