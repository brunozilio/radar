"""Audit time-window errors without overwriting the published forecast snapshot."""
import json,csv,sys,os
from pathlib import Path
import numpy as np
from hydro_routing_data import OUT as PREV,RAW,load_ana,epoch,iso,savecsv
OUT=Path(os.environ.get('HYDRO_OUTPUT_DIR',str(PREV.parent/'mucum-auditoria-2026-09-21')));OUT.mkdir(exist_ok=True)
HORIZON=int(os.environ.get('HYDRO_HORIZON','6'))
WINDOWS=[1,3,6,12,24,48]

from hydro_rain_windows import observed_rain_windows

def run():
    z=dict(np.load(PREV/'telemetria.npz'));grid=z['times'];weights=json.loads((PREV/'chuva-pesos.json').read_text());codes=sorted({c for g in weights for c in g['weights']})
    windows={};checks=[];age=[]
    for c in codes:
        d=load_ana(c);windows[c]=observed_rain_windows(d['times'],d['rain'],grid)
        dc=np.r_[np.nan,np.diff(d['counter'])];valid=np.isfinite(dc)&np.isfinite(d['rain'])&(dc>=0)&(dc<=150)
        checks.append({'station':c,'counter_pairs':int(valid.sum()),'counter_match_fraction':float(np.mean(abs(dc[valid]-d['rain'][valid])<.011)) if valid.any() else None})
    audits=[]
    for group in weights:
        name=group['group']
        for window in WINDOWS:
            amounts=sum(w*windows[c][window][0] for c,w in group['weights'].items());coverage=sum(w*windows[c][window][1] for c,w in group['weights'].items());value=np.where(coverage>=.5,amounts,np.nan)
            z[name+f':rain{window}']=value;z[name+f':cover{window}']=coverage
            audits.append({'region':name,'window_h':window,'known_area_weighted_mm':float(amounts[-1]),'space_time_coverage':float(coverage[-1]),'partial_window_feature_mm':float(value[-1]) if np.isfinite(value[-1]) else None})
    np.savez_compressed(OUT/'telemetria-corrigida.npz',**z);savecsv(OUT/'auditoria-contadores.csv',checks);savecsv(OUT/'janelas-chuva-corrigidas.csv',audits)
    # Regression test: the interval 11h–12h must not become fresh rain at 13h.
    a=observed_rain_windows(np.array([0.,3600.,7200.]),np.array([0.,0.,28.]),np.array([7200.,10800.]),[1,2])
    assert np.allclose(a[1][0],[28,0]) and np.allclose(a[1][1],[1,0])
    assert np.allclose(a[2][0],[28,28])
    # Boundary fractions conserve the measured total; unknown tail stays missing.
    a=observed_rain_windows(np.array([0.,3600.,7200.]),np.array([0.,8.,12.]),np.array([8100.]),[1])
    assert np.allclose(a[1][0],[9]) and np.allclose(a[1][1],[.75])
    (OUT/'testes-janelas.json').write_text(json.dumps({'no_repeated_hourly_increment':True,'partial_interval_conservation':True,'unknown_tail_not_zero_rain':True},indent=2))
    print(json.dumps(audits,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':run()
