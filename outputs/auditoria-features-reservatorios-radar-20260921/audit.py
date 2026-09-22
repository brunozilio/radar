"""Reservoir feature provenance only: no training, HGE or operational imports."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from collections import Counter
import bisect,csv,json,hashlib,ast
import numpy as np

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
SRC=ROOT/'outputs/experimento-niveis-reservatorios-20260921'
RADAR=ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921'
TZ=timezone(timedelta(hours=-3));PLANTS={'julho':'JIUHQJ','monte':'JIUHMC','castro':'JIUHCA'};FIELDS=['val_nivelmontante','val_niveljusante']
def epoch(s):
    x=datetime.fromisoformat(s);return (x if x.tzinfo else x.replace(tzinfo=TZ)).timestamp()
def iso(t):return datetime.fromtimestamp(float(t),TZ).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def number(v):
    try:q=float(v)
    except (TypeError,ValueError):return np.nan
    return q if np.isfinite(q) else np.nan
def dump(name,x):(OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def save(name,rows):
    if not rows:return
    with (OUT/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
checks=[]
def check(name,value,**kwargs):checks.append(dict(name=name,passed=bool(value),**kwargs))
def eq(name,a,b,tol=0):
    a,b=np.asarray(a,dtype=float),np.asarray(b,dtype=float);same=a.shape==b.shape
    fin=np.isfinite(a)&np.isfinite(b) if same else np.array([],bool)
    error=float(np.max(abs(a[fin]-b[fin]))) if fin.any() else 0.
    check(name,same and np.array_equal(np.isnan(a),np.isnan(b)) and error<=tol,max_abs_difference=error,finite_values=int(fin.sum()),tolerance=tol)

meta=json.loads((SRC/'experiment.json').read_text());manifest=json.loads((SRC/'artifact-hashes.json').read_text())
for name in ['additional-features.npz','input-trace.csv','experiment.json','protocol.json','code/hydro_reservoir_level_experiment.py']:
    r=next(r for r in manifest if r['file']==name);check('artifact_hash:'+name,sha(SRC/name)==r['sha256'])
data=dict(np.load(SRC/'additional-features.npz'));radar=dict(np.load(RADAR/'features.npz'));t=data['times'];eq('exact_Radar_hourly_origins',t,radar['times'])
check('regular_hourly_grid',np.all(np.diff(t)==3600));check('24_columns',data['levels_and_slopes'].shape==(len(t),24))
original_trace=list(csv.DictReader((SRC/'input-trace.csv').open()));trace_lookup={(r['plant'],r['field'],r['origin']):r for r in original_trace}
check('trace_unique_and_complete',len(trace_lookup)==len(original_trace)==6*len(t))
raw_paths=[Path(p) for p in meta['input_sha256'] if Path(p).name.startswith('DADOS_HIDROLOGICOS_HO_')]
check('18_source_CSVs',len(raw_paths)==18)
source_rows={v:{} for v in PLANTS.values()};duplicates=[];source_manifest=[]
for p in raw_paths:
    check('raw_hash:'+p.name,sha(p)==meta['input_sha256'][str(p)])
    source_manifest.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size))
    for line,row in enumerate(csv.DictReader(p.open(),delimiter=';'),2):
        identity=row['id_reservatorio'].strip()
        if identity not in source_rows:continue
        at=epoch(row['din_instante'])
        if at in source_rows[identity]:duplicates.append(dict(identity=identity,time=row['din_instante'],path=str(p),line=line))
        source_rows[identity][at]=dict(row=row,file=str(p.relative_to(ROOT)),line=line)
check('no_duplicate_plant_timestamp',not duplicates,count=len(duplicates))
columns=[];names=[];audit_rows=[];feature_summary=[];special=[];trace_differences=[]
latest_nonfinite=0;available_2359=0;all_source_lags=[]
for plant,identity in PLANTS.items():
    mapping=source_rows[identity];stamps=sorted(mapping)
    for field in FIELDS:
        selected=np.full(len(t),np.nan);values=np.full(len(t),np.nan);reason_counts=Counter()
        for i,origin in enumerate(t):
            cutoff=origin-3600;j=bisect.bisect_right(stamps,cutoff)-1
            source=None if j<0 else mapping[stamps[j]];stamp=None if j<0 else stamps[j]
            age=None if stamp is None else cutoff-stamp
            value=np.nan if source is None else number(source['row'].get(field));time_ok=stamp is not None and 0<=age<=5400
            reason='no_prior_record' if stamp is None else 'expired_after_delayed_cutoff' if not time_ok else 'newest_nonfinite' if not np.isfinite(value) else 'usable'
            if stamp is not None:selected[i]=stamp
            if time_ok:values[i]=value
            reason_counts[reason]+=1
            tr=trace_lookup[plant,field,iso(origin)]
            expected_time='' if stamp is None else iso(stamp)
            ok=(tr['source_time']==expected_time and tr['assumed_available_before']==iso(cutoff) and (tr['usable']=='True')==(reason=='usable'))
            if stamp is None:ok &= tr['age_after_delay_minutes']==''
            else:ok &= float(tr['age_after_delay_minutes'])==age/60
            got=number(tr['value_m']);expected=values[i]
            ok &= (not np.isfinite(got) and not np.isfinite(expected)) or (np.isfinite(got) and got==expected)
            if not ok:trace_differences.append(dict(plant=plant,field=field,origin=iso(origin)))
            older_finite=''
            if reason=='newest_nonfinite':
                latest_nonfinite+=1
                for k in range(j-1,-1,-1):
                    if cutoff-stamps[k]>5400:break
                    if np.isfinite(number(mapping[stamps[k]]['row'].get(field))):older_finite=iso(stamps[k]);break
            rawtime='' if source is None else source['row']['din_instante']
            if reason=='usable':
                all_source_lags.append((origin-stamp)/60)
                if rawtime.endswith('23:59:00'):available_2359+=1
            r=dict(plant=plant,field=field,origin=iso(origin),delayed_cutoff=iso(cutoff),source_literal_time=rawtime,source_time_assumed_UTC_minus3=expected_time,source_file='' if source is None else source['file'],source_line='' if source is None else source['line'],raw_value='' if source is None else source['row'].get(field,''),value_m=float(values[i]) if np.isfinite(values[i]) else '',age_after_delay_minutes='' if age is None else age/60,total_age_at_origin_minutes='' if stamp is None else (origin-stamp)/60,reason=reason,older_finite_not_used=older_finite)
            audit_rows.append(r)
            if reason!='usable':special.append(r)
        for lag,kind,denominator in [(0,'level',1),(1,'change1',1),(3,'slope3',3),(6,'slope6',6)]:
            name=f'{plant}:{field}:{kind}';names.append(name)
            if lag:
                previous=np.r_[np.full(lag,np.nan),values[:-lag]];v=(values-previous)/denominator
                past_sources=np.r_[np.full(lag,np.nan),selected[:-lag]]
                check('strictly_past_derivative_endpoints:'+name,np.all(selected[np.isfinite(v)]<=t[np.isfinite(v)]-3600) and np.all(past_sources[np.isfinite(v)]<=t[np.isfinite(v)]-(lag+1)*3600))
            else:v=values
            columns.append(v)
            feature_summary.append(dict(column_index=len(columns)-1,Radar_appended_column_index=180+len(columns)-1,name=name,units='m' if lag==0 else 'm/h',finite=int(np.isfinite(v).sum()),missing=int((~np.isfinite(v)).sum()),minimum=float(np.nanmin(v)),maximum=float(np.nanmax(v))))
        check('only_past_source:'+plant+':'+field,np.all(selected[np.isfinite(selected)]<=t[np.isfinite(selected)]-3600))
        check('expiry_obeyed:'+plant+':'+field,np.all((t[np.isfinite(values)]-3600-selected[np.isfinite(values)])<=5400))
        source_manifest.append(dict(series=plant+':'+field,reason_counts=dict(reason_counts)))
reconstructed=np.column_stack(columns);eq('independent_24_features',reconstructed,data['levels_and_slopes'])
check('feature_names_order',names==meta['additional_feature_names']);check('input_trace_matches_every_source_selection',not trace_differences,differences=len(trace_differences))
check('no_origin_or_future_observation',min(all_source_lags)>=60,minimum_age_minutes=min(all_source_lags),maximum_age_minutes=max(all_source_lags))
# Boundary behavior using the preserved pure feature function, not its run/model imports.
code=(SRC/'code/hydro_reservoir_level_experiment.py').read_text();node=next(n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name=='prepare_levels')
def shift(a,h):
    v=np.full_like(a,np.nan);v[h:]=a[:-h];return v
scope=dict(np=np,PLANTS=PLANTS,FIELDS=FIELDS,epoch=epoch,iso=iso,shift=shift)
exec(compile(ast.Module(body=[node],type_ignores=[]),'<pure-level-feature-function>','exec'),scope)
def fixture(stamps):
    return [dict(id_reservatorio=identity,din_instante=ts,val_nivelmontante=v,val_niveljusante=v) for identity in PLANTS.values() for ts,v in stamps]
o=epoch('2026-07-01T03:00:00-03:00')
a,_,_=scope['prepare_levels'](fixture([('2026-07-01T00:30:00-03:00','10')]),[o])
b,_,_=scope['prepare_levels'](fixture([('2026-07-01T00:29:59-03:00','10')]),[o])
c,_,_=scope['prepare_levels'](fixture([('2026-07-01T01:00:00-03:00','10'),('2026-07-01T02:00:00-03:00',''),('2026-07-01T03:00:00-03:00','1000')]),[o])
check('expiry_inclusive_90min',np.all(a[:,::4]==10));check('expiry_rejects_90min_plus1sec',np.isnan(b[:,::4]).all());check('newest_nan_not_bypassed_or_future_used',np.isnan(c[:,::4]).all())
times=[epoch('2026-07-01T00:00:00-03:00'),epoch('2026-07-01T01:00:00-03:00')]
q,_,trace=scope['prepare_levels'](fixture([('2026-06-30T23:00:00-03:00','10'),('2026-06-30T23:59:00-03:00','20')]),times)
check('2359_literal_not_available_at_midnight',np.all(q[0,::4]==10) and np.all(q[1,::4]==20) and trace[1]['source_time']=='2026-06-30T23:59:00-03:00')
save('source-selection-trace.csv',audit_rows);save('missing-and-expired-selections.csv',special);save('feature-catalog.csv',feature_summary)
dump('source-manifest.json',source_manifest)
dump('verification.json',dict(passed=all(r['passed'] for r in checks),checks=checks,origins=len(t),columns=24,source_rows=sum(len(v) for v in source_rows.values()),trace_rows=len(audit_rows),available_2359_field_selections=available_2359,newest_nonfinite_field_selections=latest_nonfinite,total_missing_feature_cells=int((~np.isfinite(reconstructed)).sum()),total_finite_feature_cells=int(np.isfinite(reconstructed).sum()),time_contract={'assumed_timezone':'UTC-03','publication_delay_minutes':60,'max_age_after_delayed_cutoff_minutes':90,'maximum_policy_age_at_origin_minutes':150,'historical_publication_verified':False},limitations=['ONS timestamp/reference assumptions remain unverified; no live CERAN contract established by this audit.','Only input provenance audited. No model fit, inference experiment or HGE execution.','Known original 168.74m July downstream value is retained, without masks or repairs.']))
(OUT/'preserved-feature-builder.py').write_text(code)
dump('artifact-hashes.json',[dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'])
print(json.dumps(dict(passed=all(r['passed'] for r in checks),checks=len(checks),failed=[r for r in checks if not r['passed']],origins=len(t),source_rows=sum(len(v) for v in source_rows.values()),trace_rows=len(audit_rows),available_2359_field_selections=available_2359,newest_nonfinite_field_selections=latest_nonfinite,max_observed_age_minutes=max(all_source_lags)),ensure_ascii=False))
