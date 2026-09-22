"""Read frozen caches/XML; independently reconstruct rainfall delays and compare."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import ast,json,hashlib,math,xml.etree.ElementTree as ET
import numpy as np
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
RAW=ROOT/'outputs/mucum-propagacao-2026-09-21/raw'
BASE=ROOT/'outputs/mucum-atualizacao-15h-2026-09-21'
TZ=timezone(timedelta(hours=-3));ORIGIN=datetime(2026,9,21,15,tzinfo=TZ).timestamp()
iso=lambda t:datetime.fromtimestamp(float(t),TZ).isoformat()
inputs={}
def record(p):
    body=p.read_bytes();inputs[str(p.relative_to(ROOT))]={'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)};return body
def dump(name,value):(P/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def number(v):
    try:x=float(v)
    except (ValueError,TypeError):return np.nan
    return x if math.isfinite(x) and x>=0 else np.nan
def shift(a,n):
    if not n:return a.copy()
    out=np.full_like(a,np.nan)
    if n>0:out[n:]=a[:-n]
    else:out[:n]=a[-n:]
    return out
# Extract only the side-effect-free integrator. No operational module import.
src=ROOT/'scripts/hydro_rain_windows.py';tree=ast.parse(record(src));node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='observed_rain_windows')
scope={'np':np,'WINDOWS':[1,3,6,12,24,48]};exec(compile(ast.Module(body=[node],type_ignores=[]),str(src),'exec'),scope);integrate=scope['observed_rain_windows']
for name in ['hydro_latency_forecast.py','hydro_routing_data.py','hydro_routing_fit.py','hydro_precision_audit.py']:record(ROOT/'scripts'/name)
wp=ROOT/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json';weights=json.loads(record(wp));codes=sorted({c for g in weights for c in g['weights']})
zp=BASE/'telemetria-latencia.npz';record(zp);z=np.load(zp);grid=z['times'];assert grid[-1]==ORIGIN and np.all(np.diff(grid)==900)
stations=[];windows={}
for code in codes:
    cp=RAW/f'normalized-{code}.npz';record(cp);cache=np.load(cp);values={float(t):float(r) for t,r in zip(cache['times'],cache['rain'])};fp=BASE/'raw'/f'ana-{code}-fresh.xml';body=record(fp);fresh={};sourceqc={};negative=nonfinite=high=rejected=0
    for el in ET.fromstring(body).iter():
        if not el.tag.endswith('DadosHidrometereologicos'):continue
        row={x.tag.split('}')[-1]:x.text for x in el};ts=datetime.fromisoformat(row['DataHora']).replace(tzinfo=TZ).timestamp();v=number(row.get('ChuvaFinal'))
        if row.get('CQ_ChuvaFinal') not in ['Dado aprovado',None]:v=np.nan;rejected+=1
        if v>150:v=np.nan;high+=1
        fresh[ts]=float(v);sourceqc[ts]=row
    overwritten=sum(t in values for t in fresh);finite_to_missing=sum(t in values and np.isfinite(values[t]) and not np.isfinite(v) for t,v in fresh.items());values.update(fresh)
    tt=np.array(sorted(values));rr=np.array([values[t] for t in tt]);valid=(tt<=ORIGIN)&np.isfinite(rr);ix=np.where(valid)[0]
    if not len(ix):stations.append({'station':code,'error':'No finite rainfall <= origin'});continue
    last=float(tt[ix[-1]]);lag=ORIGIN-last;n=int(lag/900);source='fresh_xml' if last in fresh else 'normalized_cache';row=sourceqc.get(last)
    base=integrate(tt,rr,grid);windows[code]={w:(shift(v[0],n),shift(v[1],n)) for w,v in base.items()}
    station={'station':code,'last_finite_rain_at':iso(last),'last_rain_mm':float(rr[ix[-1]]),'delay_seconds':lag,'delay_minutes':lag/60,'shift_steps_15min':n,'effective_shift_seconds':n*900,'discarded_fractional_seconds':lag-n*900,'source_of_last':source,'source_path_of_last':str((fp if source=='fresh_xml' else cp).relative_to(ROOT)),'cache_path':str(cp.relative_to(ROOT)),'fresh_path':str(fp.relative_to(ROOT)),'fresh_rows':len(fresh),'fresh_finite':sum(np.isfinite(v) for v in fresh.values()),'fresh_nonfinite':sum(not np.isfinite(v) for v in fresh.values()),'fresh_qc_rejected':rejected,'fresh_above150':high,'fresh_overwritten_cache_timestamps':overwritten,'fresh_finite_to_missing_revisions':finite_to_missing,'merged_rows':len(tt),'merged_finite':int(np.isfinite(rr).sum()),'merged_nonfinite':int((~np.isfinite(rr)).sum()),'merged_nonfinite_after_last_until_origin':int(((tt>last)&(tt<=ORIGIN)&~np.isfinite(rr)).sum()),'last_raw_timestamp_in_xml':row.get('DataHora') if row else None,'last_raw_rain_in_xml':row.get('ChuvaFinal') if row else None,'last_raw_qc_in_xml':row.get('CQ_ChuvaFinal') if row else None}
    # Native np types must not obscure machine-readable output.
    station={k:int(v) if isinstance(v,np.integer) else v for k,v in station.items()};stations.append(station)
comparisons=[]
for group in weights:
    name=group['group']
    for w in [1,3,6,12,24,48]:
        if any(c not in windows for c in group['weights']):continue
        amount=sum(weight*np.nan_to_num(windows[c][w][0],nan=0) for c,weight in group['weights'].items());cover=sum(weight*np.nan_to_num(windows[c][w][1],nan=0) for c,weight in group['weights'].items());prediction=np.where(cover>=.5,amount,np.nan)
        for suffix,got in [(f'P{w}',prediction),(f'C{w}',cover)]:
            key=name+':'+suffix;expected=z[key];same=np.isclose(got,expected,rtol=0,atol=1e-10,equal_nan=True);finite=np.isfinite(got)&np.isfinite(expected);mask_equal=np.array_equal(np.isfinite(got),np.isfinite(expected));diff=np.abs(got[finite]-expected[finite]);mismatch=np.where(~same)[0]
            comparisons.append({'field':key,'rows':len(grid),'finite_overlap':int(finite.sum()),'finite_masks_equal':mask_equal,'exact_equal':bool(np.array_equal(got,expected,equal_nan=True)),'mismatches_gt1e10':len(mismatch),'max_abs_difference':float(diff.max()) if len(diff) else None,'samples':[{'at':iso(grid[i]),'reproduced':float(got[i]) if np.isfinite(got[i]) else None,'frozen':float(expected[i]) if np.isfinite(expected[i]) else None} for i in mismatch[:5]],'latest_reproduced':float(got[-1]) if np.isfinite(got[-1]) else None,'latest_frozen':float(expected[-1]) if np.isfinite(expected[-1]) else None})
dump('latencies.json',{'origin':iso(ORIGIN),'timezone_assumption':'UTC-03 consistent with frozen parser; not a new historical publication contract','merge_rule':'Normalized cache first; every fresh timestamp replaces cache even with missing/rejected precipitation; finite nonnegative ChuvaFinal with approved or absent QC, <=150mm','stations':stations})
dump('regional-comparison.json',{'audit_at_utc':datetime.now(timezone.utc).isoformat(),'grid_start':iso(grid[0]),'grid_end':iso(grid[-1]),'rows_per_field':len(grid),'compared_fields':len(comparisons),'all_exact':all(c['exact_equal'] for c in comparisons),'total_mismatches_gt1e10':sum(c['mismatches_gt1e10'] for c in comparisons),'comparisons':comparisons})
dump('source-manifest.json',inputs)
print('stations',len(stations),'all exact',all(c['exact_equal'] for c in comparisons),'fields',len(comparisons),'rows',len(grid))
for s in stations:print(s['station'],s.get('last_finite_rain_at'),s.get('delay_minutes'),s.get('shift_steps_15min'),s.get('discarded_fractional_seconds'),s.get('source_of_last'))
print('errors',[s for s in stations if 'error' in s])
