"""Offline27station ALL-QC normalization and literal ONS references; no matrix."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
from collections import Counter,defaultdict
import csv,json,hashlib,math,xml.etree.ElementTree as ET
import numpy as np
P=Path(__file__).resolve().parent;ROOT=P.parents[1];plan=json.loads((P/'collection-plan.json').read_text());lo=datetime(2023,8,29);hi=datetime(2023,10,1);stations={c:[] for c in plan['stations']};manifest=[];summaries=[];fields=['NivelFinal','VazaoFinal','ChuvaFinal','ChuvaAcumAdotada']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def num(x):
    try:v=float(x)
    except (ValueError,TypeError):return None
    return v if math.isfinite(v) else None
def gaps(times,seconds):
    groups=[]
    for t in times:
        if groups and t-groups[-1][-1]==timedelta(seconds=seconds):groups[-1].append(t)
        else:groups.append([t])
    return [{'start':str(g[0]),'end':str(g[-1]),'slots':len(g)} for g in groups]
sources=plan['reused']+[json.loads((P/j['file']).with_suffix('.source.json').read_text()) for j in plan['new_jobs']]
for item in sources:
    meta=dict(item);manifest.append(meta)
    if 'source_path' not in item:meta['audit_status']='request_failed_or_incomplete';continue
    path=ROOT/item['source_path'];assert sha(path)==item['sha256'];tree=ET.parse(path).getroot();errors=[e.text for e in tree.iter() if e.tag.split('}')[-1]=='Error'];meta['source_errors']=errors;retained=outside=0
    for n,e in enumerate((e for e in tree.iter() if e.tag.split('}')[-1]=='DadosHidrometereologicos'),1):
        row={c.tag.split('}')[-1]:c.text for c in e};assert row['CodEstacao']==item['station'];t=datetime.fromisoformat(row['DataHora']);assert t.tzinfo is None
        if not lo<=t<hi:outside+=1;continue
        assert item['start']<=t.date().isoformat()<=item['end']
        row.update(source_file=item['source_path'],source_sha256=item['sha256'],source_record_index=n);stations[item['station']].append(row);retained+=1
    meta.update(audit_status='no_data_api' if errors else 'parsed' if retained else 'empty_response',rows_retained=retained,rows_outside_window=outside)
(P/'stations').mkdir(exist_ok=True)
for code,rows in stations.items():
    rows.sort(key=lambda r:r['DataHora']);tt=[datetime.fromisoformat(r['DataHora']) for r in rows];assert len(tt)==len(set(tt)),f'Duplicate source time for{code}:requires review'
    with (P/'stations'/f'ana-{code}-all-qc.jsonl').open('w') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    # Numeric normalization without eligibility filtering; preserve negative/suspect as raw value + QC.
    vals={};mapping={'NivelFinal':('level_m_raw',100),'VazaoFinal':('flow_m3s_raw',1),'ChuvaFinal':('rain_mm_raw',1),'ChuvaAcumAdotada':('counter_mm_raw',1)}
    for field,(key,scale) in mapping.items():vals[key]=np.array([num(r.get(field))/scale if num(r.get(field)) is not None else np.nan for r in rows],dtype=float);vals[field+'_qc']=np.array([r.get('CQ_'+field) or '' for r in rows],dtype=str)
    np.savez_compressed(P/'stations'/f'ana-{code}-normalized-all-qc.npz',time_original=np.array([r['DataHora'] for r in rows],dtype=str),source_file=np.array([r['source_file'] for r in rows],dtype=str),source_record_index=np.array([r['source_record_index'] for r in rows],dtype=int),**vals)
    diff=Counter(int((b-a).total_seconds()) for a,b in zip(tt,tt[1:]));mode=diff.most_common(1)[0][0] if diff else None;summary={'station':code,'records':len(rows),'first':str(tt[0]) if tt else None,'last':str(tt[-1]) if tt else None,'duplicates':0,'source_timezones_certified':False,'delta_seconds_counts':dict(sorted(diff.items())),'modal_cadence_seconds':mode,'seconds_counts':dict(Counter(t.second for t in tt)),'fields':{}}
    quarter=[lo+timedelta(minutes=15*i) for i in range(33*96)];missing=[t for t in quarter if t not in set(tt)];summary['quarter_hour_diagnostic']={'expected':3168,'absent':len(missing),'warning':'Not a universal denominator for hourly rain stations','gaps':gaps(missing,900)}
    if mode in (900,1800,3600) and tt:
        phase=Counter(int((t-lo).total_seconds())%mode for t in tt).most_common(1)[0][0];expected=[lo+timedelta(seconds=phase+i*mode) for i in range(int((hi-lo).total_seconds()/mode))];missing=[t for t in expected if t not in set(tt)];summary['modal_grid_diagnostic']={'step_seconds':mode,'phase_seconds':phase,'expected':len(expected),'present':len(expected)-len(missing),'off_grid':sum(t not in set(expected) for t in tt),'absent':len(missing),'gaps':gaps(missing,mode)}
    for field in fields:
        numeric=[r for r in rows if num(r.get(field)) is not None];approved=[r for r in numeric if r.get('CQ_'+field)=='Dado aprovado'];compatible=[r for r in numeric if r.get('CQ_'+field) in ['Dado aprovado',None] and num(r[field])>=0 and (field!='ChuvaFinal' or num(r[field])<=150)];empty=[datetime.fromisoformat(r['DataHora']) for r in rows if r.get(field) is None]
        summary['fields'][field]={'numeric':len(numeric),'empty':len(empty),'nonempty_nonnumeric':sum(r.get(field) is not None and num(r.get(field)) is None for r in rows),'approved_numeric':len(approved),'suspect_numeric':sum(r.get('CQ_'+field)=='Dado suspeito' for r in numeric),'numeric_without_qc':sum(r.get('CQ_'+field) is None for r in numeric),'parser_compatible':len(compatible),'negative':sum(num(r[field])<0 for r in numeric),'qc_counts':dict(Counter(str(r.get('CQ_'+field)) for r in rows)),'approved_min_native_units':min(num(r[field]) for r in approved) if approved else None,'approved_max_native_units':max(num(r[field]) for r in approved) if approved else None,'first_approved':approved[0]['DataHora'] if approved else None,'last_approved':approved[-1]['DataHora'] if approved else None,'empty_intervals_at_modal_cadence':gaps(empty,mode or 900)}
    summaries.append(summary);print(code,len(rows),'Happroved',summary['fields']['NivelFinal']['approved_numeric'],'Papproved',summary['fields']['ChuvaFinal']['approved_numeric'],'cadence',mode,flush=True)
# Reference existing CSV literal timestamp columns only. Ignore prior interpreted columns.
ons=[]
for folder,filename,month in [('historico-ceran-2023-complemento-20260921','ceran-source-values.csv','2023-08'),('historico-cheia-setembro-2023','ons-ceran-source-values.csv','2023-09')]:
    root=ROOT/'outputs'/folder;path=root/filename;am=json.loads((root/'artifact-hashes.json').read_text());entry=next(r for r in am if r.get('file',r.get('path'))==filename);assert sha(path)==entry['sha256'];rr=[r for r in csv.DictReader(path.open()) if r['din_instante'].startswith(month)];plants={}
    for code in ['JIUHQJ','JIUHMC','JIUHCA']:
        sub=[r for r in rr if r['id_reservatorio'].strip()==code];literal=[r['din_instante'] for r in sub];plants[code]={'records':len(sub),'unique_timestamps':len(set(literal)),'first':min(literal) if literal else None,'last':max(literal) if literal else None,'literal2359':sum('23:59' in t for t in literal)}
    source_manifest=json.loads((root/'source-manifest.json').read_text());rawref=next(r for r in source_manifest if ('2023_08' in r.get('file','') if month=='2023-08' else r.get('file')=='raw/ons-2023-09.parquet'));rawpath=root/rawref['file'];assert sha(rawpath)==rawref['sha256'];ons.append({'month':month,'literal_csv':str(path.relative_to(ROOT)),'csv_sha256':sha(path),'csv_manifest':str((root/'artifact-hashes.json').relative_to(ROOT)),'csv_manifest_sha256':sha(root/'artifact-hashes.json'),'raw_source_path':str(rawpath.relative_to(ROOT)),'raw_source_sha256':sha(rawpath),'raw_source_url':rawref['url'],'raw_metadata':rawref,'plants':plants,'timestamp_column_used':'din_instante','interpreted_columns_ignored':True,'no_new_request':True})
dump(P/'source-manifest.json',manifest);dump(P/'ons-references.json',ons);dump(P/'coverage.json',{'audited_at_utc':datetime.now(timezone.utc).isoformat(),'window_start':str(lo),'window_end_exclusive':str(hi),'new_get_requests':len(plan['new_jobs']),'reused_XMLs':len(plan['reused']),'statuses':dict(Counter(r['audit_status'] for r in manifest)),'normalized_series':len(summaries),'normalization':'Literal datetime strings; cm to m only for level; numeric values including negative/suspect kept together with original QC. NaN represents absent/non-numeric value; JSONL retains original text. No QC eligibility filter or interpolation applied.','stations':summaries})
