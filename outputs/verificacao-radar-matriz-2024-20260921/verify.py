"""Independent read-only verification of a frozen Radar matrix; own outputs only."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import json,csv,hashlib,math,bisect
import numpy as np
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
M=ROOT/'outputs/radar-matriz-2024-20260921'
W=ROOT/'outputs/radar-insumos-2024-meteorologia-20260921'
H=ROOT/'outputs/radar-insumos-2024-hidrologia-20260921'
TZ=timezone(timedelta(hours=-3));ep=lambda s:datetime.fromisoformat(s).replace(tzinfo=TZ).timestamp();iso=lambda t:datetime.fromtimestamp(float(t),TZ).isoformat()
inputs={};checks=[]
def read(p):
    b=p.read_bytes();inputs[str(p.relative_to(ROOT))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def check(name,ok,detail=None):checks.append({'name':name,'passed':bool(ok),'detail':detail})
def eq(name,a,b,atol=0):
    a=np.asarray(a);b=np.asarray(b);same=a.shape==b.shape and np.allclose(a,b,rtol=0,atol=atol,equal_nan=True)
    check(name,same,{'shape_a':list(a.shape),'shape_b':list(b.shape),'atol':atol,'exact_equal':bool(a.shape==b.shape and np.array_equal(a,b,equal_nan=True)),'max_abs_diff':float(np.max(np.abs(a[np.isfinite(a)&np.isfinite(b)].astype(float)-b[np.isfinite(a)&np.isfinite(b)].astype(float)))) if a.shape==b.shape and np.any(np.isfinite(a)&np.isfinite(b)) else None})
def number(row):
    try:v=float(row.get('NivelFinal'))
    except (ValueError,TypeError):return float('nan')
    return v/100 if math.isfinite(v) and v>=0 and row.get('CQ_NivelFinal') in ('Dado aprovado',None) else float('nan')
def shift(a,n):
    if not n:return a.copy()
    b=np.full_like(a,np.nan)
    if n>0:b[n:]=a[:-n]
    else:b[:n]=a[-n:]
    return b
# Verify immutable matrix artifacts, and declared inputs independently.
manifest=json.loads(read(M/'artifact-hashes.json'))
for item in manifest:check('matrix_hash:'+item['file'],hashlib.sha256(read(M/item['file'])).hexdigest()==item['sha256'])
prep=json.loads(read(M/'preparation.json'))
for name,digest in prep['input_sha256'].items():check('input_hash:'+name,hashlib.sha256(read(ROOT/name)).hexdigest()==digest)
z=np.load(M/'features.npz');q=np.load(M/'quarter-hour.npz');t=z['times'];grid=q['times'];F=z['features']
eq('origin_grid',t,np.arange(ep('2024-04-01T00:00:00'),ep('2024-05-02T00:00:00'),3600))
eq('quarter_hour_grid',grid,np.arange(ep('2024-03-29T00:00:00'),ep('2024-05-02T00:00:00'),900))
check('feature_shape',F.shape==(744,180));check('no_duplicate_origins',len(np.unique(t))==len(t))
# Weather column mapping against an independently preserved collection-time audit.
models=['gfs_seamless','ecmwf_ifs025','icon_global'];widths=[3,6,9,12];weather=np.full((744,60),np.nan);seen=set()
for line in read(W/'window-coverage.jsonl').decode().splitlines():
    r=json.loads(line);i=bisect.bisect_left(t,ep(r['origin']));j=models.index(r['model'])*20+r['location']*4+widths.index(r['window_h']);assert t[i]==ep(r['origin']) and (i,j) not in seen;seen.add((i,j));assert r['complete'] and r['n_finite']==r['window_h'];weather[i,j]=r['sum_mm']
eq('all44640_weather_cells_vs_independent_audit',F[:,120:],weather,atol=1e-12);check('weather_audit_keys_complete',len(seen)==44640)
# Recompute weather from hourly payload timestamps independently; neither index shifting nor future observed rain.
weather_raw=np.empty_like(weather)
for mi,model in enumerate(models):
    payload=json.loads(read(W/'raw'/f'{model}.json'))
    for loc,v in enumerate(payload):
        lookup={ep(s):val for s,val in zip(v['hourly']['time'],v['hourly']['precipitation_previous_day1'])}
        for wi,w in enumerate(widths):
            weather_raw[:,mi*20+loc*4+wi]=[sum(lookup[o+h*3600] for h in range(1,w+1)) for o in t]
eq('all44640_weather_cells_vs_raw_hourly',F[:,120:],weather_raw,atol=1e-12)
# Exact source row selection, no fallback to older finite rows, finite/QC rules.
codes=['86510000','86472000','86472600','86500000'];delays=[900,1800,900,1800];truth_lookup={};level_arrays={};trace=[];frozen_trace=list(csv.DictReader(read(M/'level-source-trace.csv').decode().splitlines()))
for code,delay in zip(codes,delays):
    rr=[json.loads(line) for line in read(H/'stations'/f'ana-{code}-all-qc.jsonl').decode().splitlines()];tt=[ep(r['DataHora']) for r in rr];vv=[number(r) for r in rr];lookup=dict(zip(tt,vv))
    raw=np.array([lookup.get(o,np.nan) for o in grid]);delayed=[]
    for o in grid:
        cut=o-delay;j=bisect.bisect_right(tt,cut)-1;delayed.append(vv[j] if j>=0 and cut-tt[j]<=900 else np.nan)
    delayed=np.array(delayed);level_arrays[code]=delayed;eq('raw_level:'+code,q['raw:'+code+':H'],raw);eq('delayed_level:'+code,q[code+':H'],delayed)
    if code=='86510000':truth_lookup=lookup
    for o in t:
        cut=o-delay;j=bisect.bisect_right(tt,cut)-1;src=tt[j] if j>=0 else None;age=cut-src if src is not None else None;valid=j>=0 and age<=900 and math.isfinite(vv[j]);trace.append({'origin':iso(o),'station':code,'query_time':iso(cut),'source_time':iso(src) if src is not None else '', 'age_after_delay_seconds':str(float(age)) if age is not None else '', 'value_m':str(float(vv[j])) if valid else '', 'usable':str(bool(valid))})
    check('no_future_level_source:'+code,all(r['source_time']=='' or ep(r['source_time'])<=ep(r['query_time'])<ep(r['origin']) for r in trace if r['station']==code))
trace_key=lambda r:(r['station'],r['origin'])
check('all2976_level_trace_rows',sorted(trace,key=trace_key)==sorted(frozen_trace,key=trace_key))
at=np.searchsorted(grid,t);columns=[]
for code in codes:
    v=level_arrays[code];columns.append(v)
    for h in [.5,1,2,4,8]:columns.append((v-shift(v,int(h*4)))/h)
L=np.column_stack(columns)[at];eq('all17856_first24_cells',F[:,:24],L)
eq('base_is_delayed_mucum',z['base'],level_arrays['86510000'][at]);eq('truth_is_current_exact_mucum',z['truth'],[truth_lookup.get(o,np.nan) for o in t]);eq('complete24_mask',z['complete24'],np.isfinite(L).all(axis=1));check('carreiro_all_missing',np.isnan(F[:,18:24]).all());check('zero_complete24',not z['complete24'].any())
# Target arrays are not stored: verify the correct future shift and boundary counts.
target_checks=[]
for h in range(1,13):
    shifted=shift(z['truth'],-h);direct=np.array([truth_lookup.get(o+h*3600,np.nan) for o in t]);eq('target_alignment_h'+str(h),shifted,direct)
    target_checks.append({'horizon_h':h,'origins':len(t),'finite_future_targets':int(np.isfinite(direct).sum()),'missing_future_targets':int((~np.isfinite(direct)).sum()),'expected_finite':744-h,'last_finite_target':iso(t[np.where(np.isfinite(direct))[0][-1]]+h*3600)})
    check('target_cutoff_h'+str(h),np.isfinite(direct).sum()==744-h and np.isnan(direct[-h:]).all())
# Telemetry transformations from quarter-hour fields; no model execution.
cols=[x for x in columns]
for plant in ['julho','monte','castro']:
    flow=q[plant+':Q']/1000;transformed=np.maximum(flow,0)**.6;cols.extend([transformed,flow,q[plant+':I']/1000]);cols.extend([(transformed-shift(transformed,h*4))/h for h in [1,2,4,8]])
for group in ['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']:
    for h in [1,3,6,12,24,48]:cols.extend([q[group+f':P{h}'],q[group+f':C{h}']])
    cols.extend([shift(q[group+':P3'],h*4) for h in [3,6,12]])
eq('all89280_telemetry_cells_vs_quarter_hour',F[:,:120],np.column_stack(cols)[at])
# Independent ONS timestamp/value join, including literal23:59 and newest-NaN behavior.
ons=list(csv.DictReader(read(H/'ons-ceran-source-values.csv').decode().splitlines()));ons_columns=[];ons_traces=[];ons_summary=[]
for plant,code in [('julho','JIUHQJ'),('monte','JIUHMC'),('castro','JIUHCA')]:
    rr=sorted([r for r in ons if r['id_reservatorio'].strip()==code],key=lambda r:r['din_instante']);tt=[ep(r['din_instante']) for r in rr];check('ons_unique_source_times:'+plant,len(tt)==len(set(tt)))
    arrays={}
    for key,field in [('Q','val_vazaodefluente'),('I','val_vazaoafluente')]:
        vv=[float(r[field]) if r[field] else np.nan for r in rr]
        for delay,prefix in [(0,'raw:'),(3600,'')]:
            got=[]
            for o in grid:
                cut=o-delay;j=bisect.bisect_right(tt,cut)-1;age=cut-tt[j] if j>=0 else None;good=j>=0 and age<=5400;got.append(vv[j] if good else np.nan)
                if delay and o in set(t):
                    ons_traces.append({'plant':plant,'field':key,'origin':iso(o),'query_time':iso(cut),'source_time':iso(tt[j]) if j>=0 else '', 'age_after_query_seconds':age,'source_value':vv[j] if j>=0 and math.isfinite(vv[j]) else None,'usable':bool(good and math.isfinite(vv[j])),'source_row':j+1,'source_file':rr[j]['source_file'] if j>=0 else ''})
            got=np.array(got);eq('ons_source_join:'+prefix+plant+':'+key,q[prefix+plant+':'+key],got)
            if delay:arrays[key]=got
    flow=arrays['Q']/1000;power=np.maximum(flow,0)**.6;ons_columns.extend([power,flow,arrays['I']/1000]);ons_columns.extend([(power-shift(power,h*4))/h for h in [1,2,4,8]])
    traces=[r for r in ons_traces if r['plant']==plant];literal=[r for r in traces if r['source_time'] and r['source_time'][11:16]=='23:59'];usable=[r for r in traces if r['usable']]
    ons_summary.append({'plant':plant,'hourly_field_queries':len(traces),'usable':len(usable),'missing':len(traces)-len(usable),'selected_literal_2359':len(literal),'max_age_after_query_seconds_usable':max(r['age_after_query_seconds'] for r in usable),'max_total_source_age_seconds_usable':max(ep(r['origin'])-ep(r['source_time']) for r in usable),'literal_2359_examples':literal[:2]})
check('ons_no_future_sources',all(not r['source_time'] or ep(r['source_time'])<=ep(r['query_time'])<ep(r['origin']) for r in ons_traces));check('ons_expiry_after_delayed_query',all(not r['usable'] or r['age_after_query_seconds']<=5400 for r in ons_traces));eq('all15624_flow_features_vs_ONS_source',F[:,24:45],np.column_stack(ons_columns)[at])
(P/'ons-source-trace.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in ons_traces))
result={'audited_at_utc':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in checks),'check_count':len(checks),'failed_checks':[c for c in checks if not c['passed']],'checks':checks,'target_alignment':target_checks,'ons_source_checks':ons_summary,'no_refit':True,'no_pipeline_execution':True,'limits':['This verifies the preserved inputs and transformations; it does not certify original observation publication time or vertical reference.','Regional observed-rain aggregation was not independently reconstructed from ANA sources in this audit. Rain telemetry derivatives match quarter-hour; ONS flow features were independently reconstructed from source-values CSV, not original Parquet.','truth stores current H(O), not H(O+h); future training labels require a negative h shift and exclusion when target>=2024-05-02.','Fixed delays borrowed from2026 remain assumptions for2024; weather fixed-lead vintage is not individually certified.']}
(P/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n');(P/'source-manifest.json').write_text(json.dumps(inputs,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['passed','check_count','failed_checks','target_alignment']},indent=2))
