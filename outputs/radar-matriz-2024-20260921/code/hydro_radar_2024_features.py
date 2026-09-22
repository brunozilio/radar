"""Prepare frozen Radar research features for2024; never fit or issue a model."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from hydro_hourly_forecast import ROOT,epoch,iso,weather_values
from hydro_latency_forecast import telemetry_features
from hydro_model import asof
from hydro_rain_windows import observed_rain_windows
from hydro_routing_fit import shift

HYDRO=ROOT/'outputs/radar-insumos-2024-hidrologia-20260921'
WEATHER=ROOT/'outputs/radar-insumos-2024-meteorologia-20260921'
LAGS=ROOT/'outputs/auditoria-latencias-chuva-20260921'
OUT=ROOT/'outputs/radar-matriz-2024-20260921'
LEVEL_DELAYS={'86510000':900,'86472000':1800,'86472600':900,'86500000':1800}
PLANTS={'julho':'JIUHQJ','monte':'JIUHMC','castro':'JIUHCA'}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def verify(folder):
    m=json.loads((folder/'artifact-hashes.json').read_text())
    items=m['files'].items() if isinstance(m,dict) else [(r['file'],r['sha256']) for r in m]
    for name,digest in items:assert sha(folder/name)==digest,str(folder/name)


def parse(row,field):
    try:value=float(row[field])
    except (TypeError,ValueError,KeyError):return np.nan
    if not np.isfinite(value) or value<0 or row.get('CQ_'+field) not in ['Dado aprovado',None]:return np.nan
    if field=='ChuvaFinal' and value>150:return np.nan
    return value/100 if field=='NivelFinal' else value


def save(name,rows):
    with (OUT/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def run():
    for folder in (HYDRO,WEATHER,LAGS):verify(folder)
    protocol=ROOT/'docs/radar-2024-features-protocol.json'
    weights_path=ROOT/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json'
    weights=json.loads(weights_path.read_text())
    lags={r['station']:r for r in json.loads((LAGS/'latencies.json').read_text())['stations']}
    paths=[protocol,weights_path,LAGS/'latencies.json',LAGS/'regional-comparison.json',HYDRO/'ons-ceran-source-values.csv',Path(__file__),
        ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_latency_forecast.py',ROOT/'scripts/hydro_model.py',
        ROOT/'scripts/hydro_rain_windows.py',ROOT/'scripts/hydro_routing_fit.py']
    grid=np.arange(epoch('2024-03-29T00:00:00-03:00'),epoch('2024-05-02T00:00:00-03:00'),900)
    assert len(grid)==3264
    raw={};delayed={};rain_windows={};level_sources={};rain_meta=[]
    for code in sorted(lags):
        path=HYDRO/'stations'/f'ana-{code}-all-qc.jsonl';paths.append(path)
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        stamps=np.array([epoch(r['DataHora']) for r in rows])
        assert len(stamps)==len(np.unique(stamps)) and np.all(np.diff(stamps)>0)
        rain=np.array([parse(r,'ChuvaFinal') for r in rows])
        steps=int(lags[code]['shift_steps_15min'])
        assert steps==int(lags[code]['delay_seconds']/900)
        if len(rows):
            windows=observed_rain_windows(stamps,rain,grid)
        else:
            # No measured amount or duration; regional coverage governs admission.
            windows={h:(np.zeros(len(grid)),np.zeros(len(grid))) for h in (1,3,6,12,24,48)}
        rain_windows[code]={h:(shift(v[0],steps),shift(v[1],steps)) for h,v in windows.items()}
        rain_meta.append(dict(station=code,records=len(rows),finite_rain=int(np.isfinite(rain).sum()),
            delay_seconds=lags[code]['delay_seconds'],effective_delay_seconds=steps*900,steps_15min=steps))
        if code in LEVEL_DELAYS:
            value=np.array([parse(r,'NivelFinal') for r in rows])
            raw[code+':H']=asof(stamps,value,grid,max_age=0)
            delayed[code+':H']=asof(stamps,value,grid-LEVEL_DELAYS[code],max_age=900)
            level_sources[code]=(stamps,value)
    source=list(csv.DictReader((HYDRO/'ons-ceran-source-values.csv').open()))
    for plant,identifier in PLANTS.items():
        selected=sorted([r for r in source if r['id_reservatorio'].strip()==identifier],key=lambda r:r['din_instante'])
        stamps=np.array([epoch(r['din_instante']) for r in selected])
        assert np.all(np.diff(stamps)>0)
        for key,field in [('Q','val_vazaodefluente'),('I','val_vazaoafluente')]:
            values=np.array([float(r[field]) if r[field] else np.nan for r in selected])
            raw[plant+':'+key]=asof(stamps,values,grid,max_age=5400)
            delayed[plant+':'+key]=asof(stamps,values,grid-3600,max_age=5400)
    for group in weights:
        for h in (1,3,6,12,24,48):
            amount=sum(w*np.nan_to_num(rain_windows[c][h][0],nan=0) for c,w in group['weights'].items())
            coverage=sum(w*np.nan_to_num(rain_windows[c][h][1],nan=0) for c,w in group['weights'].items())
            delayed[group['group']+f':P{h}']=np.where(coverage>=.5,amount,np.nan)
            delayed[group['group']+f':C{h}']=coverage
    times,X,H,truth,phase,_=telemetry_features(grid,raw,delayed)
    keep=times>=epoch('2024-04-01T00:00:00-03:00')
    times=times[keep];X=X[keep];H=H[keep];truth=truth[phase][keep]
    assert X.shape==(744,120) and np.all(np.diff(times)==3600)
    weather=[]
    for model in ('gfs_seamless','ecmwf_ifs025','icon_global'):
        path=WEATHER/'raw'/f'{model}.json';paths.append(path)
        for location in range(5):
            for h in (3,6,9,12):
                future=times[:,None]+np.arange(1,h+1)*3600
                a=weather_values(path,location,future.ravel(),'precipitation_previous_day1').reshape(future.shape)
                assert np.isfinite(a).all()
                weather.append(a.sum(axis=1))
    F=np.column_stack([X,np.column_stack(weather)])
    assert F.shape==(744,180) and np.isfinite(H).all() and np.isfinite(truth).all()
    complete=np.isfinite(F[:,:24]).all(axis=1)
    assert not complete.any() and np.isnan(F[:,18:24]).all()
    OUT.mkdir(exist_ok=False)
    np.savez_compressed(OUT/'features.npz',times=times,features=F,base=H,truth=truth,complete24=complete)
    np.savez_compressed(OUT/'quarter-hour.npz',times=grid,**{'raw:'+k:v for k,v in raw.items()},**delayed)
    save('rain-delays.csv',rain_meta)
    source_trace=[]
    for code,(stamps,values) in level_sources.items():
        for origin in times:
            query=origin-LEVEL_DELAYS[code];i=np.searchsorted(stamps,query,side='right')-1
            age=query-stamps[i] if i>=0 else None
            usable=i>=0 and age<=900 and np.isfinite(values[i])
            source_trace.append(dict(origin=iso(origin),station=code,query_time=iso(query),
                source_time=iso(stamps[i]) if i>=0 else None,age_after_delay_seconds=float(age) if i>=0 else None,
                value_m=float(values[i]) if usable else None,usable=bool(usable)))
    save('level-source-trace.csv',source_trace)
    rain_coverage=[]
    for group in weights:
        for h in (1,3,6,12,24,48):
            c=delayed[group['group']+f':C{h}'][phase][keep]
            p=delayed[group['group']+f':P{h}'][phase][keep]
            rain_coverage.append(dict(group=group['group'],window_h=h,origins=len(times),
                finite_precipitation=int(np.isfinite(p).sum()),coverage_min=float(c.min()),coverage_max=float(c.max()),
                coverage_mean=float(c.mean()),coverage_below_half=int((c<.5).sum())))
    save('rain-coverage.csv',rain_coverage)
    save('feature-coverage.csv',[dict(column=j,finite=int(np.isfinite(F[:,j]).sum()),missing=int((~np.isfinite(F[:,j])).sum())) for j in range(180)])
    (OUT/'protocol.json').write_bytes(protocol.read_bytes())
    (OUT/'code').mkdir()
    for p in paths:
        if p.suffix=='.py':(OUT/'code'/p.name).write_bytes(p.read_bytes())
    summary=dict(input_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},
        origins=len(times),features=F.shape[1],complete24_origins=int(complete.sum()),
        other18_complete=int(np.isfinite(F[:,:18]).all(axis=1).sum()),
        finite_base=int(np.isfinite(H).sum()),finite_current_truth=int(np.isfinite(truth).sum()),
        finite_weather_cells=int(np.isfinite(F[:,120:]).sum()),total_cells=int(F.size),missing_cells=int((~np.isfinite(F)).sum()),
        source_timezones_certified=False,datum_continuity_certified=False,publication_latency_certified=False,
        trained=False,promoted=False,goal_achieved=False)
    (OUT/'preparation.json').write_text(json.dumps(summary,indent=2)+'\n')
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file()],indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='input_sha256'},indent=2))
    print(json.dumps(rain_coverage,indent=2))


if __name__=='__main__':run()
