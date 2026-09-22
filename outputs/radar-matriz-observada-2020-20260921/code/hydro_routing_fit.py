"""Causal, chronological calibration of propagation and direct hourly forecasts."""
from pathlib import Path
from datetime import datetime,timedelta
import json,csv,collections
import numpy as np
from scipy.linalg import solve
from scipy.signal import find_peaks
from scipy.optimize import least_squares
from hydro_routing_data import OUT,RAW,TZ,epoch,iso,savecsv

def shift(a,steps):
    if not steps:return a.copy()
    out=np.full_like(a,np.nan)
    if steps>0:out[steps:]=a[:-steps]
    else:out[:steps]=a[-steps:]
    return out
def avg(a,n):
    # Strict causal rolling windows; no replacing missing precipitation with dry weather.
    out=np.full_like(a,np.nan);s=np.r_[0,np.cumsum(np.nan_to_num(a))];count=np.r_[0,np.cumsum(np.isfinite(a))]
    vv=(s[n:]-s[:-n])/n;valid=count[n:]-count[:-n]==n;out[n-1:]=np.where(valid,vv,np.nan);return out
def fit_ridge(X,y,train,apply,alpha,weights=None):
    med=np.array([np.nanmedian(X[train,j]) if np.isfinite(X[train,j]).any() else 0 for j in range(X.shape[1])])
    def fill(a):return np.column_stack([np.where(np.isfinite(a),a,med),~np.isfinite(a)])
    x=fill(X[train]);mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale<1e-8]=1;x=(x-mean)/scale
    target=y[train];w=np.ones(len(train)) if weights is None else weights[train];w=w/w.mean();ym=np.sum(w*target)/w.sum()
    gram=np.einsum('ni,n,nj->ij',x,w,x,optimize=False);rhs=np.einsum('ni,n,n->i',x,w,target-ym,optimize=False)
    beta=solve(gram+alpha*np.eye(x.shape[1]),rhs,assume_a='pos')
    z=(fill(X[apply])-mean)/scale;p=np.einsum('ni,i->n',z,beta,optimize=False)+ym
    assert np.isfinite(p).all();return p
def metric(pred,true):
    e=pred-true;return {'mae_m':float(np.mean(abs(e))),'rmse_m':float(np.sqrt(np.mean(e**2))),'bias_m':float(np.mean(e)),'p90_abs_m':float(np.quantile(abs(e),.9)),'max_abs_m':float(np.max(abs(e))),'n':len(e)}
def prepare():
    data=dict(np.load(OUT/'telemetria.npz'));times=data.pop('times');origin=times[-1]
    # Hourly calibration uses same quarter-hour phase as the actual forecast origin.
    phase=int((origin-times[0])//900)%4;ix=np.arange(phase,len(times),4);times=times[ix];data={k:v[ix] for k,v in data.items()}
    H=data['86510000:H'];Q=data['86510000:Q'];n=len(H);names=[];columns=[];groups={}
    def add(group,name,values):
        groups.setdefault(group,[]).append(len(columns));names.append(name);columns.append(values)
    # Levels remain in their own vertical reference; changes and relationships are calibrated.
    for code in ['86510000','86472000','86472600','86500000']:
        a=data[code+':H'];add('levels',code+':H',a)
        for lag in [1,2,4,8]:add('levels',code+':dH'+str(lag),(a-shift(a,lag))/lag)
    for plant in ['julho','monte','castro']:
        a=data[plant+':Q'];trans=np.power(np.maximum(a,0)/1000,.6)
        add('reservoir',plant+':Q',a/1000);add('reservoir',plant+':Q06',trans)
        for lag in [1,2,4,8]:add('reservoir',plant+':dQ06'+str(lag),(trans-shift(trans,lag))/lag)
        inflow=data[plant+':I']/1000;add('reservoir',plant+':I',inflow);add('reservoir',plant+':storage',inflow-a/1000)
    for code in ['86160000','86298000','86403000','86505500']:
        a=data[code+':Q'];a=np.where(a<20000,a,np.nan);add('tributaries',code+':Q06',np.power(a/1000,.6))
        add('tributaries',code+':dQ3',(a-shift(a,3))/3000)
    for group in ['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']:
        p=data[group+':P']
        for window in [1,3,6,12,24]:add('rain',group+':P'+str(window),avg(p,window)*window)
        for lag in [3,6,12]:add('rain',group+':P3lag'+str(lag),shift(avg(p,3)*3,lag))
        wet=avg(p,48)*48;add('rain',group+':antecedent',wet)
        add('rain',group+':wet_interaction',avg(p,3)*3*np.minimum(wet/50,3))
    X=np.column_stack(columns)
    configs={'nivel_montante':groups['levels'],'nivel_barragens':groups['levels']+groups['reservoir'],
             'integrado':sum(groups.values(),[]),'barragens_chuva':groups['levels']+groups['reservoir']+groups['rain']}
    return times,data,H,Q,X,names,configs
def propagation(times,data,H):
    # Independent event matching: downstream prominent peak, preceding upstream peak.
    valid=np.isfinite(H);filled=np.where(valid,H,-999);peaks,_=find_peaks(filled,prominence=1.5,distance=36)
    events=[];lagrows=[];summary=[]
    sources={'Linha José Júlio':'86472000:H','Santa Tereza':'86472600:H','Passo Carreiro':'86500000:H','14 de Julho':'julho:Q','Monte Claro':'monte:Q','Castro Alves':'castro:Q','Passo Tainhas':'86160000:H'}
    distances={r['id']:float(r['distancia_rede_km']) for r in csv.DictReader((OUT/'estacoes-conectividade.csv').open())}
    km={'Linha José Júlio':distances['86472000'],'Santa Tereza':distances['86472600'],'Passo Carreiro':distances['86500000'],'14 de Julho':distances['86471000'],'Passo Tainhas':distances['86160000']}
    for name,key in sources.items():
        a=data[key];dmax=30 if 'Carreiro' in name else 60 if 'Tainhas' in name else 24;prom=600 if key.endswith(':Q') else .7
        ap,_=find_peaks(np.where(np.isfinite(a),a,-999),prominence=prom,distance=12)
        lags=[]
        for pi in peaks:
            if H[pi]<7 or times[pi]>=epoch('2026-09-21T00:00:00'):continue
            candidates=[j for j in ap if 0<pi-j<=dmax]
            if not candidates:continue
            # Largest upstream event in causal window, with all choices recorded for audit.
            pj=max(candidates,key=lambda j:a[j]);lag=pi-pj;lags.append(lag)
            events.append({'source':name,'source_peak':iso(times[pj]),'source_value':float(a[pj]),'mucum_peak':iso(times[pi]),'mucum_level':float(H[pi]),'lag_h':int(lag),'distance_km':km.get(name),'wave_speed_km_h':km[name]/lag if name in km else None})
        # Cross-correlation on first differences, restricted to active event conditions.
        da=a-shift(a,1);dh=H-shift(H,1)
        for lag in range(0,dmax+1):
            x=shift(da,lag);mask=np.isfinite(x)&np.isfinite(dh)&(times<epoch('2026-07-01T00:00:00'))&((abs(dh)>.08)|(H>7))
            corr=float(np.corrcoef(x[mask],dh[mask])[0,1]) if mask.sum()>30 else None
            lagrows.append({'source':name,'lag_h':lag,'correlation_differences':corr,'n':int(mask.sum())})
        best=max([r for r in lagrows if r['source']==name and r['correlation_differences'] is not None],key=lambda r:r['correlation_differences'])
        summary.append({'source':name,'peak_pairs':len(lags),'median_peak_lag_h':float(np.median(lags)) if lags else None,'p10_peak_lag_h':float(np.quantile(lags,.1)) if lags else None,'p90_peak_lag_h':float(np.quantile(lags,.9)) if lags else None,'calibration_correlation_lag_h':best['lag_h'],'calibration_correlation':best['correlation_differences'],'distance_km':km.get(name),
                        'interpretation':'Atraso da onda de cheia; nao velocidade de uma parcela de agua. Picos tributarios podem nao pertencer ao mesmo pulso.'})
    savecsv(OUT/'eventos-propagacao.csv',events);savecsv(OUT/'correlacao-propagacao.csv',lagrows);(OUT/'tempos-propagacao.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print('PROPAGATION',summary,flush=True)
def run():
    times,data,H,Q,X,names,configs=prepare();propagation(times,data,H)
    # Chronological selection: Jan-May training, June validation. July-Sep20 untouched test.
    tr_end=epoch('2026-06-01T00:00:00');val_end=epoch('2026-07-01T00:00:00');test_end=epoch('2026-09-21T00:00:00')
    origin=times[-1];evals=[];preds=[];alltest=[];candidates=[]
    core=np.all(np.isfinite(X[:,:20]),axis=1)&np.isfinite(H)
    for h in range(1,7):
        target=shift(H,-h);delta=target-H;valid=core&np.isfinite(target)
        tr=np.where(valid&(times+h*3600<tr_end))[0];va=np.where(valid&(times>=tr_end)&(times+h*3600<val_end))[0];te=np.where(valid&(times>=val_end)&(times+h*3600<test_end))[0]
        today=np.where(valid&(times>=test_end))[0]
        # Weight observations with real upcoming rapid rises during training only.
        weights=1+2*(abs(delta)>=1)+2*(target>=9)
        selected={}
        for model,features in configs.items():
            xx=X[:,features];opts=[]
            for alpha in [10.,100.,1000.]:
                for weighted in [False,True]:
                    pp=fit_ridge(xx,delta,tr,va,alpha,weights if weighted else None)+H[va]
                    err=abs(pp-target[va]);rise=(target[va]-H[va])>=1;high=target[va]>=9
                    score=np.mean(err)+(.5*np.mean(err[rise]) if rise.any() else 0)+(.5*np.mean(err[high]) if high.any() else 0)
                    opts.append((score,alpha,weighted))
            score,alpha,weighted=min(opts);train=np.r_[tr,va];p=fit_ridge(xx,delta,train,te,alpha,weights if weighted else None)+H[te]
            # Assimilate the last realized forecast error with causal exponential decay.
            full=np.where(valid&(times>=val_end))[0];raw=fit_ridge(xx,delta,train,full,alpha,weights if weighted else None)+H[full];known={j:target[j]-raw[k] for k,j in enumerate(full)}
            corrected=[]
            for k,j in enumerate(te):
                prior=[q for q in range(max(0,j-h-2),j-h+1) if q in known]
                correction=np.mean([known[q] for q in prior]) if prior else 0
                corrected.append(p[k]+.5*correction)
            for assimilate,pp in [(False,p),(True,np.array(corrected))]:
                label=model+('_assimilado' if assimilate else '')
                m=metric(pp,target[te]);rise=target[te]-H[te]>=1;high=target[te]>=9
                m.update({'model':label,'h':h,'validation_score':float(score),'alpha':alpha,'weighted':weighted,'n_train':len(tr),'n_validation':len(va),'rapid_rise_mae_m':float(np.mean(abs(pp[rise]-target[te][rise]))) if rise.any() else None,'rapid_rise_n':int(rise.sum()),'high_water_mae_m':float(np.mean(abs(pp[high]-target[te][high]))) if high.any() else None,'high_water_n':int(high.sum())})
                evals.append(m)
                for k,j in enumerate(te):alltest.append({'model':label,'h':h,'origin':iso(times[j]),'target_time':iso(times[j]+h*3600),'origin_level_m':H[j],'observed_m':target[j],'predicted_m':pp[k]})
            # Final fit uses all historical observed targets BEFORE today; today's event held out.
            finaltrain=np.where(valid&(times+h*3600<test_end))[0]
            current=fit_ridge(xx,delta,finaltrain,np.array([len(times)-1]),alpha,weights if weighted else None)[0]+H[-1]
            recent=np.where(valid&(times>=test_end))[0];recentpred=fit_ridge(xx,delta,finaltrain,recent,alpha,weights if weighted else None)+H[recent] if len(recent) else np.array([])
            recenterrs={j:target[j]-recentpred[k] for k,j in enumerate(recent)}
            prior=[j for j in range(len(times)-1-h-2,len(times)-h) if j in recenterrs];correction=.5*np.mean([recenterrs[j] for j in prior]) if prior else 0
            for assimilated,fc in [(False,current),(True,current+correction)]:
                candidates.append({'h':h,'model':model+('_assimilado' if assimilated else ''),'forecast_m':float(fc),'origin':iso(origin),'time':iso(origin+h*3600),'validation_score':float(score),'correction_m':float(correction if assimilated else 0)})
            for k,j in enumerate(recent):alltest.append({'model':model+'_today','h':h,'origin':iso(times[j]),'target_time':iso(times[j]+h*3600),'origin_level_m':H[j],'observed_m':target[j],'predicted_m':recentpred[k]})
        # Baselines on the exact same independent origins.
        for name,p in [('persistencia',H[te]),('tendencia2h',H[te]+h*X[te,2])]:
            m=metric(p,target[te]);rise=target[te]-H[te]>=1;high=target[te]>=9
            m.update({'model':name,'h':h,'validation_score':None,'alpha':None,'weighted':False,'n_train':0,'n_validation':0,'rapid_rise_mae_m':float(np.mean(abs(p[rise]-target[te][rise]))),'rapid_rise_n':int(rise.sum()),'high_water_mae_m':float(np.mean(abs(p[high]-target[te][high]))),'high_water_n':int(high.sum())});evals.append(m)
        print('HORIZON',h,[(r['model'],round(r['forecast_m'],2)) for r in candidates if r['h']==h],flush=True)
    savecsv(OUT/'avaliacao-direta.csv',evals);savecsv(OUT/'candidatos-previsao.csv',candidates);savecsv(OUT/'teste-direto.csv',alltest)
    (OUT/'model-features.json').write_text(json.dumps({'names':names,'configs':configs,'origin':iso(origin),'origin_level_m':float(H[-1]),'train_end':iso(tr_end),'validation_end':iso(val_end),'test_end':iso(test_end),'rain_current':{g:float(data[g+':P'][-1]) if np.isfinite(data[g+':P'][-1]) else None for g in ['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']}},ensure_ascii=False,indent=2))
if __name__=='__main__':run()
