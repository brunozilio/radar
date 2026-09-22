"""Fixed-origin ablation: corrected rain windows and nonlinear response models."""
import json,csv
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from hydro_precision_audit import OUT,PREV
from hydro_routing_data import epoch,iso,savecsv
from hydro_routing_fit import prepare,shift,fit_ridge,metric
from hydro_forecast import selection_score,assimilate

def run():
    times,data,H,Q,X,names,configs=prepare();z=dict(np.load(OUT/'telemetria-corrigida.npz'));ix=np.searchsorted(z['times'],times);groups=['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']
    corrected=X.copy();coverage=[];raincols=[]
    for group in groups:
        for window in [1,3,6,12,24]:
            j=names.index(group+':P'+str(window));corrected[:,j]=z[group+f':rain{window}'][ix];raincols.append(j)
            coverage.append(z[group+f':cover{window}'][ix])
        for lag in [3,6,12]:
            j=names.index(group+':P3lag'+str(lag));corrected[:,j]=shift(z[group+':rain3'][ix],lag);raincols.append(j)
        j=names.index(group+':antecedent');corrected[:,j]=z[group+':rain48'][ix];raincols.append(j)
        j=names.index(group+':wet_interaction');corrected[:,j]=z[group+':rain3'][ix]*np.minimum(z[group+':rain48'][ix]/50,3);raincols.append(j)
    cov=np.column_stack(coverage);clean=np.column_stack([corrected,cov]);log=clean.copy();log[:,raincols]=np.log1p(np.maximum(log[:,raincols],0));nointer=[i for i,name in enumerate(names) if ':wet_interaction' not in name]+list(range(X.shape[1],clean.shape[1]))
    # Differences between contemporaneous stations remain in their separate datums.
    for c in ['86472000','86472600','86500000']:
        upstream=data[c+':H'];extra=np.column_stack([(upstream-H),upstream-shift(upstream,1),upstream-shift(upstream,3)])
        log=np.column_stack([log,extra]);clean=np.column_stack([clean,extra])
    models={'linear_corrigido':clean,'log_chuva':log,'linear_sem_interacao':clean[:,nointer],'arvores_corrigidas':clean}
    core=np.all(np.isfinite(X[:,:20]),axis=1)&np.isfinite(H);split=epoch('2025-10-01T00:00:00');test=epoch('2026-07-01T00:00:00');today=epoch('2026-09-21T00:00:00')
    evals=[];preds=[];forecasts=[];audit=[]
    for h in range(1,7):
        target=shift(H,-h);delta=target-H;valid=core&np.isfinite(target);tr=np.where(valid&(times+h*3600<split))[0];va=np.where(valid&(times>=split)&(times+h*3600<test))[0];te=np.where(valid&(times>=test)&(times+h*3600<today))[0];td=np.where(valid&(times>=today))[0];finaltrain=np.where(valid&(times+h*3600<today))[0];weight=1+2*(abs(delta)>=1)+2*(target>=9)
        for name,xx in models.items():
            tree=name.startswith('arvores');options=[]
            def fit(train,apply,param):
                if tree:
                    leaf,loss,weighted=param;est=HistGradientBoostingRegressor(max_iter=180,max_leaf_nodes=leaf,min_samples_leaf=35,learning_rate=.055,l2_regularization=10,loss=loss,early_stopping=False,random_state=57)
                    est.fit(xx[train],delta[train],sample_weight=weight[train] if weighted else None);return est.predict(xx[apply])+H[apply]
                alpha,weighted=param;return fit_ridge(xx,delta,train,apply,alpha,weight if weighted else None)+H[apply]
            params=[(leaf,loss,True) for leaf in [7,15] for loss in ['squared_error','absolute_error']] if tree else [(alpha,w) for alpha in [10.,100.,1000.] for w in [False,True]]
            for param in params:
                raw=fit(tr,va,param)
                for gain in [0.,.25,.5,1.]:
                    p,_=assimilate(va,raw,target,h,gain);options.append((selection_score(p,target[va],H[va]),param,gain))
            score,param,gain=min(options);train=np.r_[tr,va];valraw=fit(tr,va,param);valp,_=assimilate(va,valraw,target,h,gain);testp,_=assimilate(te,fit(train,te,param),target,h,gain);apply=np.r_[td,len(times)-1];todayp,_=assimilate(apply,fit(finaltrain,apply,param),target,h,gain)
            for phase,indices,pp in [('validation',va,valp),('test',te,testp),('today',td,todayp[:-1])]:
                m=metric(pp,target[indices]);rise=target[indices]-H[indices]>=1;high=target[indices]>=9
                m.update({'h':h,'model':name,'phase':phase,'validation_score':score,'param':str(param),'gain':gain,'rise_mae_m':float(np.mean(abs(pp[rise]-target[indices][rise]))) if rise.any() else None,'high_mae_m':float(np.mean(abs(pp[high]-target[indices][high]))) if high.any() else None});evals.append(m)
                for j,p in zip(indices,pp):preds.append({'model':name,'h':h,'origin':iso(times[j]),'target_time':iso(times[j]+h*3600),'base_m':H[j],'actual_m':target[j],'forecast_m':p,'phase':phase})
            f={'h':h,'model':name,'origin':iso(times[-1]),'time':iso(times[-1]+h*3600),'forecast_m':float(todayp[-1]),'validation_score':score,'gain':gain,'param':str(param)};forecasts.append(f)
            print(h,name,'forecast',round(f['forecast_m'],2),'VAL',round(score,3),'test',round(evals[-2]['mae_m'],3),'TODAY',round(evals[-1]['mae_m'],3),flush=True)
            savecsv(OUT/'avaliacao-correcoes.csv',evals);savecsv(OUT/'retrospectivas-correcoes.csv',preds);savecsv(OUT/'candidatos-corrigidos.csv',forecasts)
    (OUT/'configuracao.json').write_text(json.dumps({'origin':iso(times[-1]),'target_station':'86510000','base_m':H[-1],'train_end':iso(split),'validation_end':iso(test),'test_end':iso(today),'note':'Development-informed historical test; today excluded from fitting. Candidate selection uses validation only.'},indent=2))

if __name__=='__main__':run()
