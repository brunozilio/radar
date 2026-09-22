"""Causal integration of measured precipitation intervals."""
import numpy as np
WINDOWS=[1,3,6,12,24,48]

def observed_rain_windows(times,rain,grid,windows=WINDOWS):
    """Integrate only measured intervals, never extend rain after its timestamp."""
    dt=np.r_[0,np.diff(times)];good=np.isfinite(rain)&(rain>=0)&(dt>0)&(dt<=5400)
    increments=np.where(good,rain,0);durations=np.where(good,dt,0)
    cum=np.cumsum(increments);cov=np.cumsum(durations)
    end=np.searchsorted(times,grid,side='right')-1;safe=np.maximum(end,0)
    total=np.where(end>=0,cum[safe],0);covered=np.where(end>=0,cov[safe],0)
    result={}
    for window in windows:
        boundary=grid-window*3600;left=np.searchsorted(times,boundary,side='right')-1;ls=np.maximum(left,0)
        lr=np.where(left>=0,cum[ls],0);lc=np.where(left>=0,cov[ls],0)
        nxt=left+1;ns=np.minimum(nxt,len(times)-1)
        partial=(left>=0)&(nxt<=end)&(nxt<len(times))&good[ns]
        fraction=np.where(partial,(boundary-times[ls])/np.maximum(dt[ns],1),0)
        lr+=fraction*increments[ns];lc+=fraction*durations[ns]
        result[window]=(np.maximum(total-lr,0),np.clip((covered-lc)/(window*3600),0,1))
    return result

