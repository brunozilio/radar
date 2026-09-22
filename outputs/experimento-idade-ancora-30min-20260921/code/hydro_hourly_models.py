"""Frozen Radar calibration with fresh inference; no current-event parameter search."""
from __future__ import annotations
import ast, csv, json, pickle
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from hydro_hourly_collect import BASE, ROOT, dump
from hydro_routing_fit import shift, fit_ridge
from hydro_routing_data import epoch, iso, savecsv

GROUPS=['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']
MODELS=['gfs_seamless','ecmwf_ifs025','icon_global']
HIST=ROOT/'outputs/mucum-propagacao-2026-09-21'

def historical_weather():
    return [json.loads((BASE/'nwp-historical-icon.json' if model=='icon_global' else HIST/'raw'/f'chuva-previsao-historica-{model}.json').read_text()) for model in MODELS]

def features(z, weather, current=False):
    columns=[]
    for code in ['86510000','86472000','86472600','86500000']:
        v=z[code+':H'];columns.append(v)
        for h in [.5,1,2,4,8]:columns.append((v-shift(v,int(h*4)))/h)
    for plant in ['julho','monte','castro']:
        q=z[plant+':Q']/1000;v=np.maximum(q,0)**.6
        columns.extend([v,q,z[plant+':I']/1000])
        for h in [1,2,4,8]:columns.append((v-shift(v,int(h*4)))/h)
    for group in GROUPS:
        for w in [1,3,6,12,24,48]:columns.extend([z[group+f':P{w}'],z[group+f':C{w}']])
        for lag in [3,6,12]:columns.append(shift(z[group+':P3'],lag*4))
    phase=np.array([len(z['times'])-1]) if current else np.arange(0,len(z['times']),4)
    X=np.column_stack(columns)[phase];times=z['times'][phase]
    wc=[]
    for model in weather:
        for location in model:
            h=location['hourly']; key='precipitation' if current else 'precipitation_previous_day1'
            lookup={epoch(t):v for t,v in zip(h['time'],h[key])}
            for window in range(3,13,3):
                vals=np.array([[lookup.get(t+k*3600,np.nan) for k in range(1,window+1)] for t in times],dtype=float)
                wc.append(vals.sum(axis=1))
    return times, np.column_stack([X,*wc]), z['86510000:H'][phase]

def upstream_features(z, times):
    ix=np.searchsorted(z['times'],times);cols=[]
    for key in ['julho:Q','julho:I','monte:Q','monte:I','castro:Q','castro:I','86500000:Q']:
        a=z[key][ix]/1000;cols.extend([a,a-shift(a,1),(a-shift(a,3))/3,(a-shift(a,6))/6])
    for group in GROUPS:
        for w in [3,6,12,24,48]:cols.append(z[group+f':P{w}'][ix]/100)
    return np.column_stack(cols)

def statistical(out):
    frozen=dict(np.load(BASE/'telemetria-latencia.npz'));z=dict(np.load(out/'telemetria-latencia.npz'))
    t,X,H=features(frozen,historical_weather())
    weather=[json.loads((out/'raw'/f'weather-{m}.json').read_text()) for m in MODELS]
    nt,NX,NH=features(z,weather,True)
    assert np.isfinite(NX[:,:24]).all() and np.isfinite(NX[:, -60:]).all()
    selected=json.loads((BASE/'previsao-atualizada.json').read_text()); forecasts=[];reproduction=[]; fitted=[]
    truth=frozen['raw:86510000:H'];phase=np.arange(0,len(truth),4)
    for row in selected['forecast']:
        lead=int(row['lead_h']);target=shift(truth,-lead*4)[phase];delta=target-H
        valid=np.isfinite(H)&np.isfinite(target)&np.isfinite(X[:,:24]).all(axis=1)
        train=np.where(valid&(t+lead*3600<epoch('2026-09-21T00:00:00')))[0]
        w=1+2*(abs(delta)>=1)+2*(target>=9)
        leaf,loss=ast.literal_eval(row['parameters'])
        model=HistGradientBoostingRegressor(max_iter=180,max_leaf_nodes=leaf,min_samples_leaf=35,learning_rate=.055,l2_regularization=10,loss=loss,early_stopping=False,random_state=57)
        model.fit(X[train],delta[train],sample_weight=w[train]); fitted.append(model)
        replay=float(model.predict(X[-1:])[0]+H[-1]); error=replay-row['forecast_m']
        reproduction.append({'lead_h':lead,'original_m':row['forecast_m'],'reproduced_m':replay,'difference_m':error})
        if abs(error)>1e-7:raise ValueError(f'Frozen Radar reconstruction mismatch: {lead}h {error}')
        prediction=float(model.predict(NX)[0]+NH[0])
        forecasts.append({'model':row['model'],'lead_h':lead,'origin':iso(nt[0]),'time':iso(nt[0]+lead*3600),'forecast_m':prediction,'validation_score':row['validation_score'],'parameters':row['parameters']})
        print('Radar',lead,round(prediction,3),flush=True)
    with (out/'frozen-radar-models.pkl').open('wb') as f:pickle.dump(fitted,f)
    savecsv(out/'reproducao-calibracao.csv',reproduction)
    savecsv(out/'previsao-atualizada.csv',forecasts)
    ages=list(csv.DictReader((out/'idades-fontes.csv').open()))
    obs=next(a for a in ages if a['source']=='86510000');obs['value']=float(obs['value']);obs['delay_minutes']=float(obs['delay_minutes'])
    dump(out/'previsao-atualizada.json',{'origin':iso(nt[0]),'last_observed_mucum':obs,'forecast':forecasts,'family_validation_scores':selected['family_validation_scores'],'selection':selected['selection'],'training_cutoff_exclusive':'2026-09-21T00:00:00-03:00','parameters_frozen':True,'source_ages':ages})
    old=dict(np.load(BASE/'dados-roteamento.npz'));new=dict(np.load(out/'dados-roteamento.npz'))
    F=upstream_features(frozen,old['times']);NF=upstream_features(z,new['times'])[-1:]
    together=np.vstack([F,NF]); records=[]
    for row in csv.DictReader((BASE/'previsao-vazoes-montante.csv').open()):
        source=row['source'];lead=int(row['lead_h']);alpha=float(row['alpha']);key='julho:Q' if source=='julho' else '86500000:Q'
        known=frozen[key][np.searchsorted(frozen['times'],old['times'])]/1000
        target=shift(old[source],-lead);delta=target-known
        train=np.where(np.isfinite(target)&np.isfinite(known)&(old['times']+lead*3600<epoch('2026-09-21T00:00:00')))[0]
        value=fit_ridge(together,np.r_[delta,np.nan],train,np.array([len(F)]),alpha,np.r_[1+2*(target>2),1])[0]
        value=max(0.,value+z[key][-1]/1000)*1000
        records.append({'source':source,'lead_h':lead,'forecast_m3_s':value,'alpha':alpha,'kind':'estimated_future_or_nowcast_not_observed'})
    savecsv(out/'previsao-vazoes-montante.csv',records)

def merged_weather(out):
    origin=epoch(json.loads((out/'run.json').read_text())['reference_time'])
    base_origin=epoch(json.loads((BASE/'previsao-atualizada.json').read_text())['origin'])
    for name,model,hist in zip(['gfs','ecmwf','icon'],MODELS,historical_weather()):
        latest=json.loads((out/'raw'/f'weather-{model}.json').read_text())
        merged=[]
        for before,after in zip(hist,latest):
            assert after['hourly_units']['precipitation']=='mm' and after['utc_offset_seconds']==-10800
            old=before['hourly']; values=dict(zip(old['time'],old['precipitation_previous_day1']))
            for t,v in zip(after['hourly']['time'],after['hourly']['precipitation']):
                if epoch(t)>base_origin:values[t]=v
            times=sorted(values)
            merged.append({**before,'hourly':{'time':times,'precipitation_previous_day1':[values[t] for t in times]},'note':'Compatibility key only: historical baseline through initial reference; fresh model estimates afterwards, not observations. See collection manifest; issuance unavailable.'})
        dump(out/f'hge-weather-{name}.json',merged)


def routing_diagnostic(out):
    # Same frozen kernels as HGE; intentionally auxiliary, not an independent model.
    d=dict(np.load(out/'dados-roteamento.npz'));z=dict(np.load(out/'telemetria-latencia.npz'))
    balance=json.loads((out/'conferencia-balanco.json').read_text());rp=balance['rating_parameters']
    rows=list(csv.DictReader((out/'roteamento-vazao-pesos.csv').open()))
    ws={s:np.array([float(r['weight']) for r in rows if r['source']==s]) for s in ['14 de Julho','Passo Carreiro','chuva incremental']}
    assert abs(ws['14 de Julho'].sum()-1)<1e-6 and abs(ws['Passo Carreiro'].sum()-1)<1e-6 and ws['chuva incremental'].sum()<=1+1e-6
    future={(r['source'],int(r['lead_h'])):float(r['forecast_m3_s']) for r in csv.DictReader((out/'previsao-vazoes-montante.csv').open())}
    t=d['times']; origin=t[-1];lookup=[]
    for name in ['gfs','ecmwf','icon']:
        h=json.loads((out/f'hge-weather-{name}.json').read_text())[0]['hourly'];lookup.append({epoch(a):b for a,b in zip(h['time'],h['precipitation_previous_day1'])})
    def nwp(at):return float(np.nanmean(np.array([m.get(at,np.nan) for m in lookup],dtype=float)))
    rain=d['amount']+np.maximum(1-d['coverage'],0)*np.array([nwp(at) for at in t])
    def flow(lead):
        total=balance['baseflow_1000m3s']*1000
        for s,key,lags in [('julho','14 de Julho',range(1,13)),('carreiro','Passo Carreiro',range(4,25))]:
            for lag,w in zip(lags,ws[key]):
                k=lead-lag; total+=w*(future[s,k] if k>=0 else d[s][len(t)-1+k]*1000)
        for lag,w in enumerate(ws['chuva incremental']):
            k=lead-lag; p=nwp(origin+k*3600) if k>=0 else rain[len(t)-1+k]
            total+=w*p*float(d['area'])/3.6
        return total
    def stage(q):return rp[0]*max(q/1000,0)**rp[1]+rp[2]
    meta=json.loads((out/'previsao-atualizada.json').read_text());obs=meta['last_observed_mucum'];age=(origin-epoch(obs['last_time']))/3600
    baseq=z['86510000:Q'][-1];offset=obs['value']-stage(baseq)
    past=np.array([flow(k) for k in range(-2,1)]) if age else np.array([flow(0)])
    last=np.interp(-age,np.arange(-2,1),past) if age else past[0]
    records=[]
    for row in csv.DictReader((BASE/'roteamento-previsao.csv').open()):
        lead=int(row['h']);tau=float(row['tau_h']);q=flow(lead)+(baseq-last)*np.exp(-(lead+age)/tau)
        if not np.isfinite(q) or q<0:raise ValueError('Nonfinite/negative routed flow')
        records.append({'h':lead,'time':iso(origin+lead*3600),'forecast_m':stage(q)+offset,'tau_h':tau,'diagnostic':'frozen HGE upstream kernels and rating; not refitted legacy routing'})
    savecsv(out/'roteamento-previsao.csv',records)
