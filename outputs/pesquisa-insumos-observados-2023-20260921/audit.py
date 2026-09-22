"""Local inventory/QC only; preserves all raw values and no inferred fills."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
from collections import Counter
import json,hashlib,math,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent;ROOT=P.parents[1];plan=json.loads((P/'collection-plan.json').read_text());lo=datetime(2023,8,29);hi=datetime(2023,9,5);result=[];manifest=[]
def num(v):
    try:n=float(v)
    except (TypeError,ValueError):return None
    return n if math.isfinite(n) else None
def intervals(times,step):
    groups=[]
    for t in times:
        if groups and t-groups[-1][-1]==timedelta(seconds=step):groups[-1].append(t)
        else:groups.append([t])
    return [{'start':g[0].isoformat(),'end':g[-1].isoformat(),'slots':len(g)} for g in groups]
(P/'stations').mkdir(exist_ok=True)
for code in plan['stations']:
    meta=json.loads((P/'raw'/f'ana-{code}.source.json').read_text());manifest.append(meta);entry={'station':code,'http_status':meta.get('http_status'),'fields':{}};result.append(entry)
    if 'file' not in meta:entry['request_error']=meta;continue
    body=(P/meta['file']).read_bytes();assert hashlib.sha256(body).hexdigest()==meta['sha256'];tree=ET.fromstring(body);errors=[e.text for e in tree.iter() if e.tag.split('}')[-1]=='Error'];entry['source_errors']=errors
    rr=[];outside=[]
    for el in tree.iter():
        if el.tag.split('}')[-1]!='DadosHidrometereologicos':continue
        row={c.tag.split('}')[-1]:c.text for c in el};dt=datetime.fromisoformat(row['DataHora']);assert dt.tzinfo is None and row['CodEstacao']==code
        (rr if lo<=dt<hi else outside).append(row)
    rr.sort(key=lambda r:r['DataHora']);tt=[datetime.fromisoformat(r['DataHora']) for r in rr];unique=sorted(set(tt));entry.update(rows=len(rr),unique_timestamps=len(unique),duplicates=len(tt)-len(unique),outside_window_rows=len(outside),first=tt[0].isoformat() if tt else None,last=tt[-1].isoformat() if tt else None)
    with (P/'stations'/f'ana-{code}-all-qc.jsonl').open('w') as f:
        for row in rr:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    diff=Counter(int((b-a).total_seconds()) for a,b in zip(unique,unique[1:]));entry['timestamp_deltas_seconds']={str(k):v for k,v in sorted(diff.items())};entry['timestamp_second_counts']=dict(Counter(t.second for t in tt));entry['cadence_inferred_seconds']=diff.most_common(1)[0][0] if diff else None
    expected15=[lo+timedelta(minutes=15*i) for i in range(7*96)];missing15=[t for t in expected15 if t not in set(unique)];entry['quarter_hour_timestamp_slots']=672;entry['quarter_hour_grid_absent_count']=len(missing15);entry['quarter_hour_gaps']=intervals(missing15,900);entry['quarter_hour_count_is_not_universal_rain_denominator']=True
    cadence=entry['cadence_inferred_seconds']
    if cadence in (900,1800,3600) and unique:
        # Modal phase is diagnostic; do not round or shift source timestamps.
        phase=Counter(int((t-lo).total_seconds())%cadence for t in unique).most_common(1)[0][0];expected=[lo+timedelta(seconds=phase+i*cadence) for i in range(int((hi-lo).total_seconds()/cadence))];missing=[t for t in expected if t not in set(unique)];entry['modal_cadence_diagnostic']={'phase_seconds':phase,'expected_slots':len(expected),'present_on_grid':len(expected)-len(missing),'off_grid_records':sum(t not in set(expected) for t in unique),'missing_slots':len(missing),'gaps':intervals(missing,cadence)}
    for field in ['NivelFinal','VazaoFinal','ChuvaFinal','ChuvaAcumAdotada']:
        numeric=[r for r in rr if num(r.get(field)) is not None];approved=[r for r in numeric if r.get('CQ_'+field)=='Dado aprovado'];sus=[r for r in numeric if r.get('CQ_'+field)=='Dado suspeito'];compatible=[r for r in numeric if r.get('CQ_'+field) in ('Dado aprovado',None) and num(r[field])>=0 and (field!='ChuvaFinal' or num(r[field])<=150)];vals=[num(r[field]) for r in approved];entry['fields'][field]={'numeric':len(numeric),'empty':sum(r.get(field) is None for r in rr),'nonempty_nonnumeric':sum(r.get(field) is not None and num(r[field]) is None for r in rr),'approved_numeric':len(approved),'suspect_numeric':len(sus),'numeric_without_qc':sum(r.get('CQ_'+field) is None for r in numeric),'parser_compatible':len(compatible),'negative':sum(num(r[field])<0 for r in numeric),'qc_counts':dict(Counter(str(r.get('CQ_'+field)) for r in rr)),'approved_min_native_units':min(vals) if vals else None,'approved_max_native_units':max(vals) if vals else None,'first_approved':approved[0]['DataHora'] if approved else None,'last_approved':approved[-1]['DataHora'] if approved else None,'suspect_samples':[{k:r.get(k) for k in ['DataHora',field,'CQ_'+field]} for r in sus[:20]]}
    print(code,'rows',len(rr),'errors',errors,'H',entry['fields']['NivelFinal']['approved_numeric'],'P',entry['fields']['ChuvaFinal']['approved_numeric'],'cadence',cadence,flush=True)
for name,obj in [('source-manifest.json',manifest),('coverage.json',{'audited_at_utc':datetime.now(timezone.utc).isoformat(),'source_timestamps':'Original strings without timezone; any UTC−3 interpretation remains presumed','units':'ANA NivelFinal cm, ChuvaFinal mm under existing parser convention; raw responses preserved','collection_only':True,'no_training':True,'no_matrix':True,'stations':result})]:(P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
