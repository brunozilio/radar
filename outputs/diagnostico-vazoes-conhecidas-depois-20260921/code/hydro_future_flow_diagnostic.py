"""NON-FORECAST diagnostic using upstream observations unavailable at issuance.

Never register these reconstructions in the prospective ledger or live runner.
"""
import csv,hashlib,json
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from hydro_hourly_forecast import ROOT,BASE,epoch,dump
from hydro_hourly_models import upstream_features
from hydro_upstream_audit import predict_many,savecsv
from hydro_downstream_flow_delta import updated_stage
FLOW=ROOT/'outputs/experimento-niveis-reservatorios-20260921'
PRIOR=ROOT/'outputs/experimento-proxy-carreiro-20260921'
OUT=ROOT/'outputs/diagnostico-vazoes-conhecidas-depois-20260921'
FAMILIES=('reference','observed_julho','observed_carreiro','observed_both')


def observed_delta(estimated,truth,origin_index,horizon,weights,lags):
    if len(weights)!=len(lags) or any(lag<1 for lag in lags):raise ValueError('Past anchor must stay unchanged')
    if not np.isfinite(weights).all() or min(weights)<0 or abs(sum(weights)-1)>1e-6:raise ValueError('Invalid routing kernel')
    total=0.;required=0
    for w,lag in zip(weights,lags):
        k=horizon-lag
        if w==0 or k<0:continue
        required+=1
        observed=truth[origin_index+k]
        if not np.isfinite([observed,estimated[k]]).all():return np.nan,required
        total+=w*(observed-estimated[k])
    return total,required


def run():
    protocol=ROOT/'docs/future-flow-diagnostic-protocol.json'
    assert json.loads(protocol.read_text())['uses_information_unavailable_at_issuance'] is True
    paths=[protocol,PRIOR/'predictions.csv',PRIOR/'experiment.json',PRIOR/'artifact-hashes.json',
           PRIOR/'modeled-carreiro-inputs.npz',FLOW/'additional-features.npz',FLOW/'frozen-models.json',FLOW/'predictions.csv',
           BASE/'dados-roteamento.npz',BASE/'telemetria-latencia.npz',BASE/'conferencia-balanco.json',BASE/'roteamento-vazao-pesos.csv',
           Path(__file__),ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_hourly_models.py',ROOT/'scripts/hydro_upstream_audit.py',ROOT/'scripts/hydro_downstream_flow_delta.py']
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    manifest=json.loads(paths[3].read_text())
    for p in (paths[1],paths[4]):assert hashes[str(p)]==manifest[p.name]
    inputs=json.loads(paths[2].read_text())['input_sha256']
    for p in paths[5:12]:assert hashes[str(p)]==inputs[str(p)]
    d=dict(np.load(paths[8]));z=dict(np.load(paths[9]));extra=dict(np.load(paths[5]));proxy=dict(np.load(paths[4]));t=d['times']
    for a in (extra,proxy):np.testing.assert_array_equal(a['times'],t)
    F=upstream_features(z,t);F77=np.column_stack([F,extra['levels_and_slopes']]);models=json.loads(paths[6].read_text());flows={}
    for source,key,family,X in [('julho','julho:Q','level_and_slopes',F77),('carreiro','86500000:Q','reference',F)]:
        known=z[key][np.searchsorted(z['times'],t)]/1000
        flows[source]=np.column_stack([np.maximum(known+predict_many({k:np.array(v) if isinstance(v,list) else v for k,v in models[f'{source}:{lead}:test:{family}'].items()},X),0)*1000 for lead in range(12)])
    maxerror=0.
    for r in csv.DictReader(paths[7].open()):
        if r['phase']!='test' or (r['source'],r['family']) not in [('julho','level_and_slopes'),('carreiro','reference')]:continue
        i=int(np.searchsorted(t,epoch(r['origin'])));assert t[i]==epoch(r['origin'])
        maxerror=max(maxerror,abs(flows[r['source']][i,int(r['lead_h'])]-float(r['forecast_m3_s'])))
    assert maxerror<1e-7
    flows['carreiro']=np.where(np.isfinite(flows['carreiro']),flows['carreiro'],proxy['estimated_q_m3_s'])
    kernel=list(csv.DictReader(paths[11].open()));kernels={}
    for source,label in [('julho','14 de Julho'),('carreiro','Passo Carreiro')]:
        rr=[r for r in kernel if r['source']==label];kernels[source]=([float(r['weight']) for r in rr],[int(r['lag_h']) for r in rr])
    rating=json.loads(paths[10].read_text())['rating_parameters'];result=[]
    for r in csv.DictReader(paths[1].open()):
        at=epoch(r['origin']);i=int(np.searchsorted(t,at));assert t[i]==at;h=int(r['nominal_lead_h'])
        ai=int(np.searchsorted(z['times'],epoch(r['anchor_at'])));assert z['times'][ai]==epoch(r['anchor_at'])
        base=float(r['julho_levels_m']) if r['julho_levels_m'] else None
        deltas={s:observed_delta(flows[s][i],d[s]*1000,i,h,*kernels[s]) for s in ('julho','carreiro')}
        values={'reference_m':base};statuses={'reference_status':r['status']}
        for family,sources in [('observed_julho',('julho',)),('observed_carreiro',('carreiro',)),('observed_both',('julho','carreiro'))]:
            dq=sum(deltas[s][0] for s in sources)
            if base is None:value=None;status='baseline_unavailable'
            elif not np.isfinite(dq):value=None;status='missing_required_upstream_observation'
            elif all(deltas[s][1]==0 for s in sources):value=base;status='no_future_input_in_kernel'
            else:
                value,_,_=updated_stage(base,z['raw:86510000:H'][ai],z['raw:86510000:Q'][ai],dq,rating)
                value=float(value) if np.isfinite(value) else None
                status='reconstructed_with_unavailable_information' if value is not None else 'invalid_reconstructed_flow'
            values[family+'_m']=value;statuses[family+'_status']=status
        result.append(dict(origin=r['origin'],target_time=r['target_time'],nominal_lead_h=h,anchor_at=r['anchor_at'],
                           actual_m=float(r['actual_m']) if r['actual_m'] else None,**values,**statuses,
                           delta_julho_m3_s=float(deltas['julho'][0]) if np.isfinite(deltas['julho'][0]) else None,
                           delta_carreiro_m3_s=float(deltas['carreiro'][0]) if np.isfinite(deltas['carreiro'][0]) else None))
    evaluations=[]
    for h in range(1,13):
        for high in (False,True):
            targets=[r for r in result if r['nominal_lead_h']==h and r['actual_m'] is not None and (not high or r['actual_m']>=7)]
            common=[r for r in targets if all(r[f+'_m'] is not None for f in FAMILIES)]
            for population in ('individual','common_four'):
                for family in FAMILIES:
                    rr=[r for r in (common if population=='common_four' else targets) if r[family+'_m'] is not None]
                    e=np.array([r[family+'_m']-r['actual_m'] for r in rr]);ae=abs(e)
                    evaluations.append(dict(horizon_h=h,subset='high' if high else 'all',population=population,family=family,
                                            observed_targets=len(targets),n=len(rr),excluded_n=len(targets)-len(rr),hits=int((ae<=.5).sum()),
                                            hit_fraction=float((ae<=.5).mean()),mae_m=float(ae.mean()),bias_m=float(e.mean()),
                                            p90_abs_m=float(np.quantile(ae,.9)),p98_abs_m=float(np.quantile(ae,.98)),max_abs_m=float(ae.max())))
    OUT.mkdir(parents=True,exist_ok=False);(OUT/'protocol.json').write_bytes(protocol.read_bytes())
    savecsv(OUT/'reconstructions-not-forecasts.csv',result);savecsv(OUT/'evaluation-diagnostic-only.csv',evaluations)
    np.savez_compressed(OUT/'reference-estimated-flows.npz',times=t,**flows)
    (OUT/'code').mkdir()
    for p in paths:
        if p.suffix=='.py':(OUT/'code'/p.name).write_bytes(p.read_bytes())
    for p,digest in hashes.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest
    dump(OUT/'diagnostic.json',dict(input_sha256=hashes,rows=len(result),upstream_reference_max_difference_m3_s=maxerror,
                                   uses_information_unavailable_at_issuance=True,models_fitted=0,
                                   valid_operational_forecast=False,eligible_for_goal=False,promoted=False,goal_achieved=False,
                                   limitation='Not a theoretical accuracy upper bound: model errors can compensate. Missing observedflows reduce coverage; compare the common-four sample.'))
    print(json.dumps({'output':str(OUT),'rows':len(result),'NOT_A_FORECAST':True}))


if __name__=='__main__':
    with threadpool_limits(limits=2):run()
