"""Causal feature dependency trace and offline source-conflict fallback.

This is an inspected-data diagnostic, not certified source quality or promotion.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np
from hydro_hourly_forecast import ROOT,BASE,epoch,iso,dump
from hydro_upstream_audit import savecsv

COMPONENTS=('val_vazaoturbinada','val_vazaovertida','val_vazaooutrasestruturas')
AUDIT=ROOT/'outputs/auditoria-consistencia-componentes-ceran-20260921'
MODELS=ROOT/'outputs/experimento-sem-monte-20260921'


def finite_number(value):
    try:
        v=float(value);return v if math.isfinite(v) else None
    except (TypeError,ValueError):return None


def component_conflict(row):
    q=finite_number(row.get('val_vazaodefluente'))
    values=[finite_number(row.get(k)) for k in COMPONENTS]
    return q==0 and all(v is not None for v in values) and sum(values)>1


def source_dependencies(times,flags,origins,delay_seconds=3600,max_age=5400):
    times=np.asarray(times);flags=np.asarray(flags,dtype=bool);origins=np.asarray(origins)
    if not len(times) or times.shape!=flags.shape or not np.all(np.diff(times)>0):
        raise ValueError('Unique increasing nonempty source times required')
    if delay_seconds<0 or max_age<0:raise ValueError('Nonnegative source delay/expiry required')
    needed=origins[:,None]-np.array([0,1,3,6])*3600-delay_seconds
    indices=np.searchsorted(times,needed,side='right')-1;safe=np.maximum(indices,0)
    usable=(indices>=0)&(needed-times[safe]<=max_age)
    return usable&flags[safe],np.where(usable,times[safe],np.nan)


def choose_forecast(reference,fallback,conflict):
    # Neither measured target nor prediction residual participates in selection.
    return fallback if conflict else reference


def run(out,protocol_path):
    protocol=json.loads(protocol_path.read_text())
    if protocol['lags_h']!=[0,1,3,6] or protocol['source_delay_seconds']!=3600 or protocol['max_age_seconds']!=5400:
        raise ValueError('Unsupported dependency policy')
    source_manifest=AUDIT/'source-manifest.json'
    paths=[source_manifest,MODELS/'predictions.csv',MODELS/'frozen-models.json',MODELS/'experiment.json',
           BASE/'telemetria-latencia.npz',BASE/'dados-roteamento.npz',protocol_path,Path(__file__),
           ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_upstream_audit.py']
    rows=[]
    for item in json.loads(source_manifest.read_text()):
        p=ROOT/item['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'];paths.append(p)
        with p.open() as f:
            for line,row in enumerate(csv.DictReader(f,delimiter=';'),2):
                if row['id_reservatorio'].strip()=='JIUHMC':
                    rows.append({**row,'source_path':str(p),'source_line':line})
    rows.sort(key=lambda r:epoch(r['din_instante']))
    t=np.array([epoch(r['din_instante']) for r in rows]);flags=np.array([component_conflict(r) for r in rows])
    d=dict(np.load(BASE/'dados-roteamento.npz'));z=dict(np.load(BASE/'telemetria-latencia.npz'));origins=d['times']
    impacts,used=source_dependencies(t,flags,origins);affected=impacts.any(axis=1)
    lookup={iso(at):bool(hit) for at,hit in zip(origins,affected)};trace=[]
    for i in np.where(affected)[0]:
        for j in np.where(impacts[i])[0]:
            offset=(0,1,3,6)[j];at=used[i,j];r=rows[int(np.searchsorted(t,at))]
            qtime=origins[i]-offset*3600;zi=int(np.searchsorted(z['times'],qtime))
            assert z['times'][zi]==qtime
            assert z['monte:Q'][zi]==float(r['val_vazaodefluente'])==0
            trace.append(dict(origin=iso(origins[i]),predictor_history_offset_h=offset,source_time=iso(at),
                              assumed_available_at=iso(at+3600),source_path=r['source_path'],source_line=r['source_line'],
                              raw_total_q_m3_s=float(r['val_vazaodefluente']),component_sum_m3_s=sum(float(r[k]) for k in COMPONENTS)))
    data=list(csv.DictReader((MODELS/'predictions.csv').open()))
    key=lambda r:(r['phase'],int(r['lead_h']),r['origin'],r['target_time'])
    old={key(r):r for r in data if r['family']=='level_and_slopes'}
    alternative={key(r):r for r in data if r['family']=='without_monte'}
    assert old.keys()==alternative.keys()
    result=[];unchanged=0;changed=0
    for k,r in old.items():
        alt=alternative[k];assert all(r[n]==alt[n] for n in ('actual_m3_s','high_flow'))
        selected=lookup[r['origin']]
        value=choose_forecast(r['forecast_m3_s'],alt['forecast_m3_s'],selected)
        unchanged+=value==r['forecast_m3_s'];changed+=value!=r['forecast_m3_s']
        result.append({**r,'family':'component_conflict_fallback','reference_m3_s':r['forecast_m3_s'],
                       'forecast_m3_s':value,'fallback_selected':selected})
    hashes={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    out.mkdir(parents=True,exist_ok=False);(out/'protocol.json').write_bytes(protocol_path.read_bytes())
    savecsv(out/'dependency-trace.csv',trace);savecsv(out/'predictions.csv',result)
    savecsv(out/'flagged-source-records.csv',[r for r,flag in zip(rows,flags) if flag])
    np.savez_compressed(out/'dependency-flags.npz',times=origins,affected=affected,by_lag=impacts,source_times=used)
    (out/'code').mkdir()
    for p in paths:
        if p.suffix=='.py':(out/'code'/p.name).write_bytes(p.read_bytes())
    for p,digest in hashes.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest
    dump(out/'experiment.json',dict(input_sha256=hashes,source_monte_records=len(rows),flagged_source_records=int(flags.sum()),
                                   affected_hourly_origins=int(affected.sum()),prediction_rows=len(result),
                                   changed_predictions=changed,unchanged_predictions=unchanged,
                                   validation_fallback_selected=sum(r['phase']=='validation' and r['fallback_selected'] for r in result),
                                   test_fallback_selected=sum(r['phase']=='test' and r['fallback_selected'] for r in result),
                                   models_fitted=0,promoted=False,live_issuance=False,goal_achieved=False,
                                   historical_availability_verified=False,official_source_invalidity_claim=False))
    print(json.dumps({'output':str(out),'flagged_sources':int(flags.sum()),'affected_origins':int(affected.sum()),'changed_predictions':changed}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path)
    p.add_argument('--protocol',type=Path,default=ROOT/'docs/component-fallback-protocol.json');a=p.parse_args();run(a.output,a.protocol)
