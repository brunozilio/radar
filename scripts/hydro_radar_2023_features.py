"""Prepare a 120-column observed RADAR matrix from frozen 2023 source files."""
import csv,json
from pathlib import Path
import numpy as np
from hydro_hourly_forecast import ROOT,epoch,iso
from hydro_latency_forecast import telemetry_features
from hydro_model import asof
from hydro_rain_windows import observed_rain_windows
from hydro_routing_fit import shift
from hydro_radar_2024_features import sha,verify,parse,LEVEL_DELAYS,PLANTS

HYDRO=ROOT/'outputs/radar-insumos-observados-2023-20260921'
LAGS=ROOT/'outputs/auditoria-latencias-chuva-20260921'
OUT=ROOT/'outputs/radar-matriz-observada-2023-20260921'
def save(name,rows):
    with (OUT/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def run():
    for p in (HYDRO,LAGS):verify(p)
    protocol=ROOT/'docs/radar-2023-observed-features-protocol.json'
    wp=ROOT/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json'
    weights=json.loads(wp.read_text());lags={r['station']:r for r in json.loads((LAGS/'latencies.json').read_text())['stations']}
    paths=[protocol,wp,LAGS/'latencies.json',HYDRO/'ons-references.json',Path(__file__),
        ROOT/'scripts/hydro_radar_2024_features.py',ROOT/'scripts/hydro_hourly_forecast.py',
        ROOT/'scripts/hydro_latency_forecast.py',ROOT/'scripts/hydro_model.py',ROOT/'scripts/hydro_rain_windows.py',ROOT/'scripts/hydro_routing_fit.py']
    grid=np.arange(epoch('2023-08-29T00:00:00-03:00'),epoch('2023-10-01T00:00:00-03:00'),900)
    assert len(grid)==3168
    raw={};delayed={};rain={};level_sources={}
    for code in sorted(lags):
        p=HYDRO/'stations'/f'ana-{code}-all-qc.jsonl';paths.append(p)
        rows=[json.loads(s) for s in p.read_text().splitlines()]
        ts=np.array([epoch(r['DataHora']) for r in rows]);assert np.all(np.diff(ts)>0)
        steps=int(lags[code]['delay_seconds']/900);assert steps==lags[code]['shift_steps_15min']
        windows=observed_rain_windows(ts,np.array([parse(r,'ChuvaFinal') for r in rows]),grid) if len(rows) else {h:(np.zeros(len(grid)),np.zeros(len(grid))) for h in (1,3,6,12,24,48)}
        rain[code]={h:(shift(v[0],steps),shift(v[1],steps)) for h,v in windows.items()}
        if code in LEVEL_DELAYS:
            v=np.array([parse(r,'NivelFinal') for r in rows]);level_sources[code]=(ts,v)
            raw[code+':H']=asof(ts,v,grid,max_age=0)
            delayed[code+':H']=asof(ts,v,grid-LEVEL_DELAYS[code],max_age=900)
    ons=[]
    for r in json.loads((HYDRO/'ons-references.json').read_text()):
        p=ROOT/r['literal_csv'];assert sha(p)==r['csv_sha256'];paths.append(p)
        ons += [v for v in csv.DictReader(p.open()) if v['din_instante'].startswith(r['month'])]
    for plant,code in PLANTS.items():
        rows=sorted([r for r in ons if r['id_reservatorio'].strip()==code],key=lambda r:r['din_instante'])
        ts=np.array([epoch(r['din_instante']) for r in rows]);assert np.all(np.diff(ts)>0)
        for key,field in [('Q','val_vazaodefluente'),('I','val_vazaoafluente')]:
            v=np.array([float(r[field]) if r[field] else np.nan for r in rows])
            raw[plant+':'+key]=asof(ts,v,grid,max_age=5400)
            delayed[plant+':'+key]=asof(ts,v,grid-3600,max_age=5400)
    for group in weights:
        for h in (1,3,6,12,24,48):
            amount=sum(w*np.nan_to_num(rain[c][h][0],nan=0) for c,w in group['weights'].items())
            coverage=sum(w*np.nan_to_num(rain[c][h][1],nan=0) for c,w in group['weights'].items())
            delayed[group['group']+f':P{h}']=np.where(coverage>=.5,amount,np.nan)
            delayed[group['group']+f':C{h}']=coverage
    times,F,H,truth,phase,_=telemetry_features(grid,raw,delayed)
    keep=times>=epoch('2023-09-01T00:00:00-03:00')
    times,F,H,truth=times[keep],F[keep],H[keep],truth[phase][keep]
    assert F.shape==(720,120) and np.all(np.diff(times)==3600)
    complete=np.isfinite(F[:,:24]).all(axis=1);assert not complete.any() and np.isnan(F[:,12:24]).all()
    OUT.mkdir(exist_ok=False)
    np.savez_compressed(OUT/'features.npz',times=times,features=F,base=H,truth=truth,complete24=complete)
    np.savez_compressed(OUT/'quarter-hour.npz',times=grid,**{'raw:'+k:v for k,v in raw.items()},**delayed)
    coverage=[]
    for g in weights:
        for h in (1,3,6,12,24,48):
            c=delayed[g['group']+f':C{h}'][phase][keep];p=delayed[g['group']+f':P{h}'][phase][keep]
            coverage.append(dict(group=g['group'],window_h=h,origins=720,finite_precipitation=int(np.isfinite(p).sum()),
                coverage_min=float(c.min()),coverage_max=float(c.max()),coverage_mean=float(c.mean())))
    save('rain-coverage.csv',coverage)
    pairs=[]
    for h in range(1,13):
        target=shift(truth,-h);valid=np.isfinite(H)&np.isfinite(target);delta=target-H
        pairs.append(dict(horizon_h=h,origins=720,finite_base=int(np.isfinite(H).sum()),finite_target=int(np.isfinite(target).sum()),
            valid_pairs=int(valid.sum()),high_targets=int(((target>=7)&valid).sum()),
            minimum_response_m=float(delta[valid].min()),maximum_response_m=float(delta[valid].max())))
    save('target-coverage.csv',pairs)
    save('feature-coverage.csv',[dict(column=j,finite=int(np.isfinite(F[:,j]).sum()),missing=int(np.isnan(F[:,j]).sum())) for j in range(120)])
    trace=[]
    for code,(ts,v) in level_sources.items():
        for origin in times:
            query=origin-LEVEL_DELAYS[code];i=np.searchsorted(ts,query,side='right')-1
            usable=i>=0 and query-ts[i]<=900 and np.isfinite(v[i])
            trace.append(dict(station=code,origin=iso(origin),query=iso(query),source_time=iso(ts[i]) if i>=0 else None,
                value_m=float(v[i]) if usable else None,usable=bool(usable)))
    save('level-source-trace.csv',trace)
    (OUT/'protocol.json').write_bytes(protocol.read_bytes());(OUT/'code').mkdir()
    for p in paths:
        if p.suffix=='.py':(OUT/'code'/p.name).write_bytes(p.read_bytes())
    result=dict(input_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},origins=720,features=120,
        finite_base=int(np.isfinite(H).sum()),finite_current_truth=int(np.isfinite(truth).sum()),complete24=0,
        missing_cells=int(np.isnan(F).sum()),target_coverage=pairs,source_metadata_certified=False,trained=False,promoted=False,goal_achieved=False)
    (OUT/'preparation.json').write_text(json.dumps(result,indent=2)+'\n')
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file()],indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))
if __name__=='__main__':run()
