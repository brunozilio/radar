"""Exact downstream stage update when only future upstream inference changes."""
import argparse,csv,hashlib,json
from pathlib import Path
from collections import Counter
import numpy as np
from threadpoolctl import threadpool_limits
from hydro_hourly_forecast import ROOT,BASE,epoch,dump
from hydro_hourly_models import upstream_features
from hydro_upstream_audit import predict_many,savecsv

RAIN=ROOT/'outputs/experimento-chuva-prevista-montante-20260921'
PRIOR=ROOT/'outputs/experimento-proxy-carreiro-20260921'
LEVELS=ROOT/'outputs/experimento-niveis-reservatorios-20260921'


def stage(q,rating):
    a,b,c=rating
    if a<=0 or b<=0 or not np.isfinite(rating).all():raise ValueError('Noninvertible rating')
    return a*np.maximum(np.asarray(q)/1000,0)**b+c


def updated_stage(base_h,anchor_h,anchor_q,delta_q,rating):
    if not np.isfinite([base_h,anchor_h,anchor_q,delta_q]).all():return np.nan,np.nan,np.nan
    if anchor_q<0:raise ValueError('Negative observed anchor flow')
    offset=anchor_h-float(stage(anchor_q,rating));a,b,c=rating
    adjusted=base_h-offset-c
    if adjusted < -1e-10:raise ValueError('Baseline outside invertible rating range')
    qbase=1000*(max(adjusted,0)/a)**(1/b)
    if abs(float(stage(qbase,rating))+offset-base_h)>1e-9:raise ValueError('Rating inversion failed')
    qnew=qbase+delta_q
    return (float(stage(qnew,rating))+offset if qnew>=0 else np.nan),qbase,qnew


def future_flow_delta(old,new,weights,lags,horizon):
    if len(weights)!=len(lags) or any(lag<1 for lag in lags) or not np.isfinite(weights).all() or min(weights)<0 or abs(sum(weights)-1)>1e-6:
        raise ValueError('Routing does not preserve common historical anchor')
    total=0.
    for w,lag in zip(weights,lags):
        k=horizon-lag
        if k<0 or w==0:continue
        if not np.isfinite([old[k],new[k]]).all():return np.nan
        total+=w*(new[k]-old[k])
    return total


def evaluate(rows):
    result=[]
    for horizon in range(1,13):
        for high in [False,True]:
            selected=[r for r in rows if int(r['nominal_lead_h'])==horizon and r['actual_m'] is not None and (not high or r['actual_m']>=7)]
            for population in ['all_available','common_pairs']:
                common=[r for r in selected if all(r[f+'_m'] is not None for f in ['julho_levels','julho_levels_rain'])]
                for family in ['julho_levels','julho_levels_rain']:
                    paired=[r for r in (common if population=='common_pairs' else selected) if r[family+'_m'] is not None]
                    e=np.array([r[family+'_m']-r['actual_m'] for r in paired]);ae=abs(e)
                    result.append(dict(nominal_lead_h=horizon,subset='level_ge_7m' if high else 'all',population=population,family=family,observed_targets=len(selected),paired_n=len(e),forecast_failures_with_truth=len(selected)-len(e),coverage=len(e)/len(selected) if selected else None,within_0_50_n=int((ae<=.5).sum()),within_0_50_fraction=float((ae<=.5).mean()) if len(e) else None,mae_m=float(ae.mean()) if len(e) else None,bias_m=float(e.mean()) if len(e) else None,p90_abs_m=float(np.quantile(ae,.9)) if len(e) else None,p98_abs_m=float(np.quantile(ae,.98)) if len(e) else None,max_abs_m=float(ae.max()) if len(e) else None))
    return result


def run(out,policy_path):
    policy=json.loads(policy_path.read_text())
    if policy['id']!='downstream-forecast-rain-delta-v1':raise ValueError('Unsupported protocol')
    paths=[policy_path,PRIOR/'predictions.csv',PRIOR/'artifact-hashes.json',RAIN/'frozen-models.json',RAIN/'forecast-rain-features.npz',RAIN/'predictions.csv',RAIN/'artifact-hashes.json',LEVELS/'additional-features.npz',BASE/'dados-roteamento.npz',BASE/'telemetria-latencia.npz',BASE/'conferencia-balanco.json',BASE/'roteamento-vazao-pesos.csv',Path(__file__),ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_hourly_models.py',ROOT/'scripts/hydro_upstream_audit.py']
    hashes={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    for folder in [PRIOR,RAIN]:
        manifest=json.loads((folder/'artifact-hashes.json').read_text())
        for p in paths:
            if p.parent==folder and p.name!='artifact-hashes.json':assert hashes[str(p.resolve())]==manifest[p.name]
    prior_meta=json.loads((PRIOR/'experiment.json').read_text())
    for p in paths[7:12]:assert hashes[str(p.resolve())]==prior_meta['input_sha256'][str(p.resolve())]
    d=dict(np.load(paths[8]));z=dict(np.load(paths[9]));extra=dict(np.load(paths[7]));rain=dict(np.load(paths[4]));t=d['times']
    np.testing.assert_array_equal(extra['times'],t);np.testing.assert_array_equal(rain['times'],t)
    F=np.column_stack([upstream_features(z,t),extra['levels_and_slopes']]);X=np.column_stack([F,rain['values']])
    known=z['julho:Q'][np.searchsorted(z['times'],t)]/1000
    models=json.loads(paths[3].read_text());flows={}
    for family,features in [('level_and_slopes',F),('levels_forecast_rain',X)]:
        flows[family]=np.column_stack([np.maximum(known+predict_many({k:np.array(v) if isinstance(v,list) else v for k,v in models[f'julho:{lead}:test:{family}'].items()},features),0)*1000 for lead in range(12)])
    max_flow_error=0.
    for r in csv.DictReader(paths[5].open()):
        if r['source']!='julho' or r['phase']!='test':continue
        i=int(np.searchsorted(t,epoch(r['origin'])));assert t[i]==epoch(r['origin'])
        diff=abs(flows[r['family']][i,int(r['lead_h'])]-float(r['forecast_m3_s']));max_flow_error=max(max_flow_error,diff)
    if max_flow_error>1e-7:raise ValueError('Upstream predictions not reproduced')
    rating=json.loads(paths[10].read_text())['rating_parameters']
    kr=[r for r in csv.DictReader(paths[11].open()) if r['source']=='14 de Julho'];weights=[float(r['weight']) for r in kr];lags=[int(r['lag_h']) for r in kr]
    result=[];roundtrip=0.
    for r in csv.DictReader(paths[1].open()):
        i=int(np.searchsorted(t,epoch(r['origin'])));assert t[i]==epoch(r['origin'])
        anchor=epoch(r['anchor_at']);ai=int(np.searchsorted(z['times'],anchor))
        assert ai<len(z['times']) and z['times'][ai]==anchor
        base=float(r['julho_levels_m']) if r['julho_levels_m'] else np.nan
        actual=float(r['actual_m']) if r['actual_m'] else None
        dq=future_flow_delta(flows['level_and_slopes'][i],flows['levels_forecast_rain'][i],weights,lags,int(r['nominal_lead_h']))
        candidate,qbase,qnew=updated_stage(base,z['raw:86510000:H'][ai],z['raw:86510000:Q'][ai],dq,rating)
        if np.isfinite(base):
            unchanged,_,_=updated_stage(base,z['raw:86510000:H'][ai],z['raw:86510000:Q'][ai],0.,rating)
            if np.isfinite(unchanged):roundtrip=max(roundtrip,abs(unchanged-base))
        status='missing_exact_anchor' if r['status']=='missing_exact_anchor' else 'missing_or_invalid_forecast_input' if not np.isfinite(candidate) else 'missing_exact_target' if actual is None else 'paired'
        result.append({k:r[k] for k in ['origin','target_time','nominal_lead_h','anchor_at','state_rain_observations_end_at','modeled_car_history_inputs','modeled_car_future_inputs','uses_missing_flow_proxy']}|dict(actual_m=actual,julho_levels_m=float(base) if np.isfinite(base) else None,julho_levels_rain_m=float(candidate) if np.isfinite(candidate) else None,previous_status=r['status'],candidate_status=status,delta_julho_routed_m3_s=float(dq) if np.isfinite(dq) else None,baseline_total_q_m3_s=float(qbase) if np.isfinite(qbase) else None,candidate_total_q_m3_s=float(qnew) if np.isfinite(qnew) else None))
    out.mkdir(parents=True,exist_ok=False);(out/'protocol.json').write_bytes(policy_path.read_bytes())
    savecsv(out/'predictions.csv',result);savecsv(out/'evaluation.csv',evaluate(result))
    (out/'code').mkdir()
    for p in paths:
        if p.suffix=='.py':(out/'code'/p.name).write_bytes(p.read_bytes())
    for name,expected in hashes.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==expected
    dump(out/'experiment.json',dict(input_sha256=hashes,rows=len(result),candidate_status_counts=dict(Counter(r['candidate_status'] for r in result)),upstream_reproduction_max_error_m3_s=max_flow_error,stage_roundtrip_max_error_m=roundtrip,fitted_here=False,historical_availability_verified=False,promoted=False,live_issuance=False,goal_achieved=False))
    print(json.dumps({'output':str(out),'rows':len(result),'status_counts':dict(Counter(r['candidate_status'] for r in result)),'roundtrip_error_m':roundtrip}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--protocol',type=Path,default=ROOT/'docs/downstream-forecast-rain-delta-protocol.json');a=p.parse_args()
    with threadpool_limits(limits=2):run(a.output,a.protocol)
