"""Online model weights depend only on forecasts whose targets are already observed."""
import csv,json,math
from datetime import datetime
from pathlib import Path
import numpy as np
from hydro_routing_data import OUT,TZ,epoch,iso,savecsv
from hydro_routing_fit import metric
from hydro_forecast import selection_score

def online(times,preds,actual,h,memory,prior_n,power,bias_gain):
    n,m=preds.shape;out=np.zeros(n);weights=np.zeros_like(preds);errors=preds-actual[:,None]
    sq=np.zeros(m);bias=np.zeros(m);mass=0.;pointer=0;previous=times[0];prior=(.1*h)**2
    for i,t in enumerate(times):
        decay=math.exp(-(t-previous)/(memory*3600));sq*=decay;bias*=decay;mass*=decay;previous=t
        # Add newly realized errors at their proper observation times, never at forecast issue time.
        while pointer<n and times[pointer]+h*3600<=t:
            if np.isfinite(actual[pointer]) and np.isfinite(errors[pointer]).all():
                weight=math.exp(-(t-times[pointer]-h*3600)/(memory*3600));sq+=weight*errors[pointer]**2;bias+=weight*errors[pointer];mass+=weight
            pointer+=1
        mse=(sq+prior_n*prior)/(mass+prior_n);w=1/np.maximum(mse,.01**2)**power;w/=w.sum();weights[i]=w
        correction=bias_gain*bias/(mass+prior_n)
        out[i]=np.sum(w*(preds[i]-correction))
    return out,weights

def matrix(rows,models):
    by={}
    for r in rows:
        by.setdefault(r['origin'],{})[r['model']]=r
    times=[];preds=[];actual=[];base=[]
    for t,d in sorted(by.items()):
        if not all(m in d for m in models):continue
        times.append(epoch(t[:19]));preds.append([float(d[m]['forecast_m']) for m in models]);actual.append(float(d[models[0]]['actual_m']));base.append(float(d[models[0]]['base_m']))
    return np.array(times),np.array(preds),np.array(actual),np.array(base)
def run():
    allrows=list(csv.DictReader((OUT/'teste-calibrado.csv').open()));alts=list(csv.DictReader((OUT/'alternativas-calibradas.csv').open()));meta=json.loads((OUT/'previsao.json').read_text());models=sorted({r['model'] for r in alts});forecasts=[];evals=[];outrows=[]
    for h in range(1,7):
        rows=[r for r in allrows if int(r['h'])==h];v=matrix([r for r in rows if r['phase']=='validation'],models);opts=[]
        for memory in [6.,12.,24.]:
            for prior_n in [1.,6.]:
                for power in [1.,2.]:
                    for gain in [0.,.25,.5]:
                        p,w=online(v[0],v[1],v[2],h,memory,prior_n,power,gain)
                        opts.append((selection_score(p,v[2],v[3]),memory,prior_n,power,gain))
        score,memory,prior_n,power,gain=min(opts);test=matrix([r for r in rows if r['phase']=='test'],models)
        p,w=online(test[0],test[1],test[2],h,memory,prior_n,power,gain);m=metric(p,test[2]);rise=test[2]-test[3]>=1;high=test[2]>=9
        m.update({'h':h,'memory_h':memory,'prior_n':prior_n,'power':power,'bias_gain':gain,'validation_score':score,'rising_mae_m':float(np.mean(abs(p[rise]-test[2][rise]))),'rising_n':int(rise.sum()),'high_water_mae_m':float(np.mean(abs(p[high]-test[2][high]))),'high_water_n':int(high.sum())});evals.append(m)
        for i,t in enumerate(test[0]):outrows.append({'h':h,'origin':iso(t),'target':iso(t+h*3600),'actual_m':test[2][i],'forecast_m':p[i],'phase':'test'})
        # Current weighting sees recent completed causal hindcasts, then the new forecast.
        today=matrix([r for r in rows if r['phase']=='today'],models);current=np.array([float(next(r for r in alts if r['model']==model and int(r['h'])==h)['forecast_m']) for model in models])
        history_times=np.r_[test[0][-48:],today[0],epoch(meta['origin'][:19])];history_pred=np.vstack([test[1][-48:],today[1],current]);history_actual=np.r_[test[2][-48:],today[2],np.nan]
        result,rw=online(history_times,history_pred,history_actual,h,memory,prior_n,power,gain);point=float(result[-1]);currentw=rw[-1]
        recent_errors=history_actual[-len(today[0])-1:-1]-result[-len(today[0])-1:-1] if len(today[0]) else np.array([])
        for i,t in enumerate(today[0]):outrows.append({'h':h,'origin':iso(t),'target':iso(t+h*3600),'actual_m':today[2][i],'forecast_m':result[48+i] if len(test[0])>=48 else result[len(test[0])+i],'phase':'today'})
        similar=((p-test[3])>=.15*h)|(test[3]>=7);errors=abs(test[2][similar]-p[similar]);historic90=float(np.quantile(errors,.9))
        recent90=float(np.quantile(abs(recent_errors),.9)) if len(recent_errors) else 0
        width=max(historic90,recent90)
        forecasts.append({'h':h,'time':iso(epoch(meta['origin'][:19])+h*3600),'forecast_m':point,'lower_reference_m':point-width,'upper_reference_m':point+width,'historical_similar_p90_abs_m':historic90,'today_p90_abs_m':recent90,'today_mae_m':float(np.mean(abs(recent_errors))) if len(recent_errors) else None,'validation_score':score,'weights':{model:float(weight) for model,weight in zip(models,currentw)}})
        print(h,round(point,2),'range',round(point-width,2),round(point+width,2),'weights',[(model,round(weight,2)) for model,weight in zip(models,currentw)],flush=True)
    savecsv(OUT/'avaliacao-combinada.csv',evals);savecsv(OUT/'teste-combinado.csv',outrows)
    (OUT/'previsao-combinada.json').write_text(json.dumps({'origin':meta['origin'],'observed_level_m':meta['observed_level_m'],'issued_at':datetime.now(TZ).isoformat(),'forecast':forecasts,'evaluation':evals,'method':'Weighted ensemble with exponential memory of already-realized errors; hyperparameters selected in validation period.'},ensure_ascii=False,indent=2))
    savecsv(OUT/'previsao-final.csv',[{k:v for k,v in r.items() if k!='weights'} for r in forecasts])
if __name__=='__main__':run()
