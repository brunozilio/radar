from pathlib import Path
from datetime import datetime,timedelta,timezone
from collections import Counter,defaultdict
from bisect import bisect_right
import json,csv,hashlib,math,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent;R=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(P/n).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def number(x):
 try:return float(x)
 except (TypeError,ValueError):return float('nan')
start=datetime(2024,6,15);end=datetime(2024,6,22)
expected=[start+timedelta(minutes=15*i) for i in range(672)]
plan=json.loads((P/'plan.json').read_text());summaries=[];traces=[];checks=[]
for spec in plan['stations']:
 code=spec['code'];p=P/f'raw/ana-{code}-20240615-20240621.xml';receipt=json.loads(Path(str(p)+'.receipt.json').read_text());checks.append(receipt['sha256']==sha(p))
 tree=ET.parse(p);raw=[{c.tag.split('}')[-1]:c.text for c in e} for e in tree.getroot().iter() if e.tag.split('}')[-1]=='DadosHidrometereologicos']
 errors=[e.text for e in tree.getroot().iter() if e.tag.split('}')[-1]=='Error']
 rec=[dict(r,source_file=str(p.relative_to(R)),source_sha256=sha(p),source_record_index=i+1) for i,r in enumerate(raw)]
 rec.sort(key=lambda r:(r['DataHora'],r['source_record_index']))
 out=P/f'ana-{code}-all-qc.jsonl';out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rec))
 checks.extend([{k:v for k,v in r.items() if k not in ['source_file','source_sha256','source_record_index']}==raw[r['source_record_index']-1] for r in rec]);checks.append(all(r['CodEstacao']==code for r in rec))
 times=[datetime.fromisoformat(r['DataHora']) for r in rec];unique=set(times);dups=defaultdict(list)
 for r in rec:dups[r['DataHora']].append(r)
 duplicates={k:v for k,v in dups.items() if len(v)>1}
 conflicts={k:v for k,v in duplicates.items() if len({json.dumps(raw[r['source_record_index']-1],sort_keys=True) for r in v})>1}
 save(f'ana-{code}-duplicates-conflicts.json',{'duplicates':duplicates,'conflicts':conflicts})
 fields={}
 for f in ('NivelFinal','NivelSensor','NivelManual','NivelDisplay'):
  finite=[r for r in rec if math.isfinite(number(r.get(f)))]; approved=[r for r in finite if r.get('CQ_'+f)=='Dado aprovado']
  vals=[number(r[f]) for r in approved]
  fields[f]={'field_omitted':sum(f not in r for r in rec),'null_or_nonfinite':len(rec)-len(finite),'finite':len(finite),'qc':dict(Counter(r.get('CQ_'+f) or '<empty>' for r in rec)),'finite_approved':len(approved),'negative':sum(number(r[f])<0 for r in finite),'zero':sum(number(r[f])==0 for r in finite),'approved_min':min(vals,default=None),'approved_max':max(vals,default=None),'approved_max_at':[r['DataHora'] for r in approved if number(r[f])==max(vals,default=None)]}
 both=[r for r in rec if math.isfinite(number(r.get('NivelFinal'))) and math.isfinite(number(r.get('NivelSensor')))]
 match=sum(number(r['NivelFinal'])==number(r['NivelSensor']) for r in both)
 for i in range(168):
  o=start+timedelta(hours=i);q=o-timedelta(minutes=spec['delay_minutes']);idx=bisect_right(times,q)-1
  picked=rec[idx] if idx>=0 else None;t=times[idx] if idx>=0 else None
  age=(q-t).total_seconds() if t is not None else None
  finite=picked is not None and math.isfinite(number(picked.get('NivelFinal')))
  approved=picked is not None and picked.get('CQ_NivelFinal')=='Dado aprovado'
  fresh=t is not None and age<=spec['max_age_after_query_minutes']*60
  eligible=fresh and finite and approved
  reason='available' if eligible else ('no_record_at_or_before_query' if picked is None else ('expired' if not fresh else ('missing_final_level' if not finite else 'qc_not_approved')))
  traces.append({'station':code,'name':spec['name'],'origin_literal':o.isoformat(' '),'query_literal':q.isoformat(' '),'source_time_literal':t.isoformat(' ') if t else '', 'age_after_query_seconds':age,'age_at_origin_seconds':(o-t).total_seconds() if t else None,'source_record_index':picked['source_record_index'] if picked else None,'final_level_original':picked.get('NivelFinal') if picked else None,'final_qc':picked.get('CQ_NivelFinal') if picked else None,'sensor_original':picked.get('NivelSensor') if picked else None,'sensor_qc':picked.get('CQ_NivelSensor') if picked else None,'source_file':str(p.relative_to(R)),'source_sha256':sha(p),'eligible_strict_level':eligible,'reason':reason})
 station_trace=[x for x in traces if x['station']==code]
 summaries.append({'station':code,'name':spec['name'],'response_status':'http_error' if receipt['http_status']!=200 else ('records' if rec else ('explicit_sem_dados' if any('Sem dados' in (e or '') for e in errors) else 'empty_other')),'http_status':receipt['http_status'],'error_texts':errors,'records':len(rec),'unique_timestamps':len(unique),'first_literal':min(times).isoformat(' ') if times else None,'last_literal':max(times).isoformat(' ') if times else None,'cadence_seconds':dict(Counter(str(int((b-a).total_seconds())) for a,b in zip(times,times[1:]))),'expected_quarter_rows':672,'missing_quarter_timestamps':len(set(expected)-unique),'missing_exact_hour_timestamps':sum(start+timedelta(hours=i) not in unique for i in range(168)),'duplicates':len(duplicates),'conflicts':len(conflicts),'fields':fields,'final_sensor_both_finite':len(both),'final_sensor_equal':match,'anchor_origins':168,'anchor_eligible':sum(x['eligible_strict_level'] for x in station_trace),'anchor_reasons':dict(Counter(x['reason'] for x in station_trace)),'delay_minutes':spec['delay_minutes'],'max_age_after_query_minutes':spec['max_age_after_query_minutes']})
with (P/'anchor-source-trace.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=traces[0]);w.writeheader();w.writerows(traces)
save('summary.json',{'generated_utc':datetime.now(timezone.utc).isoformat(),'stations':summaries,'no_matrix_or_model':True,'units':'ANA original fields preserved. SantaTereza bulletin expressly cm; two timestamp comparisons below. No per-record unit or timezone in XML.','time_interpretation':'Literal timezone-naive source times; no DST conversion/rounding. Delay is experiment convention, not certified historic publication availability.','no_invalid_record_bypass':True})
# Primary identity and two contemporaneous level checks, without new GET.
rows=[json.loads(x) for x in (P/'ana-86472600-all-qc.jsonl').read_text().splitlines()]
lookup={r['DataHora']:r for r in rows};points=[]
for t,v in [('2024-06-17 22:00:00',1407.),('2024-06-20 07:00:00',817.)]:
 r=lookup.get(t);actual=number(r['NivelFinal']) if r else None;points.append({'timestamp_literal':t,'sgb_santa_tereza_cm':v,'ana_final':actual,'equal':v==actual})
 checks.extend(x['equal'] for x in points)
save('bulletin-comparison.json',points)
save('verification.json',{'passed':all(checks),'checks':len(checks),'xml_jsonl_roundtrip_records':sum(s['records'] for s in summaries),'asof_trace_rows':len(traces),'no_duplicates':all(s['duplicates']==0 for s in summaries),'no_conflicts':all(s['conflicts']==0 for s in summaries),'no_level_substitution':True})
print(json.dumps(summaries,ensure_ascii=False,indent=2))
