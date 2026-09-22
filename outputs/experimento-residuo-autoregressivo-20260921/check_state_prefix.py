"""Perturb future rainfall and verify finalized state/features are unchanged."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from hydro_hourly_forecast import BASE,epoch,iso
from hydro_hge_dependencies import weather

out=Path(__file__).resolve().parent
saved=dict(np.load(out/'residual-series.npz'))
d=dict(np.load(BASE/'dados-roteamento.npz'));times=d['times']
hgepath=ROOT/'experiments/hge-water-balance/run.py'
spec=importlib.util.spec_from_file_location('prefix_hge',hgepath)
hge=importlib.util.module_from_spec(spec);spec.loader.exec_module(hge)
pars=next(r['parameters'] for r in json.loads((ROOT/'outputs/mucum-hge-experimental-2026-09-21/parametros.json').read_text()) if r['pet_mm_day_hypothesis']==3)
pars=np.array([pars[k] for k in hge.NAMES]);area=float(d['area'])
members=[]
for model in ('gfs_seamless','ecmwf_ifs025','icon_global'):
    p=BASE/'nwp-historical-icon.json' if model=='icon_global' else ROOT/f'outputs/mucum-propagacao-2026-09-21/raw/chuva-previsao-historica-{model}.json'
    members.append(weather(p,times,'precipitation_previous_day1')[0])
mean=np.nanmean(members,axis=0)
rain=d['amount']+np.maximum(1-d['coverage'],0)*mean
states,err=hge.simulate(rain,3.,pars,area,hge.initial_state(pars))
assert np.max(abs(err))<1e-8
assert np.array_equal(states[:,-1],saved['local_q'])
checks=[]
for origin in ('2026-06-01T00:00:00-03:00','2026-07-22T09:00:00-03:00','2026-08-14T06:00:00-03:00'):
    i=int(np.searchsorted(times,epoch(origin)))
    altered=rain.copy();altered[i:]=rain[i:]+100.
    changed,changed_err=hge.simulate(altered,3.,pars,area,hge.initial_state(pars))
    np.testing.assert_array_equal(changed[:i],states[:i])
    old_local,_=hge.simulate(mean[i:i+1],3.,pars,area,states[i-1].copy())
    new_local,_=hge.simulate(mean[i:i+1],3.,pars,area,changed[i-1].copy())
    np.testing.assert_array_equal(old_local,new_local)
    reconstructed=.25*(saved['routed'][i-1]+states[i-1,-1])+.75*(saved['routed'][i]+old_local[0,-1])
    assert abs(saved['anchor_q'][i]-reconstructed-saved['anchor_residual'][i])<1e-9
    assert np.max(abs(changed_err))<1e-8
    checks.append(dict(origin=origin,modified_observed_rain_from=iso(times[i]),prefix_states_identical=True,
                       anchor_forecast_local_identical=True,anchor_reproduced=True))
result=dict(checks=checks,full_local_series_reproduced=True,
            limitations='Checks numerical causality of finalized HGE states and forecast-rain anchor. Does not certify real source publication times, prior-day weather availability or raw-source accuracy.')
(out/'state-prefix-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
