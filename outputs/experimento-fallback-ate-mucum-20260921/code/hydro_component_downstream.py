"""Propagate only conditional future-Julho changes to fixed Muçum hindcasts."""
import csv,hashlib,json
from pathlib import Path
from collections import Counter
import numpy as np
from hydro_hourly_forecast import ROOT,BASE,epoch,dump
from hydro_downstream_flow_delta import future_flow_delta,updated_stage
from hydro_upstream_audit import savecsv
PRIOR=ROOT/'outputs/experimento-proxy-carreiro-20260921'
UPSTREAM=ROOT/'outputs/experimento-fallback-componentes-20260921'
OUT=ROOT/'outputs/experimento-fallback-ate-mucum-20260921'


def run():
    protocol=ROOT/'docs/component-downstream-protocol.json'
    assert json.loads(protocol.read_text())['id']=='component-downstream-v1'
    paths=[protocol,PRIOR/'predictions.csv',PRIOR/'experiment.json',PRIOR/'artifact-hashes.json',
           UPSTREAM/'predictions.csv',UPSTREAM/'experiment.json',UPSTREAM/'protocol.json',
           BASE/'telemetria-latencia.npz',BASE/'conferencia-balanco.json',BASE/'roteamento-vazao-pesos.csv',
           Path(__file__),ROOT/'scripts/hydro_downstream_flow_delta.py',ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_upstream_audit.py']
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    manifest=json.loads(paths[3].read_text());assert hashes[str(paths[1])]==manifest['predictions.csv']
    old=json.loads(paths[2].read_text())['input_sha256']
    for p in paths[7:10]:assert hashes[str(p)]==old[str(p)]
    source={}
    for r in csv.DictReader(paths[4].open()):
        if r['phase']=='test':
            k=r['origin'],int(r['lead_h']);assert k not in source;source[k]=r
    z=dict(np.load(paths[7]));rating=json.loads(paths[8].read_text())['rating_parameters']
    kr=[r for r in csv.DictReader(paths[9].open()) if r['source']=='14 de Julho']
    weights=[float(r['weight']) for r in kr];lags=[int(r['lag_h']) for r in kr]
    assert min(lags)>=1 # Both anchor endpoints remain independent of future-Julho inference.
    result=[];affected=0;roundtrip=0.
    for r in csv.DictReader(paths[1].open()):
        h=int(r['nominal_lead_h']);origin=r['origin'];base=float(r['julho_levels_m']) if r['julho_levels_m'] else None
        required=[source[origin,k] for k in range(h)]
        selected={x['fallback_selected'] for x in required};assert len(selected)==1
        conditional=selected=={'True'}
        if not conditional:
            candidate=base;dq=0.;status=r['status']
        else:
            affected+=1
            previous=np.array([float(x['reference_m3_s']) for x in required]);new=np.array([float(x['forecast_m3_s']) for x in required])
            dq=future_flow_delta(previous,new,weights,lags,h)
            ai=int(np.searchsorted(z['times'],epoch(r['anchor_at'])));assert z['times'][ai]==epoch(r['anchor_at'])
            value,q0,q1=updated_stage(base if base is not None else np.nan,z['raw:86510000:H'][ai],z['raw:86510000:Q'][ai],dq,rating)
            candidate=float(value) if np.isfinite(value) else None
            replay,_,_=updated_stage(base if base is not None else np.nan,z['raw:86510000:H'][ai],z['raw:86510000:Q'][ai],0.,rating)
            if base is not None:roundtrip=max(roundtrip,abs(replay-base))
            status='missing_exact_anchor' if r['status']=='missing_exact_anchor' else 'missing_or_invalid_forecast_input' if candidate is None else 'missing_exact_target' if not r['actual_m'] else 'paired'
        result.append(dict(origin=origin,target_time=r['target_time'],nominal_lead_h=h,anchor_at=r['anchor_at'],
                           actual_m=float(r['actual_m']) if r['actual_m'] else None,
                           reference_m=base,candidate_m=candidate,previous_status=r['status'],candidate_status=status,
                           conditional_selected=conditional,delta_julho_routed_m3_s=float(dq)))
    evaluation=[];transitions=[]
    for h in range(1,13):
        for high in (False,True):
            rs=[r for r in result if r['nominal_lead_h']==h and r['actual_m'] is not None and (not high or r['actual_m']>=7)]
            common=[r for r in rs if r['reference_m'] is not None and r['candidate_m'] is not None]
            for population in ('individual','common'):
                for family in ('reference','candidate'):
                    pair=[r for r in (common if population=='common' else rs) if r[family+'_m'] is not None]
                    e=np.array([r[family+'_m']-r['actual_m'] for r in pair]);ae=abs(e)
                    evaluation.append(dict(horizon_h=h,subset='high' if high else 'all',population=population,family=family,
                                           observed_targets=len(rs),n=len(e),hits=int((ae<=.5).sum()),hit_fraction=float((ae<=.5).mean()),
                                           mae_m=float(ae.mean()),bias_m=float(e.mean()),p90_abs_m=float(np.quantile(ae,.9)),
                                           p98_abs_m=float(np.quantile(ae,.98)),max_abs_m=float(ae.max())))
            oldhit=np.array([abs(r['reference_m']-r['actual_m'])<=.5 for r in common])
            newhit=np.array([abs(r['candidate_m']-r['actual_m'])<=.5 for r in common])
            transitions.append(dict(horizon_h=h,subset='high' if high else 'all',common_n=len(common),
                                    gained_hits=int((~oldhit&newhit).sum()),lost_hits=int((oldhit&~newhit).sum())))
    OUT.mkdir(parents=True,exist_ok=False);(OUT/'protocol.json').write_bytes(protocol.read_bytes())
    savecsv(OUT/'predictions.csv',result);savecsv(OUT/'evaluation.csv',evaluation);savecsv(OUT/'hit-transitions.csv',transitions)
    (OUT/'code').mkdir()
    for p in paths:
        if p.suffix=='.py':(OUT/'code'/p.name).write_bytes(p.read_bytes())
    for p,digest in hashes.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest
    dump(OUT/'experiment.json',dict(input_sha256=hashes,rows=len(result),selected_rows=affected,
                                   candidate_status_counts=dict(Counter(r['candidate_status'] for r in result)),
                                   stage_roundtrip_max_error_m=roundtrip,models_fitted=0,
                                   promoted=False,live_issuance=False,goal_achieved=False,historical_availability_verified=False))
    print(json.dumps({'rows':len(result),'selected_rows':affected,'roundtrip_m':roundtrip,'output':str(OUT)}))


if __name__=='__main__':run()
