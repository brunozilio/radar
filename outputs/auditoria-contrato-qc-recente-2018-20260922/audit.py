"""Read-only reconstruction of ANA cache/fresh semantics and strict latest variants."""
from pathlib import Path
from collections import Counter
import csv,json,hashlib,datetime as dt,xml.etree.ElementTree as ET,math
import numpy as np
R=Path(__file__).resolve().parent;W=R.parents[1];RAW=W/'outputs/mucum-propagacao-2026-09-21/raw';B=W/'outputs/mucum-atualizacao-15h-2026-09-21';E=W/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921';TZ=dt.timezone(dt.timedelta(hours=-3));LEVELS=['86510000','86472000','86472600','86500000']
FIELDS={'level':'NivelFinal','rain':'ChuvaFinal'};sources=[];hashes={};checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):hashes[str(p.relative_to(W))]=sha(p);return p
def dump(p,o):p.write_text(json.dumps(o,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def iso(t):return dt.datetime.fromtimestamp(float(t),TZ).isoformat()
def ep(s):return dt.datetime.fromisoformat(s).replace(tzinfo=TZ).timestamp()
def value(r,field,strict):
 try:v=float(r.get(field))
 except (ValueError,TypeError):return np.nan
 if not math.isfinite(v) or v<0 or r.get('CQ_'+field) not in (('Dado aprovado',) if strict else ('Dado aprovado',None)) or (field=='ChuvaFinal' and v>150):return np.nan
 return v/100 if field=='NivelFinal' else v
def ck(name,b):checks.append({'check':name,'passed':bool(b)})
def same(a,b):return (np.isnan(a)&np.isnan(b))|(a==b)
def comparison(a,b,mask=None):
 good=~same(a,b)
 if mask is not None:good&=mask
 return {'different':int(good.sum()),'finite_to_missing':int((good&np.isfinite(a)&~np.isfinite(b)).sum()),'missing_to_finite':int((good&~np.isfinite(a)&np.isfinite(b)).sum()),'different_both_finite':int((good&np.isfinite(a)&np.isfinite(b)).sum())}
def asof(ts,v,q,age):
 ix=np.searchsorted(ts,q,side='right')-1;out=np.full(len(q),np.nan)
 if len(ts):valid=(ix>=0)&(q-ts[np.maximum(ix,0)]<=age);out[valid]=v[ix[valid]]
 return out,ix
def save(name,rows):
 if rows:
  with (R/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 (R/'strict-latest').mkdir(exist_ok=True);(R/'lineage').mkdir(exist_ok=True)
 weights=json.loads(use(W/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json').read_text());codes=sorted({c for g in weights for c in g['weights']});assert len(codes)==27
 z=dict(np.load(use(B/'telemetria-latencia.npz')));grid=z['times'];origin=grid[-1];features=dict(np.load(use(E/'features.npz')));et=json.loads(use(E/'experiment.json').read_text());ck('frozen telemetry hash',et['input_sha256'][str((B/'telemetria-latencia.npz').resolve())]==sha(B/'telemetria-latencia.npz'))
 provenance_script=use(W/'scripts/hydro_routing_data.py');use(E/'code/hydro_latency_forecast.py')
 contract={'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'fields':['NivelFinal','ChuvaFinal'],'stations':codes,'precedence':['ana-CODE-2025.xml','ana-CODE.xml','ana-CODE-latest.xml','mucum-atualizacao-15h/raw/ana-CODE-fresh.xml'],'strict_latest_rule':'Every last encountered literal timestamp record replaces earlier record field, including rejected/missing/nonfinite values, in source precedence then XML document order. No bypass. All timestamps retained.','strict_qc':'Only Dado aprovado; finite nonnegative, rain<=150mm; level cm to m. UTC-3 computational convention, not certified timezone.','legacy_cache_rule':'Per-field finite approved or absent-QC only replacement; invalid new values leave earlier finite value. Fresh rows replace all fields even NaN.','variants':'legacy reproduces existing semantic; strict_finite changes only QC gate while keeping finite-only historical replacement; strict_latest also changes historical revision precedence. Changes are distinct.','no_mutation':'Only own artifact folder written; caches, frozen telemetry, operation and source XML untouched','runtime':'No production module imports, no fit/inference/network'}
 dump(R/'reconstruction-contract.json',contract)
 summaries=[];invalidating=[];absent=[];sourceqc=[];diffrows=[];hourdiff=[]
 for code in codes:
  sourcepaths=[p for p in [RAW/f'ana-{code}-2025.xml',RAW/f'ana-{code}.xml',RAW/f'ana-{code}-latest.xml'] if p.exists()];fp=B/'raw'/f'ana-{code}-fresh.xml';assert fp.exists();cp=use(RAW/f'normalized-{code}.npz');cache=dict(np.load(cp))
  states={};cache_repro={};localcounts=Counter()
  # Each field stores three (value,source_id,index,QC) variants.
  empty=(np.nan,-1,-1,None)
  for position,p in enumerate(sourcepaths+[fp]):
   fresh=p==fp
   if fresh:
    ts=np.array(sorted(states))
    for key in FIELDS:
     vals=np.array([states[t][key][0][0] for t in ts]);ck(code+key+' cache timestamp alignment',np.array_equal(ts,cache['times']));cache_repro[key]=comparison(cache[key],vals) if np.array_equal(ts,cache['times']) else {'different':'unmatched_times'};ck(code+key+' reconstruct cache exact',cache_repro[key]['different']==0)
   sid=len(sources);use(p);sources.append({'source_id':sid,'station':code,'source_file':str(p.relative_to(W)),'sha256':sha(p),'role':'fresh' if fresh else p.name,'precedence_position':position})
   qcc=Counter();index=0
   for _,el in ET.iterparse(p,events=['end']):
    if el.tag.split('}')[-1]!='DadosHidrometereologicos':continue
    index+=1;r={c.tag.split('}')[-1]:c.text for c in el};t=ep(r['DataHora']);assert r['CodEstacao']==code
    state=states.setdefault(t,{k:[empty,empty,empty] for k in FIELDS})
    for key,field in FIELDS.items():
     qc=r.get('CQ_'+field);old=state[key];lv=value(r,field,False);sv=value(r,field,True);lp=(lv,sid,index,qc);sp=(sv,sid,index,qc);qcc[(field,str(qc))]+=1
     if np.isfinite(lv) and not np.isfinite(sv):
      absent.append({'station':code,'field':field,'timestamp_literal':r['DataHora'],'raw_value':r.get(field),'QC':qc,'source_file':str(p.relative_to(W)),'source_sha256':sources[sid]['sha256'],'source_record_index':index,'fresh':fresh})
     if not fresh and np.isfinite(old[0][0]) and not np.isfinite(lv):
      invalidating.append({'station':code,'field':field,'timestamp_literal':r['DataHora'],'retained_value':old[0][0],'retained_source_id':old[0][1],'retained_record_index':old[0][2],'new_raw_value':r.get(field),'new_QC':qc,'new_source_id':sid,'new_record_index':index});localcounts[key+'_invalidating_skipped']+=1
     state[key]=[lp if fresh or np.isfinite(lv) else old[0],sp if fresh or np.isfinite(sv) else old[1],sp]
    el.clear()
   sources[sid]['xml_records']=index
   for (field,qc),count in qcc.items():sourceqc.append({'station':code,'source_id':sid,'field':field,'QC':qc,'records':count})
  ts=np.array(sorted(states));arr={'times':ts};lineage={'times':ts};report={'station':code,'records':len(ts),'cache_reproduction':cache_repro,'fields':{}}
  for key,field in FIELDS.items():
   variants=[]
   for j,name in enumerate(['legacy','strict_finite','strict_latest']):
    tuples=[states[t][key][j] for t in ts];v=np.array([x[0] for x in tuples]);variants.append(v);lineage[key+'_'+name]=v;lineage[key+'_'+name+'_source_id']=np.array([x[1] for x in tuples]);lineage[key+'_'+name+'_record_index']=np.array([x[2] for x in tuples]);lineage[key+'_'+name+'_qc']=np.array([x[3] or '<absent_or_empty>' for x in tuples]);lineage[key+'_'+name+'_qc_approved']=np.array([x[3]=='Dado aprovado' for x in tuples]);lineage[key+'_'+name+'_finite']=np.isfinite(v)
   legacy,strict_finite,strict_latest=variants;arr[key]=strict_latest;arr[key+'_finite']=np.isfinite(strict_latest);arr[key+'_qc_approved']=lineage[key+'_strict_latest_qc_approved'];arr[key+'_source_id']=lineage[key+'_strict_latest_source_id'];arr[key+'_source_record_index']=lineage[key+'_strict_latest_record_index'];arr[key+'_qc']=lineage[key+'_strict_latest_qc']
   ingrid=(ts>=grid[0])&(ts<=origin);pre=(ts>=grid[0])&(ts<ep('2026-07-01T00:00:00'));both=comparison(legacy,strict_latest,ingrid);qconly=comparison(legacy,strict_finite,ingrid)
   report['fields'][key]={'legacy_finite':int(np.isfinite(legacy).sum()),'strict_finite_finite':int(np.isfinite(strict_finite).sum()),'strict_latest_finite':int(np.isfinite(strict_latest).sum()),'legacy_to_strict_finite_in_grid':qconly,'legacy_to_strict_latest_in_grid':both,'legacy_to_strict_latest_preJuly':comparison(legacy,strict_latest,pre),'skipped_invalidating_revisions_events':localcounts[key+'_invalidating_skipped'],'legacy_surviving_finite_absent_qc_in_grid':int((ingrid&np.isfinite(legacy)&~lineage[key+'_legacy_qc_approved']).sum())}
   bad=np.where(ingrid&~same(legacy,strict_latest))[0]
   for i in bad:
    row={'station':code,'field':field,'timestamp_assumed_brt':iso(ts[i]),'legacy_value':float(legacy[i]) if np.isfinite(legacy[i]) else None,'strict_finite_value':float(strict_finite[i]) if np.isfinite(strict_finite[i]) else None,'strict_latest_value':float(strict_latest[i]) if np.isfinite(strict_latest[i]) else None,'legacy_source_id':int(lineage[key+'_legacy_source_id'][i]),'legacy_record_index':int(lineage[key+'_legacy_record_index'][i]),'legacy_QC':str(lineage[key+'_legacy_qc'][i]),'latest_source_id':int(lineage[key+'_strict_latest_source_id'][i]),'latest_record_index':int(lineage[key+'_strict_latest_record_index'][i]),'latest_QC':str(lineage[key+'_strict_latest_qc'][i])};diffrows.append(row)
   if key=='level' and code in LEVELS:
    exact,_=asof(ts,legacy,grid,0);ck(code+' frozen rawH exactly reproduced',np.array_equal(exact,z['raw:'+code+':H'],equal_nan=True));valid=(ts<=origin)&np.isfinite(legacy);lag=origin-ts[np.where(valid)[0][-1]];delayed,_=asof(ts,legacy,grid-lag,900);ck(code+' frozen delayedH exactly reproduced',np.array_equal(delayed,z[code+':H'],equal_nan=True));report['frozen_level_delay_seconds']=float(lag)
    newexact,_=asof(ts,strict_latest,grid,0);report['strict_latest_raw_grid_changes']=comparison(exact,newexact)
    hour=features['times'];hourlegacy,_=asof(ts,legacy,hour,0);hourstrict,_=asof(ts,strict_latest,hour,0);report['strict_latest_exact_hour_changes']=comparison(hourlegacy,hourstrict)
    if code=='86510000':
     ck('frozen Mu truth exactly reproduced',np.array_equal(hourlegacy,features['truth'],equal_nan=True));newbase,_=asof(ts,strict_latest,hour-3600,0);np.savez_compressed(R/'mucum-hourly-exact-60min.npz',times=hour,base=newbase,truth=hourstrict)
     report['mucum_experimental_base60_finite']=int(np.isfinite(newbase).sum());report['mucum_original_base15_finite']=int(np.isfinite(features['base']).sum())
    for i in np.where(~same(hourlegacy,hourstrict))[0]:hourdiff.append({'station':code,'timestamp_assumed_brt':iso(hour[i]),'legacy_level_m':float(hourlegacy[i]) if np.isfinite(hourlegacy[i]) else None,'strict_latest_level_m':float(hourstrict[i]) if np.isfinite(hourstrict[i]) else None})
  np.savez_compressed(R/'strict-latest'/f'ana-{code}.npz',**arr);np.savez_compressed(R/'lineage'/f'ana-{code}.npz',**lineage);summaries.append(report);print(code,'cache',cache_repro,'level changes',report['fields']['level']['legacy_to_strict_latest_in_grid']['different'],'rain changes',report['fields']['rain']['legacy_to_strict_latest_in_grid']['different'],flush=True)
  dump(R/'station-summary.json',summaries);dump(R/'source-index.json',sources)
 save('invalidating-revisions-skipped.csv',invalidating);save('finite-absent-qc-records.csv',absent);save('source-qc-counts.csv',sourceqc);save('legacy-vs-strict-latest-differences.csv',diffrows);save('exact-hour-level-differences.csv',hourdiff)
 # Explicitly create empty reports if there are no matching observations.
 for name,rows in [('invalidating-revisions-skipped.csv',invalidating),('finite-absent-qc-records.csv',absent),('legacy-vs-strict-latest-differences.csv',diffrows),('exact-hour-level-differences.csv',hourdiff)]:
  if not rows:(R/name).write_text('')
 for p,h in hashes.items():ck('source unchanged '+p,sha(W/p)==h)
 result={'passed':all(c['passed'] for c in checks),'check_count':len(checks),'checks':checks,'station_count':len(codes),'source_xml_count':len(sources),'invalidating_revision_events':len(invalidating),'finite_absent_qc_source_records':len(absent),'strict_latest_different_grid_values':len(diffrows),'exact_hour_level_differences':len(hourdiff),'source_sha256':hashes,'grid_start':iso(grid[0]),'grid_end':iso(grid[-1]),'hourly_rows':len(features['times']),'network':False,'fit':False,'inference':False,'operational_mutation':False}
 dump(R/'verification.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('checks','source_sha256')},indent=2))
if __name__=='__main__':main()
