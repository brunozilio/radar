"""Forecast clock hours with explicit source ages and latency-matched hindcasts."""
import csv,json,re,sys,os,xml.etree.ElementTree as ET
from datetime import datetime
import numpy as np
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingRegressor
from hydro_precision_audit import OUT,PREV,HORIZON,observed_rain_windows
from hydro_routing_data import load_ana,epoch,iso,number,savecsv,TZ
from hydro_model import asof
from hydro_routing_fit import shift,fit_ridge,metric
from hydro_forecast import selection_score

def select_horizon(forecasts):
    # Choose one family for the whole hydrograph. Switching the winning family
    # independently at each lead can create a fictitious spike or recession.
    scores={name:float(np.mean([float(f['validation_score']) for f in forecasts if f['model']==name])) for name in {f['model'] for f in forecasts}}
    chosen=min(scores,key=scores.get)
    return sorted([f for f in forecasts if f['model']==chosen],key=lambda f:float(f['lead_h'])),scores

def merged(code):
    if os.environ.get('HYDRO_HISTORY_DIR'):
        return dict(np.load(Path(os.environ['HYDRO_HISTORY_DIR'])/f'ana-{code}.npz'))
    d=load_ana(code);mapping={t:[h,q,r,c] for t,h,q,r,c in zip(d['times'],d['level'],d['flow'],d['rain'],d['counter'])};path=OUT/'raw'/f'ana-{code}-fresh.xml'
    for el in ET.parse(path).getroot().iter():
        if not el.tag.endswith('DadosHidrometereologicos'):continue
        r={x.tag.split('}')[-1]:x.text for x in el};ts=epoch(r['DataHora']);v=[]
        for field,qc in [('NivelFinal','CQ_NivelFinal'),('VazaoFinal','CQ_VazaoFinal'),('ChuvaFinal','CQ_ChuvaFinal'),('ChuvaAcumAdotada','CQ_ChuvaAcumAdotada')]:v.append(number(r.get(field)) if r.get(qc) in ['Dado aprovado',None] else np.nan)
        v[0]/=100
        if v[2]>150:v[2]=np.nan
        mapping[ts]=v # Revised missing/invalid data must replace older values too.
    ts=np.array(sorted(mapping));a=np.array([mapping[t] for t in ts]);return {'times':ts,'level':a[:,0],'flow':a[:,1],'rain':a[:,2],'counter':a[:,3]}

def prepare_current():
    old=dict(np.load(PREV/'telemetria.npz'));origin=epoch(os.environ.get('HYDRO_ORIGIN','2026-09-21T14:00:00'));grid=np.arange(old['times'][0],origin+1,900);rainweights=json.loads((PREV/'chuva-pesos.json').read_text());codes=sorted({c for g in rainweights for c in g['weights']});data={c:merged(c) for c in codes};raw={};delayed={};ages=[];windows={}
    for code,d in data.items():
        for key,field in [('H','level'),('Q','flow')]:
            valid=(d['times']<=origin)&np.isfinite(d[field]);ix=np.where(valid)[0]
            if not len(ix):raw[code+':'+key]=np.full(len(grid),np.nan);delayed[code+':'+key]=np.full(len(grid),np.nan);continue
            latest=d['times'][ix[-1]];lag=origin-latest;raw[code+':'+key]=asof(d['times'],d[field],grid,max_age=0)
            delayed[code+':'+key]=asof(d['times'],d[field],grid-lag,max_age=900)
            if key=='H':ages.append({'source':code,'last_time':iso(latest),'delay_minutes':lag/60,'value':float(d[field][ix[-1]])})
        valid=(d['times']<=origin)&np.isfinite(d['rain']);latest=d['times'][np.where(valid)[0][-1]];lag=origin-latest
        # Move measurement availability, not measured rainfall itself. Integrals use
        # actual interval endpoints and only increments published under this stress delay.
        base=observed_rain_windows(d['times'],d['rain'],grid)
        delaysteps=int(lag/900);windows[code]={w:(shift(v[0],delaysteps),shift(v[1],delaysteps)) for w,v in base.items()}
    for plant in ['julho','monte','castro']:
        if os.environ.get('HYDRO_HISTORY_DIR'):
            history=dict(np.load(Path(os.environ['HYDRO_HISTORY_DIR'])/f'ceran-{plant}.npz'))
            valid=(history['times']<=origin)&np.isfinite(history['Q'])
            if not valid.any():raise ValueError('No admissible historical CERAN flow')
            last=history['times'][np.where(valid)[0][-1]];lag=origin-last
            for key in ['Q','I']:
                raw[plant+':'+key]=asof(history['times'],history[key],grid,max_age=5400)
                delayed[plant+':'+key]=asof(history['times'],history[key],grid-lag,max_age=5400)
            ages.append({'source':plant,'last_time':iso(last),'delay_minutes':lag/60,'value':float(history['Q'][np.where(valid)[0][-1]])})
            continue
        text=(OUT/'raw'/f'ceran-{plant}-fresh.html').read_text();fresh={}
        for row in re.findall(r'<tr>(.*?)</tr>',text,re.S):
            td=re.findall(r'<td>(.*?)</td>',row,re.S)
            if len(td)==8:
                ts=datetime.strptime(td[0],'%d/%m/%Y %H:%M:%S').replace(tzinfo=TZ).timestamp();fresh[ts]={'Q':number(td[7]),'I':number(td[3])}
        last=max(t for t in fresh if t<=origin);lag=origin-last
        for key in ['Q','I']:
            allvalues={t:v for t,v in zip(old['times'],old[plant+':'+key])};allvalues.update({t:r[key] for t,r in fresh.items()});ts=np.array(sorted(allvalues));vv=np.array([allvalues[t] for t in ts]);raw[plant+':'+key]=asof(ts,vv,grid,max_age=5400);delayed[plant+':'+key]=asof(ts,vv,grid-lag,max_age=5400)
        ages.append({'source':plant,'last_time':iso(last),'delay_minutes':lag/60,'value':fresh[last]['Q']})
    # Rain windows end at the last admissible observation time of each station;
    # the extra trailing delay is represented by coverage and ages, not new rain.
    for group in rainweights:
        name=group['group']
        for w in [1,3,6,12,24,48]:
            amount=sum(weight*np.nan_to_num(windows[c][w][0],nan=0) for c,weight in group['weights'].items());cover=sum(weight*np.nan_to_num(windows[c][w][1],nan=0) for c,weight in group['weights'].items());delayed[name+f':P{w}']=np.where(cover>=.5,amount,np.nan);delayed[name+f':C{w}']=cover
    np.savez_compressed(OUT/'telemetria-latencia.npz',times=grid,**{'raw:'+k:v for k,v in raw.items()},**delayed);savecsv(OUT/'idades-fontes.csv',ages)
    return grid,raw,delayed,ages

def telemetry_features(t,raw,d):
    """Shared feature definition for the historical audit and live runner."""
    cols=[];names=[];rainidx=[]
    def add(name,v):names.append(name);cols.append(v)
    base=d['86510000:H'];truth=raw['86510000:H']
    for code in ['86510000','86472000','86472600','86500000']:
        v=d[code+':H'];add(code+':H',v)
        for hours in [.5,1,2,4,8]:add(code+f':dH{hours}',(v-shift(v,int(hours*4)))/hours)
    for plant in ['julho','monte','castro']:
        q=d[plant+':Q']/1000;v=np.maximum(q,0)**.6;add(plant+':Q06',v);add(plant+':Q',q);add(plant+':I',d[plant+':I']/1000)
        for hours in [1,2,4,8]:add(plant+f':dQ{hours}',(v-shift(v,int(hours*4)))/hours)
    for group in ['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']:
        for w in [1,3,6,12,24,48]:
            rainidx.append(len(cols));add(group+f':P{w}',d[group+f':P{w}']);add(group+f':C{w}',d[group+f':C{w}'])
        for lag in [3,6,12]:rainidx.append(len(cols));add(group+f':P3lag{lag}',shift(d[group+':P3'],lag*4))
    X=np.column_stack(cols);phase=np.arange(0,len(t),4);times=t[phase];X=X[phase];H=base[phase];log=X.copy();log[:,rainidx]=np.log1p(np.maximum(log[:,rainidx],0))
    return times, X, H, truth, phase, log

def run():
    t,raw,d,ages=prepare_current()
    times,X,H,truth,phase,log=telemetry_features(t,raw,d)
    weather=[]
    for model in ['gfs_seamless','ecmwf_ifs025','icon_global']:
        path=OUT/'nwp-historical-icon.json' if model=='icon_global' else PREV/'raw'/f'chuva-previsao-historica-{model}.json'
        for location in json.loads(path.read_text()):
            wt=np.array([epoch(v) for v in location['hourly']['time']]);wv=np.array([v if v is not None else np.nan for v in location['hourly']['precipitation_previous_day1']])
            for window in range(3,HORIZON+1,3):
                vals=[]
                for when in times:
                    eligible=(wt>when)&(wt<=when+window*3600);value=wv[eligible];vals.append(float(value.sum()) if len(value)==window and np.isfinite(value).all() else np.nan)
                weather.append(vals)
    weatherX=np.column_stack([X,np.column_stack(weather)])
    start=epoch('2025-10-01T00:00:00');valend=epoch('2026-07-01T00:00:00');today=epoch('2026-09-21T00:00:00');preds=[];evals=[];forecasts=[];selected=[]
    if '--weather-only' in sys.argv:
        preds=list(csv.DictReader((OUT/'retrospectivas-latencia.csv').open()));evals=list(csv.DictReader((OUT/'avaliacao-latencia.csv').open()));forecasts=list(csv.DictReader((OUT/'candidatos-latencia.csv').open()))
        for f in forecasts:
            for key in ['lead_h','forecast_m','lower_m','upper_m','validation_score','test_mae_m','today_mae_m','today_n','today_p90_abs_m']:f[key]=float(f[key])
    for h in range(HORIZON):
        lead=float(h+1);target=shift(truth,-int(lead*4))[phase];valid=np.isfinite(H)&np.isfinite(target)&np.all(np.isfinite(X[:,:24]),axis=1);delta=target-H
        tr=np.where(valid&(times+lead*3600<start))[0];va=np.where(valid&(times>=start)&(times+lead*3600<valend))[0];te=np.where(valid&(times>=valend)&(times+lead*3600<today))[0];td=np.where(valid&(times>=today))[0];final=np.where(valid&(times+lead*3600<today))[0];w=1+2*(abs(delta)>=1)+2*(target>=9)
        for name in (['arvores_previsao_chuva'] if '--weather-only' in sys.argv else ['linear_log','arvores','arvores_previsao_chuva']):
            tree=name.startswith('arvores');xx=weatherX if name=='arvores_previsao_chuva' else X if tree else log
            def fit(train,apply,param):
                if tree:
                    leaf,loss=param;model=HistGradientBoostingRegressor(max_iter=180,max_leaf_nodes=leaf,min_samples_leaf=35,learning_rate=.055,l2_regularization=10,loss=loss,early_stopping=False,random_state=57);model.fit(xx[train],delta[train],sample_weight=w[train]);return model.predict(xx[apply])+H[apply]
                alpha,weighted=param;return fit_ridge(xx,delta,train,apply,alpha,w if weighted else None)+H[apply]
            params=[(n,loss) for n in [7,15] for loss in ['squared_error','absolute_error']] if tree else [(a,b) for a in [10.,100.,1000.] for b in [False,True]]
            options=[]
            for param in params:
                p=fit(tr,va,param);options.append((selection_score(p,target[va],H[va]),param))
            score,param=min(options);testp=fit(np.r_[tr,va],te,param);apply=np.r_[td,len(times)-1];current=fit(final,apply,param)
            for label,indices,pp in [('test',te,testp),('today',td,current[:-1])]:
                m=metric(pp,target[indices]);m.update({'model':name,'lead_h':lead,'phase':label,'score':score});evals.append(m)
                for j,p in zip(indices,pp):preds.append({'model':name,'lead_h':lead,'origin':iso(times[j]),'target_time':iso(times[j]+lead*3600),'base_m':H[j],'actual_m':target[j],'forecast_m':p,'phase':label})
            similar=((testp-H[te])>=.15*lead)|(H[te]>=7);err=abs(testp-target[te]);hist90=float(np.quantile(err[similar],.9));recent=abs(current[:-1]-target[td]);recent90=float(np.quantile(recent,.9));width=max(hist90,recent90)
            f={'model':name,'lead_h':lead,'origin':iso(times[-1]),'time':iso(times[-1]+lead*3600),'forecast_m':float(current[-1]),'lower_m':float(current[-1]-width),'upper_m':float(current[-1]+width),'validation_score':score,'parameters':str(param),'test_mae_m':evals[-2]['mae_m'],'today_mae_m':evals[-1]['mae_m'],'today_n':len(td),'today_p90_abs_m':recent90};forecasts.append(f)
            print(lead,name,'CURRENT',round(f['forecast_m'],2),'test',round(f['test_mae_m'],3),'today',round(f['today_mae_m'],3),'val',round(score,3),flush=True)
        selected.append(min([f for f in forecasts if f['lead_h']==lead],key=lambda r:r['validation_score']))
        savecsv(OUT/'avaliacao-latencia.csv',evals);savecsv(OUT/'retrospectivas-latencia.csv',preds);savecsv(OUT/'candidatos-latencia.csv',forecasts);savecsv(OUT/'previsao-atualizada.csv',selected)
    selected,scores=select_horizon(forecasts);savecsv(OUT/'previsao-atualizada.csv',selected)
    (OUT/'previsao-atualizada.json').write_text(json.dumps({'origin':iso(times[-1]),'last_observed_mucum':next(a for a in ages if a['source']=='86510000'),'issued_at':datetime.now(TZ).isoformat(),'forecast':selected,'family_validation_scores':scores,'selection':'One family across the full horizon, chosen by mean historical validation score only.','source_ages':ages,'latency_note':'Fixed current source ages imposed in retrospective inputs; availability stress test, not historical publication-log reconstruction.'},ensure_ascii=False,indent=2))

if __name__=='__main__':run()
