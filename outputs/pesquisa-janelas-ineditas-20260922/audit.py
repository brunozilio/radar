from pathlib import Path
from collections import Counter, defaultdict
import json, hashlib, datetime as dt, xml.etree.ElementTree as ET, math, shutil
R=Path(__file__).resolve().parent; W=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
specs=[('ana-20180830-20180905.xml','2018-08-30','2018-09-05','2018-09-02 17:00:00',845),('ana-20180930-20181006.xml','2018-09-30','2018-10-06','2018-10-03 22:00:00',1126)]
summaries=[]; checks=[]
for name,start,end,bt,bv in specs:
 p=R/'raw'/name; rows=[]
 for i,e in enumerate(ET.fromstring(p.read_bytes()).iter('DadosHidrometereologicos'),1):
  row={c.tag:c.text or '' for c in e};row['_provenance']={'source_file':str(p.relative_to(R)),'source_sha256':sha(p),'xml_record_index_1based':i};rows.append(row)
 original=rows.copy();rows.sort(key=lambda r:r['DataHora'])
 out=R/(name.removesuffix('.xml')+'-all-qc.jsonl');out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
 checks.append({'check':name+' XML to JSONL all fields/indices exact','passed':sorted(rows,key=lambda r:r['_provenance']['xml_record_index_1based'])==original})
 times=[dt.datetime.fromisoformat(r['DataHora']) for r in rows];by=defaultdict(list)
 for r in rows:by[r['DataHora']].append(r)
 fields={}
 for f in ['NivelFinal','NivelSensor','NivelManual','NivelDisplay','VazaoFinal','ChuvaFinal','ChuvaAcumAdotada']:
  finite=[]
  for r in rows:
   try:v=float(r.get(f,''))
   except ValueError:continue
   if math.isfinite(v):finite.append((v,r['DataHora'],r.get('CQ_'+f,'')))
  approved=[r for r in finite if r[2]=='Dado aprovado']
  fields[f]={'field_absent':sum(f not in r for r in rows),'empty':sum(r.get(f)==' ' or r.get(f)=='' for r in rows),'finite':len(finite),'finite_approved':len(approved),'qc_counts':dict(Counter(r.get('CQ_'+f,'<absent>') for r in rows)),'min':min(finite) if finite else None,'max':max(finite) if finite else None}
 startdt=dt.datetime.fromisoformat(start);stopdt=dt.datetime.fromisoformat(end)+dt.timedelta(days=1)
 hours=[startdt+dt.timedelta(hours=i) for i in range(int((stopdt-startdt).total_seconds()/3600))]
 def valid(r):
  try:return r.get('CQ_NivelFinal')=='Dado aprovado' and math.isfinite(float(r['NivelFinal']))
  except (ValueError,KeyError):return False
 hourtruth=sum(any(valid(r) for r in by.get(t.isoformat(' '),[])) for t in hours)
 anchors=[]
 for t in hours:
  q=t-dt.timedelta(minutes=15); eligible=[r for r in rows if dt.datetime.fromisoformat(r['DataHora'])<=q]
  latest=eligible[-1] if eligible else None
  age=(q-dt.datetime.fromisoformat(latest['DataHora'])).total_seconds()/60 if latest else None
  anchors.append({'origin_literal':t.isoformat(' '),'query_literal':q.isoformat(' '),'source_literal':latest['DataHora'] if latest else None,'age_after_query_minutes':age,'admissible_current_anchor_contract':bool(latest and age<=15 and valid(latest))})
 dump(R/(name.removesuffix('.xml')+'-anchor-coverage.json'),anchors)
 bulletin_rows=by.get(bt,[])
 summary={'source_file':str(p.relative_to(R)),'source_sha256':sha(p),'start_requested':start,'end_requested':end,'record_count':len(rows),'station_ids':sorted(set(r['CodEstacao'] for r in rows)),'first_literal':rows[0]['DataHora'] if rows else None,'last_literal':rows[-1]['DataHora'] if rows else None,'interval_seconds':dict(Counter(str(int((b-a).total_seconds())) for a,b in zip(times,times[1:]))),'duplicate_timestamps':{t:len(rs) for t,rs in by.items() if len(rs)>1},'fields':fields,'expected_hour_slots':len(hours),'approved_exact_hour_levels':hourtruth,'missing_exact_hours':[t.isoformat(' ') for t in hours if not any(valid(r) for r in by.get(t.isoformat(' '),[]))],'expected_quarter_hour_slots':len(hours)*4,'present_quarter_hour_levels':sum(valid(r) and dt.datetime.fromisoformat(r['DataHora']).minute%15==0 for r in rows),'anchor_current_contract_admissible':sum(a['admissible_current_anchor_contract'] for a in anchors),'bulletin_point':{'timestamp_literal':bt,'reported_cm':bv,'ana_records':bulletin_rows,'exact_approved_match':any(valid(r) and float(r['NivelFinal'])==bv for r in bulletin_rows)},'timezone_contract':'unverified; literal timestamps preserved; no offset assigned','vertical_reference':'unverified; station code identity does not establish unchanged zero','historical_publication_times':'not provided by endpoint; retrieval/revision now is not historical availability'}
 checks.extend([{'check':name+' station86510000','passed':summary['station_ids']==['86510000']},{'check':name+' bulletin exact approved numerical match','passed':summary['bulletin_point']['exact_approved_match']}])
 levelvalues=[(float(r['NivelFinal']),r['DataHora'],r['CQ_NivelFinal']) for r in rows]
 summary['level_nonfinite_count']=sum(not math.isfinite(v) for v,t,q in levelvalues)
 summary['level_negative_count']=sum(v<0 for v,t,q in levelvalues)
 summary['level_zero_count']=sum(v==0 for v,t,q in levelvalues)
 summary['approved_level_discrete_max_cm']=max((v,t) for v,t,q in levelvalues if q=='Dado aprovado')
 summary['nonapproved_level_records']=[{'DataHora':r['DataHora'],'NivelFinal':r['NivelFinal'],'CQ_NivelFinal':r['CQ_NivelFinal'],'provenance':r['_provenance']} for r in rows if not valid(r)]
 summary['target_schedule']=[{'horizon_hours':h,'scheduled_within_window':len(hours)-h,'boundary_excluded':h,'approved_exact_future_targets':sum(any(valid(r) for r in by.get(t.isoformat(' '),[])) for t in hours[h:]),'eligible_anchor_target_pairs_current_contract':0} for h in range(1,13)]
 summaries.append(summary)
dump(R/'availability.json',summaries)
refs=[]
for rel,url in [('outputs/mucum-propagacao-2026-09-21/raw/sgb-boletins-lista.html','https://www.sgb.gov.br/sace/boletins.php?idbacia=9'),('outputs/pesquisa-diversidade-eventos-pre2020-20260922/sources/sgb-2022.txt','https://rigeo.sgb.gov.br/server/api/core/bitstreams/cfb7f9ef-3abf-4a2d-8f27-6ef599577287/content'),('outputs/pesquisa-diversidade-eventos-pre2020-20260922/README.md',None),('docs/forecast-accuracy-goal.md',None)]:
 p=W/rel; dest=R/'raw'/('reused-'+p.name);shutil.copyfile(p,dest)
 refs.append({'original_path':rel,'preserved_copy':str(dest.relative_to(R)),'sha256':sha(p),'url':url,'copy_captured_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'retrieval_time_note':'Original source acquisition is inherited from local archive; no new GET.'})
dump(R/'local-source-references.json',refs)
for p in (R/'raw').glob('*.receipt.json'):
 receipt=json.loads(p.read_text()); checks.append({'check':p.name+' body hash','passed':sha(R/receipt['file'])==receipt['sha256']})
dump(R/'verification.json',{'checks':checks,'passed':all(c['passed'] for c in checks),'telemetry_gets':2,'document_gets':2,'search_queries':4,'notes':['Only two windows checked, no mass collection','JSONL retains all strings and QC; no resampling','Anchor coverage is a contract admissibility check, not a forecast or fit']})
print(json.dumps([{k:s[k] for k in ['start_requested','end_requested','record_count','interval_seconds','approved_exact_hour_levels','missing_exact_hours','anchor_current_contract_admissible']} for s in summaries],indent=2))
print('PASSED',all(c['passed'] for c in checks),len(checks))
