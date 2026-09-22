"""Fit rating on paired H/Q, independent of missing routing covariates."""
import csv,hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from hydro_hourly_forecast import ROOT,BASE,epoch,dump
from hydro_downstream_flow_delta import stage,updated_stage
from hydro_upstream_audit import savecsv
PRIOR=ROOT/'outputs/experimento-proxy-carreiro-20260921'
OUT=ROOT/'outputs/experimento-curva-pares-hq-20260921'


def fit_curve(q,h,indices):
    if not len(indices) or not np.isfinite(q[indices]).all() or not np.isfinite(h[indices]).all() or np.any(q[indices]<0):
        raise ValueError('Finite nonnegativeQ and finiteH training pairs required')
    result=least_squares(lambda p:p[0]*q[indices]**p[1]+p[2]-h[indices],
                         [4.5,.64,.4],bounds=([.01,.1,-10],[20,1.2,10]),loss='soft_l1')
    if not result.success or not np.isfinite(result.x).all():raise ValueError('Curve fit failed')
    return result.x,dict(success=bool(result.success),status=int(result.status),cost=float(result.cost),optimality=float(result.optimality),nfev=int(result.nfev))


def replace_curve(base_h,anchor_h,anchor_q,old,new):
    _,q,_=updated_stage(base_h,anchor_h,anchor_q,0.,old)
    if not np.isfinite(q):return np.nan,np.nan
    return float(stage(q,new)+anchor_h-stage(anchor_q,new)),q


def metrics(e):
    e=np.asarray(e);a=abs(e)
    return dict(n=len(e),hits=int((a<=.5).sum()),hit_fraction=float((a<=.5).mean()),mae_m=float(a.mean()),
                bias_m=float(e.mean()),p90_abs_m=float(np.quantile(a,.9)),p98_abs_m=float(np.quantile(a,.98)),max_abs_m=float(a.max()))


def run():
    policy=ROOT/'docs/rating-paired-only-protocol.json'
    assert json.loads(policy.read_text())['id']=='rating-all-paired-hq-v1'
    paths=[policy,BASE/'dados-roteamento.npz',BASE/'telemetria-latencia.npz',BASE/'conferencia-balanco.json',
           PRIOR/'predictions.csv',PRIOR/'experiment.json',PRIOR/'artifact-hashes.json',
           Path(__file__),ROOT/'scripts/hydro_downstream_flow_delta.py',ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_upstream_audit.py']
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    oldmeta=json.loads(paths[5].read_text())['input_sha256']
    for p in paths[1:4]:assert hashes[str(p)]==oldmeta[str(p)]
    assert hashes[str(paths[4])]==json.loads(paths[6].read_text())['predictions.csv']
    d=dict(np.load(paths[1]));z=dict(np.load(paths[2]));t=d['times'];q=d['q'];h=d['h']
    paired=np.isfinite(q)&np.isfinite(h);routing=paired&np.isfinite(d['X']).all(axis=1)
    a=epoch('2025-10-01T00:00:00-03:00');b=epoch('2026-07-01T00:00:00-03:00');c=epoch('2026-09-21T00:00:00-03:00')
    models={};curve_scores=[];fitting=[];curve_rows=[]
    for phase,cutoff,end in [('validation',a,b),('test',b,c)]:
        evaluation=np.where(paired&(t>=cutoff)&(t<end))[0]
        for family,valid in [('original_membership',routing),('all_paired_hq',paired)]:
            idx=np.where(valid&(t<cutoff))[0];pars,info=fit_curve(q,h,idx)
            models[phase+':'+family]=pars.tolist()
            fitting.append(dict(phase=phase,family=family,training_n=len(idx),training_high_n=int((h[idx]>=7).sum()),
                                latest_training_epoch=float(t[idx].max()),cutoff_exclusive_epoch=cutoff,training_qmax_m3_s=float(q[idx].max()*1000),**info))
            values=stage(q[evaluation]*1000,pars)
            for high in (False,True):
                select=h[evaluation]>=7 if high else np.ones(len(evaluation),dtype=bool)
                curve_scores.append(dict(phase=phase,family=family,subset='high' if high else 'all',**metrics(values[select]-h[evaluation][select])))
            for i,value in zip(evaluation,values):curve_rows.append(dict(phase=phase,family=family,epoch=float(t[i]),reported_q_m3_s=float(q[i]*1000),observed_h_m=float(h[i]),stage_m=float(value)))
    old=np.array(json.loads(paths[3].read_text())['rating_parameters']);new=np.array(models['test:all_paired_hq'])
    maximum=float(abs(np.array(models['test:original_membership'])-old).max());assert maximum<1e-7
    result=[];decomposition=[];roundtrip=0.
    for r in csv.DictReader(paths[4].open()):
        ai=int(np.searchsorted(z['times'],epoch(r['anchor_at'])));ti=int(np.searchsorted(z['times'],epoch(r['target_time'])))
        assert z['times'][ai]==epoch(r['anchor_at']) and z['times'][ti]==epoch(r['target_time'])
        ah=z['raw:86510000:H'][ai];aq=z['raw:86510000:Q'][ai]
        base=float(r['julho_levels_m']) if r['julho_levels_m'] else np.nan
        candidate,pq=replace_curve(base,ah,aq,old,new)
        if np.isfinite(base):
            replay,_=replace_curve(base,ah,aq,old,old);roundtrip=max(roundtrip,abs(replay-base))
        actual=float(r['actual_m']) if r['actual_m'] else None
        status='missing_exact_anchor' if r['status']=='missing_exact_anchor' else 'missing_or_invalid_forecast_input' if not np.isfinite(candidate) else 'missing_exact_target' if actual is None else 'paired'
        result.append(dict(origin=r['origin'],target_time=r['target_time'],nominal_lead_h=int(r['nominal_lead_h']),anchor_at=r['anchor_at'],
                           actual_m=actual,reference_m=float(base) if np.isfinite(base) else None,candidate_m=float(candidate) if np.isfinite(candidate) else None,
                           previous_status=r['status'],candidate_status=status,preserved_predicted_q_m3_s=float(pq) if np.isfinite(pq) else None))
        tq=z['raw:86510000:Q'][ti]
        if actual is not None and np.isfinite([base,aq,ah,tq,pq]).all():
            curve_error=float(ah-stage(aq,old)-(actual-stage(tq,old)))
            flow_error=float(stage(pq,old)-stage(tq,old));error=base-actual
            assert abs(curve_error+flow_error-error)<1e-9
            decomposition.append(dict(origin=r['origin'],target_time=r['target_time'],horizon_h=int(r['nominal_lead_h']),actual_m=actual,
                                      total_error_m=error,flow_conversion_error_m=flow_error,anchor_curve_error_m=curve_error,
                                      reported_target_q_m3_s=float(tq),predicted_q_m3_s=float(pq)))
    evaluations=[];components=[]
    for lead in range(1,13):
        for high in (False,True):
            rr=[r for r in result if r['nominal_lead_h']==lead and r['actual_m'] is not None and (not high or r['actual_m']>=7)]
            common=[r for r in rr if r['reference_m'] is not None and r['candidate_m'] is not None]
            for population in ('individual','common'):
                for family in ('reference','candidate'):
                    ss=[r for r in (common if population=='common' else rr) if r[family+'_m'] is not None]
                    evaluations.append(dict(horizon_h=lead,subset='high' if high else 'all',population=population,family=family,observed_targets=len(rr),**metrics([r[family+'_m']-r['actual_m'] for r in ss])))
            comp=[r for r in decomposition if r['horizon_h']==lead and (not high or r['actual_m']>=7)]
            for name in ('total_error_m','flow_conversion_error_m','anchor_curve_error_m'):
                components.append(dict(horizon_h=lead,subset='high' if high else 'all',component=name,**metrics([r[name] for r in comp])))
    OUT.mkdir(parents=True,exist_ok=False);(OUT/'protocol.json').write_bytes(policy.read_bytes())
    for name,rows in [('training',fitting),('curve-fit-evaluation',curve_scores),('curve-fit-pairs',curve_rows),('predictions',result),('evaluation',evaluations),('error-decomposition',decomposition),('component-metrics',components)]:savecsv(OUT/(name+'.csv'),rows)
    dump(OUT/'curves.json',models);(OUT/'code').mkdir()
    for p in paths:
        if p.suffix=='.py':(OUT/'code'/p.name).write_bytes(p.read_bytes())
    for p,digest in hashes.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest
    dump(OUT/'experiment.json',dict(input_sha256=hashes,curves_fitted=4,reference_parameters_max_difference=maximum,reference_stage_roundtrip_m=roundtrip,
                                   rows=len(result),decomposed_rows=len(decomposition),promoted=False,live_issuance=False,goal_achieved=False,
                                   limitation='ReportedQ is not certified independent physicalgauging; chronological development and old effectiveHGEparameters retained.'))
    print(json.dumps({'output':str(OUT),'curves':models,'reference_difference':maximum,'rows':len(result)}))


if __name__=='__main__':run()
