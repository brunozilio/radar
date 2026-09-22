"""Audit upstream-flow extrapolation; no live model or forecast is replaced.

Chronological development experiment: the July–September evaluation period has
been inspected before and is NOT a fresh independent holdout or prospective proof.
"""
import argparse, csv, hashlib, json
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from hydro_hourly_forecast import ridge_fit, ridge_predict, epoch, iso, ROOT, BASE, dump
from hydro_hourly_models import upstream_features, GROUPS
from hydro_routing_fit import shift
from hydro_flow_diagnostics import feature_names, attribution, outside_training_range

def predict_many(state,X):
    a=np.column_stack([np.where(np.isfinite(X),X,state['median']),~np.isfinite(X)])
    return (a-state['mean'])/state['scale']@state['beta']+state['intercept']

def metrics(p,y,high):
    result={}
    for label,mask in [('all',np.isfinite(y)&np.isfinite(p)),('high_flow',np.isfinite(y)&np.isfinite(p)&high)]:
        e=(p[mask]-y[mask])*1000
        result[label]={'n':len(e),'mae_m3_s':float(abs(e).mean()) if len(e) else None,'bias_m3_s':float(e.mean()) if len(e) else None,'p90_absolute_m3_s':float(np.quantile(abs(e),.9)) if len(e) else None}
    return result

def savecsv(path,records):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)

def run(source,out):
    out.mkdir(parents=True,exist_ok=False)
    d=dict(np.load(BASE/'dados-roteamento.npz'));z=dict(np.load(BASE/'telemetria-latencia.npz'))
    nd=dict(np.load(source/'dados-roteamento.npz'));nz=dict(np.load(source/'telemetria-latencia.npz'))
    t=d['times'];F=upstream_features(z,t);NF=upstream_features(nz,nd['times'])[-1]
    names=feature_names();assert F.shape[1]==len(names)
    saved={(r['source'],int(r['lead_h'])):r for r in csv.DictReader((source/'previsao-vazoes-montante.csv').open())}
    split=epoch('2025-10-01T00:00:00-03:00');teststart=epoch('2026-07-01T00:00:00-03:00');cutoff=epoch('2026-09-21T00:00:00-03:00')
    selection=[];evaluation=[];current=[];decomposition=[];outliers=[];predictions=[];frozen={}
    for source_id,key in [('julho','julho:Q'),('carreiro','86500000:Q')]:
        known=z[key][np.searchsorted(z['times'],t)]/1000;latest=float(nz[key][-1]/1000)
        prior=d[source_id][t<split];threshold=float(np.quantile(prior[np.isfinite(prior)],.95))
        trainingmax=float(np.nanmax(d[source_id][t<cutoff]))
        for lead in range(12):
            target=shift(d[source_id],-lead);delta=target-known
            valid=np.isfinite(target)&np.isfinite(known)
            tr=np.where(valid&(t+lead*3600<split))[0]
            va=np.where(valid&(t>=split)&(t+lead*3600<teststart))[0]
            pretest=np.where(valid&(t+lead*3600<teststart))[0]
            te=np.where(valid&(t>=teststart)&(t+lead*3600<cutoff))[0]
            final=np.where(valid&(t+lead*3600<cutoff))[0]
            alpha=float(saved[source_id,lead]['alpha']);w=1+2*(target>2)
            vmodel=ridge_fit(F,delta,tr,alpha,w)
            vr=predict_many(vmodel,F[va]);choices=[]
            for gain in [0.,.25,.5,.75,1.]:
                p=np.maximum(known[va]+gain*vr,0)
                m=metrics(p,target[va],target[va]>=threshold)
                score=m['all']['mae_m3_s']+.5*m['high_flow']['mae_m3_s']
                choices.append((score,gain))
            score,gain=min(choices)
            selection.append({'source':source_id,'lead_h':lead,'gain':gain,'validation_score_m3_s':score,'high_flow_threshold_m3_s':threshold*1000,'validation_n':len(va),'validation_latest_target':iso((t[va]+lead*3600).max())})
            model=ridge_fit(F,delta,pretest,alpha,w);changes=predict_many(model,F[te])
            for candidate,g in [('ridge_reference',1.),('persistence',0.),('validation_blend',gain)]:
                p=np.maximum(known[te]+g*changes,0)
                m=metrics(p,target[te],target[te]>=threshold)
                for subset,v in m.items():evaluation.append({'source':source_id,'lead_h':lead,'candidate':candidate,'subset':subset,'gain':g,**v})
                for idx,pred in zip(te,p):predictions.append({'source':source_id,'lead_h':lead,'candidate':candidate,'origin':iso(t[idx]),'target_time':iso(t[idx]+lead*3600),'actual_m3_s':float(target[idx]*1000),'forecast_m3_s':float(pred*1000),'high_flow':bool(target[idx]>=threshold)})
            fm=ridge_fit(F,delta,final,alpha,w);frozen[f'{source_id}:{lead}']={k:(v.tolist() if isinstance(v,np.ndarray) else float(v)) for k,v in fm.items()}
            change=ridge_predict(fm,NF);forecast=max(0,latest+change)*1000
            stored=float(saved[source_id,lead]['forecast_m3_s'])
            if abs(forecast-stored)>1e-5:raise ValueError(f'Reproduction mismatch: {source_id}/{lead}: {forecast-stored}')
            contrib=attribution(fm,NF,names)
            if abs(sum(v['contribution_m3_s'] for v in contrib)+fm['intercept']*1000-change*1000)>1e-7:raise ValueError('Attribution does not sum to model output')
            for r in contrib:decomposition.append({'source':source_id,'lead_h':lead,**r})
            for r in outside_training_range(F[final],NF,names):outliers.append({'source':source_id,'lead_h':lead,**r})
            current.append({'source':source_id,'lead_h':lead,'known_m3_s':latest*1000,'ridge_m3_s':forecast,'saved_reference_m3_s':stored,'reproduction_error_m3_s':forecast-stored,'training_max_flow_m3_s':trainingmax*1000,'above_training_max':forecast>trainingmax*1000,'blend_gain':gain,'blend_candidate_m3_s':max(0,latest+gain*change)*1000,'persistence_m3_s':latest*1000,'intercept_m3_s':float(fm['intercept']*1000)})
    for name,value in [('selection',selection),('evaluation',evaluation),('current',current),('contributions',decomposition),('retrospective-predictions',predictions)]:savecsv(out/f'{name}.csv',value)
    if outliers:savecsv(out/'out-of-training-range.csv',outliers)
    dump(out/'frozen-ridge-models.json',frozen)
    code=[Path(__file__),ROOT/'scripts/hydro_flow_diagnostics.py',ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_hourly_models.py',ROOT/'scripts/hydro_routing_fit.py']
    (out/'code').mkdir()
    for p in code:(out/'code'/p.name).write_bytes(p.read_bytes())
    inputs=[BASE/'dados-roteamento.npz',BASE/'telemetria-latencia.npz',source/'dados-roteamento.npz',source/'telemetria-latencia.npz',source/'previsao-vazoes-montante.csv',*code]
    dump(out/'audit.json',{'source_snapshot':str(source),'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'development_validation':'2025-10-01 to 2026-07-01 exclusive targets','development_test':'2026-07-01 to 2026-09-21 exclusive targets; previously inspected, not new independent holdout','high_flow_definition':'95th percentile of source flow before 2025-10-01; not a flood warning threshold','gain_candidates':[0,.25,.5,.75,1],'selection_score':'validation MAE all + 0.5 * validation MAE high flow','model_promoted':False,'goal_achieved':False,'live_issuance':False,'maximum_reproduction_error_m3_s':max(abs(r['reproduction_error_m3_s']) for r in current),'out_of_range_feature_rows':len(outliers)})
    lines=['# Auditoria da vazão de montante','','Nenhuma referência ou emissão foi substituída. Esta comparação usa períodos de desenvolvimento já examinados; não comprova ganho independente nem 98%.','','| Fonte | Prazo | Ridge atual | Mistura candidata | Máximo histórico treino | Ganho |','|---|---:|---:|---:|---:|---:|']
    for r in current:
        if r['lead_h'] in [0,5,11]:lines.append(f"| {r['source']} | {r['lead_h']}h | {r['ridge_m3_s']:.1f} | {r['blend_candidate_m3_s']:.1f} | {r['training_max_flow_m3_s']:.1f} | {r['blend_gain']:.2f} |")
    lines+=['','Vazões em m³/s. A mistura reduz somente a mudança prevista em relação à vazão conhecida; não impõe limite físico ao rio. Ganho escolhido antes do período de avaliação. Previsões futuras candidatas são diagnósticos locais, não novas emissões.','','Os arquivos de contribuições mostram cada parcela linear, incluindo indicadores de ausência. Faixas HGE de PET/chuva não abrangem a incerteza dessas vazões estimadas.']
    (out/'report.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'output':str(out),'current':current[-1],'out_of_range_rows':len(outliers)}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    with threadpool_limits(limits=2):run(args.source,args.output)
