"""Prospective routing check with trained upstream-flow forecasts, no future observations."""
import json,csv
import numpy as np
from scipy.optimize import minimize,least_squares
from hydro_precision_audit import OUT,PREV,HORIZON
from hydro_routing_data import epoch,iso,savecsv
from hydro_routing_fit import shift,fit_ridge,metric
from hydro_forecast import selection_score

def run():
    data=dict(np.load(OUT/'dados-roteamento.npz'));t=data['times'];X=data['X'];q=data['q'];H=data['h'];area=float(data['area']);z=dict(np.load(OUT/'telemetria-latencia.npz'));ix=np.searchsorted(z['times'],t);baseq=z['86510000:Q'][ix]/1000;baseH=z['86510000:H'][ix];features=[]
    for key in ['julho:Q','julho:I','monte:Q','monte:I','castro:Q','castro:I','86500000:Q']:
        a=z[key][ix]/1000;features.extend([a,a-shift(a,1),(a-shift(a,3))/3,(a-shift(a,6))/6])
    for group in ['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']:
        for window in [3,6,12,24,48]:features.append(z[group+f':P{window}'][ix]/100)
    F=np.column_stack(features);split=epoch('2025-10-01T00:00:00');valend=epoch('2026-07-01T00:00:00');today=epoch('2026-09-21T00:00:00');phases={
        'validation':(t<split,(t>=split)&(t+HORIZON*3600<valend)),
        'test':(t<valend,(t>=valend)&(t+HORIZON*3600<today)),
        'today':(t<today,t>=today)}
    # Public forecasts issued 24h before valid time, hence available before every origin used.
    weather=[]
    for model in ['gfs_seamless','ecmwf_ifs025','icon_global']:
        path=OUT/'nwp-historical-icon.json' if model=='icon_global' else PREV/'raw'/f'chuva-previsao-historica-{model}.json';r=json.loads(path.read_text())[0]['hourly'];wt=np.array([epoch(v) for v in r['time']]);wv=np.array([v if v is not None else np.nan for v in r['precipitation_previous_day1']]);lookup=dict(zip(wt,wv));weather.append(np.array([lookup.get(v,np.nan) for v in t]))
    rainforecast=np.nanmean(weather,axis=0)*area/3600
    # Retain measured parts of an incomplete interval; the missing fraction is
    # estimated by a previously issued meteorological forecast, not dry weather.
    rainfilled=np.where(np.isfinite(data['rain']),data['rain'],data['amount']*area/3600+(1-data['coverage'])*rainforecast)
    Xapply=X.copy()
    for lag in range(25):Xapply[:,33+lag]=shift(rainfilled,lag)
    flowparams={};flowforecasts={};flowaudit=[]
    for source,key,col in [('julho','julho:Q',0),('carreiro','86500000:Q',24)]:
        actual=data[source];known=z[key][ix]/1000
        for k in range(HORIZON):
            target=shift(actual,-k);delta=target-known;valid=np.isfinite(target)&np.isfinite(known);tr=np.where(valid&(t+k*3600<split))[0];va=np.where(valid&(t>=split)&(t+k*3600<valend))[0];w=1+2*(target>2)
            choices=[]
            for alpha in [10.,100.,1000.]:
                p=fit_ridge(F,delta,tr,va,alpha,w)+known[va];choices.append((float(np.mean(abs(p-target[va]))),alpha))
            _,alpha=min(choices);flowparams[(source,k)]=alpha
            for phase,(trainmask,applymask) in phases.items():
                train=np.where(valid&trainmask&(t+k*3600<(split if phase=='validation' else valend if phase=='test' else today)))[0];apply=np.where(applymask)[0];p=np.maximum(fit_ridge(F,delta,train,apply,alpha,w)+known[apply],0);arr=np.full(len(t),np.nan);arr[apply]=p;flowforecasts[(phase,source,k)]=arr
                if phase=='today':flowaudit.append({'source':source,'lead_h':k,'forecast_m3_s':float(p[-1]*1000),'alpha':alpha})
    savecsv(OUT/'previsao-vazoes-montante.csv',flowaudit)
    evaluations=[];forecasts=[];allpred=[];tauchoices={}
    for phase,(trainmask,applymask) in phases.items():
        valid=np.isfinite(X).all(axis=1)&np.isfinite(q)&np.isfinite(H);train=np.where(valid&trainmask)[0];a=X[train];sample=1+2*(q[train]>=2);p=X.shape[1];g=np.einsum('ni,n,nj->ij',a,sample,a)/len(train);rhs=np.einsum('ni,n,n->i',a,sample,q[train])/len(train)
        for start,n in [(0,12),(12,21),(33,25)]:
            for k in range(start,start+n-1):v=np.zeros(p);v[k]=1;v[k+1]=-1;g+=.005*np.outer(v,v)
        x=np.zeros(p);x[3]=1;x[12+5]=1;x[33+3]=.2
        constraints=[{'type':'eq','fun':lambda v:v[:12].sum()-1},{'type':'eq','fun':lambda v:v[12:33].sum()-1},{'type':'ineq','fun':lambda v:1-v[33:58].sum()}]
        res=minimize(lambda v:.5*np.einsum('i,ij,j',v,g,v)-np.dot(rhs,v),x,jac=lambda v:np.einsum('ij,j->i',g,v)-rhs,method='SLSQP',bounds=[(0,None)]*p,constraints=constraints,options={'maxiter':600,'ftol':1e-10});assert res.success;v=res.x
        rp=least_squares(lambda r:r[0]*q[train]**r[1]+r[2]-H[train],[4.5,.64,.4],bounds=([.01,.1,-10],[20,1.2,10]),loss='soft_l1').x
        def stage(qv):return rp[0]*np.maximum(qv,0)**rp[1]+rp[2]
        apply=np.where(applymask)[0];origins=apply.copy();qs={}
        for horizon in range(HORIZON+1):
            total=np.full(len(origins),v[-1])
            for source,lags,weights in [('julho',range(1,13),v[:12]),('carreiro',range(4,25),v[12:33])]:
                for lag,weight in zip(lags,weights):
                    lead=horizon-lag
                    if lead>=0:value=flowforecasts[(phase,source,lead)][origins]
                    else:value=data[source][origins+lead]
                    total+=weight*value
            for lag,weight in zip(range(25),v[33:58]):
                lead=horizon-lag;targetidx=origins+lead
                if lead>=0:
                    # Future meteorological predictions are known, unlike future observed rainfall.
                    value=np.array([rainforecast[j] if j<len(t) else np.nan for j in targetidx])
                    if phase=='today':
                        # Extend using exact valid-time forecast values in the same archive.
                        modelvals=[]
                        for model in ['gfs_seamless','ecmwf_ifs025','icon_global']:
                            path=OUT/'nwp-historical-icon.json' if model=='icon_global' else PREV/'raw'/f'chuva-previsao-historica-{model}.json';r=json.loads(path.read_text())[0]['hourly'];lookup={epoch(tt):vv for tt,vv in zip(r['time'],r['precipitation_previous_day1'])};modelvals.append([lookup.get(t[i]+lead*3600,np.nan) for i in origins])
                        value=np.nanmean(np.array(modelvals,dtype=float),axis=0)*area/3600
                else:value=rainfilled[targetidx]
                total+=weight*value
            qs[horizon]=total
        # Assimilate at the actual measurement age; do not hard-code 30 minutes.
        age=float(next(r for r in csv.DictReader((OUT/'idades-fontes.csv').open()) if r['source']=='86510000')['delay_minutes'])/60
        whole=int(np.floor(age));fraction=age-whole
        recent=qs[0] if whole==0 else np.einsum('ni,i->n',Xapply[np.maximum(origins-whole,0)],v)
        older=np.einsum('ni,i->n',Xapply[np.maximum(origins-whole-1,0)],v)
        reconstructed_last=recent if fraction==0 else (1-fraction)*recent+fraction*older
        residual=baseq[origins]-reconstructed_last;ratingoffset=baseH[origins]-stage(baseq[origins])
        for horizon in range(1,HORIZON+1):
            target=shift(H,-horizon)[origins];good=np.isfinite(target)&np.isfinite(qs[horizon])&np.isfinite(residual)&np.isfinite(baseH[origins]);options=[]
            for tau in ([2.,6.,12.,1e6] if phase=='validation' else [tauchoices[horizon]]):
                pred=stage(qs[horizon]+residual*np.exp(-(horizon+age)/tau))+ratingoffset
                score=selection_score(pred[good],target[good],baseH[origins][good]);options.append((score,tau,pred))
            score,tau,pred=min(options,key=lambda r:r[0]);tauchoices[horizon]=tau;metrics=metric(pred[good],target[good]);metrics.update({'h':horizon,'phase':phase,'tau_h':tau});evaluations.append(metrics)
            for i,true,pp in zip(origins[good],target[good],pred[good]):allpred.append({'h':horizon,'phase':phase,'origin':iso(t[i]),'target':iso(t[i]+horizon*3600),'actual_m':true,'forecast_m':pp})
            if phase=='today':forecasts.append({'h':horizon,'time':iso(t[-1]+horizon*3600),'forecast_m':float(pred[-1]) if np.isfinite(pred[-1]) else None,'today_mae_m':metrics['mae_m'],'test_mae_m':next(e['mae_m'] for e in evaluations if e['h']==horizon and e['phase']=='test'),'tau_h':tau});print(horizon,'routing forecast',forecasts[-1],flush=True)
    savecsv(OUT/'roteamento-previsao.csv',forecasts);savecsv(OUT/'roteamento-avaliacao.csv',evaluations);savecsv(OUT/'roteamento-retrospectivas.csv',allpred)

if __name__=='__main__':run()
