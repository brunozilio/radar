"""Prepare reserved2021/2022 inputs only, under the frozen RADAR challenge contract."""
import csv,json
from pathlib import Path
import numpy as np
from hydro_hourly_forecast import ROOT,epoch,iso
from hydro_latency_forecast import telemetry_features
from hydro_model import asof
from hydro_rain_windows import observed_rain_windows
from hydro_routing_fit import shift
from hydro_radar_2024_features import sha,verify,parse,LEVEL_DELAYS,PLANTS

HYDRO=ROOT/'outputs/radar-insumos-reservados-2021-2022-20260922'
QI=ROOT/'outputs/ons-reserva-2021-2022-20260922'
LAGS=ROOT/'outputs/auditoria-latencias-chuva-20260921'
FROZEN=ROOT/'outputs/congelamento-radar-reserva-2021-2022-20260922'
OUT=ROOT/'outputs/radar-matrizes-reservadas-2021-2022-20260922'
PROTOCOL=ROOT/'docs/radar-reserved-2021-2022-challenge-protocol.json'
def save(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def dump(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def run():
    assert not OUT.exists(),'Existing preparation must be inspected, never overwritten.'
    for p in (HYDRO,QI,LAGS,FROZEN):verify(p)
    protocol=json.loads(PROTOCOL.read_text());assert sha(PROTOCOL)==sha(FROZEN/'protocol.json')
    for name,h in protocol['reference_sha256'].items():assert sha(ROOT/name)==h,name
    wp=ROOT/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json'
    weights=json.loads(wp.read_text());lags={r['station']:r for r in json.loads((LAGS/'latencies.json').read_text())['stations']}
    assert set(lags)=={c for g in weights for c in g['weights']} and len(lags)==27
    common=[PROTOCOL,wp,LAGS/'latencies.json',QI/'ons-references.json',QI/'audit.json',QI/'lag-source-trace.csv',QI/'origin-diagnostics.csv',
        HYDRO/'source-manifest.json',HYDRO/'verification.json',Path(__file__),ROOT/'scripts/hydro_radar_2024_features.py',
        ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_latency_forecast.py',ROOT/'scripts/hydro_model.py',
        ROOT/'scripts/hydro_rain_windows.py',ROOT/'scripts/hydro_routing_fit.py']
    OUT.mkdir();(OUT/'code').mkdir();(OUT/'protocol.json').write_bytes(PROTOCOL.read_bytes())
    for p in common:
        if p.suffix=='.py':(OUT/'code'/p.name).write_bytes(p.read_bytes())
    years=[];allpaths=set(common)
    for year,n,stop in [(2021,744,'2021-06-01'),(2022,1464,'2022-07-01')]:
        folder=OUT/str(year);folder.mkdir();paths=list(common)
        grid=np.arange(epoch(f'{year}-04-28T00:00:00-03:00'),epoch(stop+'T00:00:00-03:00'),900)
        raw={};delayed={};rain={};level_sources={};strict_truth=None;station_meta=[]
        for code in sorted(lags):
            p=HYDRO/'stations'/str(year)/f'ana-{code}-all-qc.jsonl';paths.append(p)
            rows=[json.loads(s) for s in p.read_text().splitlines()]
            ts=np.array([epoch(r['DataHora']) for r in rows]);assert np.all(np.diff(ts)>0)
            values=np.array([parse(r,'ChuvaFinal') for r in rows])
            steps=int(lags[code]['delay_seconds']/900);assert steps==lags[code]['shift_steps_15min']
            windows=observed_rain_windows(ts,values,grid) if len(rows) else {h:(np.zeros(len(grid)),np.zeros(len(grid))) for h in (1,3,6,12,24,48)}
            rain[code]={h:(shift(v[0],steps),shift(v[1],steps)) for h,v in windows.items()}
            station_meta.append(dict(station=code,rows=len(rows),finite_parsed_rain=int(np.isfinite(values).sum()),effective_delay_seconds=steps*900))
            if code in LEVEL_DELAYS:
                v=np.array([parse(r,'NivelFinal') for r in rows]);level_sources[code]=(ts,v)
                raw[code+':H']=asof(ts,v,grid,max_age=0)
                delayed[code+':H']=asof(ts,v,grid-LEVEL_DELAYS[code],max_age=900)
                if code=='86510000':
                    strict=np.array([parse(r,'NivelFinal') if r.get('CQ_NivelFinal')=='Dado aprovado' else np.nan for r in rows])
                    strict_truth=asof(ts,strict,grid,max_age=0)
        assert strict_truth is not None
        ons=[]
        for ref in json.loads((QI/'ons-references.json').read_text()):
            if not ref['month'].startswith(str(year)):continue
            p=ROOT/ref['literal_csv'];assert sha(p)==ref['csv_sha256'];paths.append(p)
            ons.extend(v for v in csv.DictReader(p.open()) if v['din_instante'].startswith(ref['month']))
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
        times,F,H,_,phase,_=telemetry_features(grid,raw,delayed)
        keep=times>=epoch(f'{year}-05-01T00:00:00-03:00')
        times,F,H,truth=times[keep],F[keep],H[keep],strict_truth[phase][keep]
        assert F.shape==(n,120) and np.all(np.diff(times)==3600)
        assert times[-1]+3600==epoch(stop+'T00:00:00-03:00')
        complete=np.isfinite(F[:,:24]).all(axis=1)
        np.savez_compressed(folder/'features.npz',times=times,features=F,base=H,truth=truth,complete24=complete)
        np.savez_compressed(folder/'quarter-hour.npz',times=grid,strict_truth=strict_truth,**{'raw:'+k:v for k,v in raw.items()},**delayed)
        coverage=[]
        for g in weights:
            for h in (1,3,6,12,24,48):
                c=delayed[g['group']+f':C{h}'][phase][keep];p=delayed[g['group']+f':P{h}'][phase][keep]
                coverage.append(dict(group=g['group'],window_h=h,origins=n,finite_precipitation=int(np.isfinite(p).sum()),
                    coverage_min=float(c.min()),coverage_max=float(c.max()),coverage_mean=float(c.mean())))
        save(folder/'rain-coverage.csv',coverage);save(folder/'station-rain-coverage.csv',station_meta)
        pairs=[]
        for h in range(1,13):
            target=shift(truth,-h);within=times+h*3600<epoch(stop+'T00:00:00-03:00')
            finite=np.isfinite(target)&within;valid=np.isfinite(H)&finite
            pairs.append(dict(horizon_h=h,origins=n,scheduled_rows=int(within.sum()),boundary_excluded=int((~within).sum()),
                finite_base_in_schedule=int((np.isfinite(H)&within).sum()),observed_targets=int(finite.sum()),valid_pairs=int(valid.sum()),
                missing_truth_in_schedule=int((within&~finite).sum()),missing_base_observed_target=int((finite&~np.isfinite(H)).sum()),
                high_observed_targets=int(((target>=7)&finite).sum()),high_valid_pairs=int(((target>=7)&valid).sum())))
        save(folder/'target-coverage.csv',pairs)
        save(folder/'feature-coverage.csv',[dict(column=j,finite=int(np.isfinite(F[:,j]).sum()),missing=int(np.isnan(F[:,j]).sum())) for j in range(120)])
        trace=[]
        for code,(ts,v) in level_sources.items():
            for origin in times:
                query=origin-LEVEL_DELAYS[code];i=np.searchsorted(ts,query,side='right')-1
                usable=i>=0 and query-ts[i]<=900 and np.isfinite(v[i])
                trace.append(dict(station=code,origin=iso(origin),query=iso(query),source_time=iso(ts[i]) if i>=0 else None,
                    value_m=float(v[i]) if usable else None,usable=bool(usable)))
        save(folder/'level-source-trace.csv',trace)
        qidiag=[r for r in csv.DictReader((QI/'origin-diagnostics.csv').open()) if r['year']==str(year)]
        assert [epoch(r['origin']) for r in qidiag]==times.tolist();save(folder/'qi-origin-diagnostics.csv',qidiag)
        result=dict(year=year,origins=n,features=120,quarter_rows=len(grid),finite_base=int(np.isfinite(H).sum()),finite_current_truth=int(np.isfinite(truth).sum()),
            complete24=int(complete.sum()),missing_cells=int(np.isnan(F).sum()),target_coverage=pairs,
            input_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},model_inference=False,trained=False,promoted=False,goal_achieved=False)
        dump(folder/'preparation.json',result);years.append(result);allpaths.update(paths)
        print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','target_coverage')}),flush=True)
    dump(OUT/'preparation.json',dict(years=years,input_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(allpaths)},
        protocol_sha256=sha(PROTOCOL),models_accessed=False,inference_performed=False,goal_achieved=False))
    dump(OUT/'artifact-hashes.json',[dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file()])

if __name__=='__main__':run()
