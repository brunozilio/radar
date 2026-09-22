"""Decompose frozen July discharge predictions at three largest historical level errors.

Observed future flows are comparison-only; no candidate is fitted or emitted.
"""
import csv,hashlib,json,sys
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from hydro_hourly_forecast import BASE,epoch,iso
from hydro_hourly_models import upstream_features
from hydro_flow_diagnostics import feature_names,attribution
from hydro_upstream_audit import savecsv,predict_many
FLOW=ROOT/'outputs/experimento-niveis-reservatorios-20260921'
RANK=ROOT/'outputs/diagnostico-eventos-proxy-carreiro-20260921/all-12h-flood-errors-ranked.csv'
def read(p):return list(csv.DictReader(p.open()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths=[RANK,BASE/'dados-roteamento.npz',BASE/'telemetria-latencia.npz',BASE/'roteamento-vazao-pesos.csv',FLOW/'frozen-models.json',FLOW/'additional-features.npz',FLOW/'experiment.json',FLOW/'predictions.csv',Path(__file__),ROOT/'scripts/hydro_hourly_models.py',ROOT/'scripts/hydro_flow_diagnostics.py',ROOT/'scripts/hydro_upstream_audit.py']
d=dict(np.load(paths[1]));z=dict(np.load(paths[2]));levels=dict(np.load(paths[5]))
t=d['times'];np.testing.assert_array_equal(t,levels['times'])
F=np.column_stack([upstream_features(z,t),levels['levels_and_slopes']])
names=feature_names()+json.loads(paths[6].read_text())['additional_feature_names']
models=json.loads(paths[4].read_text())
weights={12-int(r['lag_h']):float(r['weight']) for r in read(paths[3]) if r['source']=='14 de Julho'}
stored={(r['origin'],int(r['lead_h'])):float(r['forecast_m3_s']) for r in read(paths[7]) if r['source']=='julho' and r['family']=='level_and_slopes' and r['phase']=='test'}
contributions=[];features=[];summaries=[];lead_predictions=[];maxerr=0.
for row in read(RANK)[:3]:
    origin=row['origin'];i=int(np.searchsorted(t,epoch(origin)));assert t[i]==epoch(origin)
    known=float(z['julho:Q'][np.searchsorted(z['times'],t[i])]);parts={};predsum=0.;actualsum=0.
    for lead in range(12):
        m={k:np.array(v) if isinstance(v,list) else v for k,v in models[f'julho:{lead}:test:level_and_slopes'].items()}
        change=float(predict_many(m,F[i:i+1])[0]*1000);unclipped=known+change;pred=max(unclipped,0)
        maxerr=max(maxerr,abs(pred-stored[origin,lead]));assert abs(pred-stored[origin,lead])<1e-7
        attributions=attribution(m,F[i],names)
        assert abs(sum(x['contribution_m3_s'] for x in attributions)+m['intercept']*1000-change)<1e-7
        w=weights[lead];predsum+=w*pred;actual=float(d['julho'][i+lead]*1000);assert np.isfinite(actual);actualsum+=w*actual
        for part,value in [('known_julho_Q',known),('intercept',m['intercept']*1000),('zero_floor',pred-unclipped)]+[(x['feature'],x['contribution_m3_s']) for x in attributions]:
            parts[part]=parts.get(part,0.)+w*value
        lead_predictions.append(dict(origin=origin,relative_lead_h=lead,input_target_time=iso(t[i+lead]),routing_weight=w,predicted_m3_s=pred,observed_future_comparison_only_m3_s=actual,error_m3_s=pred-actual))
    assert abs(sum(parts.values())-predsum)<1e-7
    for name,value in parts.items():contributions.append(dict(origin=origin,feature=name,routed_contribution_m3_s=value))
    for name,value in zip(names,F[i]):features.append(dict(origin=origin,feature=name,value=float(value) if np.isfinite(value) else None))
    grouped={}
    for name,value in parts.items():
        group=name.split(':')[0];grouped[group]=grouped.get(group,0.)+value
    summaries.append(dict(origin=origin,target_time=row['target_time'],level_error_m=float(row['signed_error_m']),known_julho_m3_s=known,routed_julho_forecast_m3_s=predsum,routed_julho_observed_future_comparison_only_m3_s=actualsum,routed_julho_error_m3_s=predsum-actualsum,groups=grouped,largest_feature_contributions=sorted(parts.items(),key=lambda p:abs(p[1]),reverse=True)[:12]))
for name,data in [('feature-contributions',contributions),('features',features),('upstream-predictions',lead_predictions)]:savecsv(OUT/(name+'.csv'),data)
result=dict(scope='Post-evaluation diagnostic of three largest absolute 12h historical flood errors; selected by error for investigation only, not validation or candidate selection.',input_sha256={str(p):sha(p) for p in paths},prediction_reproduction_max_difference_m3_s=maxerr,items=summaries,fitted=False,promoted=False,goal_achieved=False)
(OUT/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summaries,ensure_ascii=False))
