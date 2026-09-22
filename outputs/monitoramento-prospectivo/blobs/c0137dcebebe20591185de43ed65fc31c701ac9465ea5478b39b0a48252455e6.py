"""Extrapolation diagnostics. These never clip a forecast or certify accuracy."""
import numpy as np

def feature_names():
    names=[]
    for key in ['julho:Q','julho:I','monte:Q','monte:I','castro:Q','castro:I','86500000:Q']:
        names.extend([key+':1000m3s',key+':delta1h',key+':slope3h',key+':slope6h'])
    for group in ['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']:
        for window in [3,6,12,24,48]:names.append(f'{group}:P{window}/100mm')
    return names

def attribution(state,x,names):
    filled=np.r_[np.where(np.isfinite(x),x,state['median']),~np.isfinite(x)]
    standardized=(filled-state['mean'])/state['scale']
    contribution=standardized*state['beta']
    return [{'feature':name,'contribution_m3_s':float(value*1000),'standardized_value':float(z)} for name,value,z in zip(names+['missing:'+n for n in names],contribution,standardized)]

def outside_training_range(training,current,names):
    result=[]
    for j,name in enumerate(names):
        values=training[:,j];values=values[np.isfinite(values)]
        if not len(values) or not np.isfinite(current[j]):continue
        lo,hi=values.min(),values.max()
        if current[j]<lo or current[j]>hi:
            result.append({'feature':name,'current_value':float(current[j]),'training_min':float(lo),'training_max':float(hi)})
    return result
