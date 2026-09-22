"""Forecast selection using historical rain forecasts and causal error assimilation."""
from pathlib import Path
import json,csv,math,collections
from datetime import datetime
import numpy as np
from hydro_routing_fit import prepare,shift,avg,fit_ridge,metric
from hydro_routing_data import OUT,RAW,TZ,epoch,iso,savecsv

def assimilate(indices,predictions,truth,h,gain):
    residual={j:truth[j]-p for j,p in zip(indices,predictions) if np.isfinite(truth[j])}
    corrections=[]
    for j in indices:
        known=[q for q in range(max(0,j-h-2),j-h+1) if q in residual]
        corrections.append(gain*np.mean([residual[q] for q in known]) if known else 0)
    return predictions+np.array(corrections),np.array(corrections)
def selection_score(pred,true,base):
    err=abs(pred-true);rise=true-base>=1;high=true>=9
    return float(np.mean(err)+(.5*np.mean(err[rise]) if rise.any() else 0)+(.5*np.mean(err[high]) if high.any() else 0))
def weather(times,h):
    columns=[];names=[]
    for model in ['gfs_seamless','ecmwf_ifs025']:
        forecasts=json.loads((RAW/f'chuva-previsao-historica-{model}.json').read_text())
        for group,row in zip(['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas'],forecasts):
            wt=np.array([epoch(t) for t in row['hourly']['time']]);wv=np.array([v if v is not None else np.nan for v in row['hourly']['precipitation_previous_day1']])
            for window in [3,6]:
                vals=[]
                for t in times:
                    # Forecasts at 24h lead were issued at least 18h before this origin.
                    eligible=(wt>t)&(wt<=t+window*3600);v=wv[eligible];vals.append(float(v.sum()) if len(v)==window and np.isfinite(v).all() else np.nan)
                columns.append(vals);names.append(f'{model}:{group}:future{window}h_from24h_lead')
    return np.column_stack(columns),names
def run():
    times,data,H,Q,X,names,configs=prepare();last=len(times)-1
    tr_end=epoch('2025-10-01T00:00:00');val_end=epoch('2026-07-01T00:00:00');today=epoch('2026-09-21T00:00:00')
    # Distributed history bins expose measured propagation rather than a single fixed velocity.
    lagcols=[];lagnames=[]
    for source in ['julho:Q','monte:Q','castro:Q','86472000:H','86472600:H','86500000:H']:
        v=data[source];v=(v/1000)**.6 if source.endswith(':Q') else v
        for lo,hi in [(0,1),(1,3),(3,6),(6,12),(12,24)]:
            lagcols.append(shift(avg(v,hi-lo),lo));lagnames.append(source+f':lag{lo}-{hi}')
    lagX=np.column_stack(lagcols)
    coverX=np.column_stack([data[g+':coverage'] for g in ['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']])
    baseX=np.column_stack([X,coverX]);distributed=np.column_stack([baseX,lagX]);models={'nivel_montante':X[:,configs['nivel_montante']],'nivel_barragens':X[:,configs['nivel_barragens']],'barragens_chuva':baseX[:,configs['barragens_chuva']+list(range(X.shape[1],baseX.shape[1]))],'integrado':baseX,'propagacao_distribuida':distributed}
    NWP,wnames=weather(times,6);models['propagacao_previsao_chuva']=np.column_stack([distributed,NWP])
    core=np.all(np.isfinite(X[:,:20]),axis=1)&np.isfinite(H);evaluations=[];forecast=[];tests=[];audit=[]
    for h in range(1,7):
        target=shift(H,-h);delta=target-H;valid=core&np.isfinite(target)
        tr=np.where(valid&(times+h*3600<tr_end))[0];va=np.where(valid&(times>=tr_end)&(times+h*3600<val_end))[0];te=np.where(valid&(times>=val_end)&(times+h*3600<today))[0]
        todayidx=np.where(valid&(times>=today))[0];weights=1+2*(abs(delta)>=1)+2*(target>=9)
        choices=[]
        for model,xx in models.items():
            opts=[]
            for alpha in [10.,100.,1000.]:
                for weighted in [False,True]:
                    raw=fit_ridge(xx,delta,tr,va,alpha,weights if weighted else None)+H[va]
                    for gain in [0.,.25,.5,1.]:
                        corrected,_=assimilate(va,raw,target,h,gain);score=selection_score(corrected,target[va],H[va]);opts.append((score,alpha,weighted,gain))
            score,alpha,weighted,gain=min(opts);train=np.r_[tr,va]
            validation_raw=fit_ridge(xx,delta,tr,va,alpha,weights if weighted else None)+H[va]
            validation_pred,validation_correction=assimilate(va,validation_raw,target,h,gain)
            for k,j in enumerate(va):tests.append({'model':model,'h':h,'origin':iso(times[j]),'target_time':iso(times[j]+h*3600),'base_m':float(H[j]),'actual_m':float(target[j]),'forecast_m':float(validation_pred[k]),'assimilation_m':float(validation_correction[k]),'phase':'validation'})
            pp=fit_ridge(xx,delta,train,te,alpha,weights if weighted else None)+H[te];pp,cor=assimilate(te,pp,target,h,gain)
            metrics=metric(pp,target[te]);rising=target[te]-H[te]>=1;high=target[te]>=9
            metrics.update({'model':model,'h':h,'validation_score':score,'alpha':alpha,'weighted':weighted,'gain':gain,'train_n':len(tr),'validation_n':len(va),'rapid_rise_n':int(rising.sum()),'rapid_rise_mae_m':float(np.mean(abs(pp[rising]-target[te][rising]))),'high_water_n':int(high.sum()),'high_water_mae_m':float(np.mean(abs(pp[high]-target[te][high])))})
            evaluations.append(metrics)
            for k,j in enumerate(te):tests.append({'model':model,'h':h,'origin':iso(times[j]),'target_time':iso(times[j]+h*3600),'base_m':float(H[j]),'actual_m':float(target[j]),'forecast_m':float(pp[k]),'assimilation_m':float(cor[k]),'phase':'test'})
            finaltrain=np.where(valid&(times+h*3600<today))[0];apply=np.r_[todayidx,last];raw=fit_ridge(xx,delta,finaltrain,apply,alpha,weights if weighted else None)+H[apply];corrected,corr=assimilate(apply,raw,target,h,gain)
            for k,j in enumerate(todayidx):tests.append({'model':model,'h':h,'origin':iso(times[j]),'target_time':iso(times[j]+h*3600),'base_m':float(H[j]),'actual_m':float(target[j]),'forecast_m':float(corrected[k]),'assimilation_m':float(corr[k]),'phase':'today'})
            # Error envelope from similar forecast situations in held-out temporal test.
            similar=((pp-H[te])>=.2*h)|(H[te]>=7);err=target[te]-pp
            historic=err[similar] if similar.sum()>=20 else err
            recent_errors=target[todayidx]-corrected[:-1]
            low=float(np.quantile(historic,.05));highq=float(np.quantile(historic,.95))
            # Recent completed errors expand the envelope; it is NOT a nominal-confidence claim.
            if len(recent_errors):low=min(low,float(np.quantile(recent_errors,.1)));highq=max(highq,float(np.quantile(recent_errors,.9)))
            current=float(corrected[-1]);row={'h':h,'model':model,'origin':iso(times[-1]),'time':iso(times[-1]+h*3600),'forecast_m':current,'raw_forecast_m':float(raw[-1]),'assimilation_m':float(corr[-1]),'gain':gain,'validation_score':score,'lower_error_envelope_m':current+low,'upper_error_envelope_m':current+highq,'historical_similar_n':int(similar.sum()),'recent_completed_n':len(recent_errors),'historical_mae_m':metrics['mae_m'],'historical_rising_mae_m':metrics['rapid_rise_mae_m'],'historical_high_mae_m':metrics['high_water_mae_m']}
            choices.append(row);audit.append(row)
        best=min(choices,key=lambda r:r['validation_score']);forecast.append(best)
        print('H',h,'SELECT',best['model'],'GAIN',best['gain'],'PRED',round(best['forecast_m'],2),'ENVELOPE',round(best['lower_error_envelope_m'],2),round(best['upper_error_envelope_m'],2),flush=True)
    savecsv(OUT/'previsao-horaria.csv',forecast);savecsv(OUT/'avaliacao-calibrada.csv',evaluations);savecsv(OUT/'teste-calibrado.csv',tests);savecsv(OUT/'alternativas-calibradas.csv',audit)
    (OUT/'previsao.json').write_text(json.dumps({'issued_at':datetime.now(TZ).isoformat(),'origin':iso(times[-1]),'observed_level_m':float(H[-1]),'forecast':forecast,'train_end':iso(tr_end),'validation_end':iso(val_end),'test_end':iso(today),'weather_features':wnames,'feature_count':{k:v.shape[1] for k,v in models.items()},'uncertainty':'Empirical error envelope from historical similar forecasts expanded by recent realized errors; no guaranteed probability or upper bound.'},ensure_ascii=False,indent=2))
if __name__=='__main__':run()
