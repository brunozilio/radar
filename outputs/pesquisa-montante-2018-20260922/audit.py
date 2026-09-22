from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,datetime as dt,xml.etree.ElementTree as ET,math
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,o):p.write_text(json.dumps(o,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def numeric(s):
 try:v=float(s);return v if math.isfinite(v) else None
 except (TypeError,ValueError):return None
def ranges(times,step=900):
 groups=[]
 for t in times:
  if groups and (t-groups[-1][-1]).total_seconds()==step:groups[-1].append(t)
  else:groups.append([t])
 return [{'first_literal':g[0].isoformat(' '),'last_literal':g[-1].isoformat(' '),'slots':len(g)} for g in groups]
results=[];checks=[];receipts=[]
(R/'all-qc').mkdir(exist_ok=True)
for receipt in sorted((R/'raw').glob('*.receipt.json')):
 m=json.loads(receipt.read_text());p=R/m['file'];receipts.append(m)
 checks.append({'check':p.name+' sha256','passed':sha(p)==m['sha256']})
 root=ET.fromstring(p.read_bytes());raw=[]
 for i,e in enumerate(root.iter('DadosHidrometereologicos'),1):
  row={c.tag:c.text or '' for c in e};row['_provenance']={'source_file':m['file'],'source_sha256':m['sha256'],'xml_record_index_1based':i,'xml_attributes':e.attrib};raw.append(row)
 errors=[e.text for e in root.iter('Error')]
 rows=sorted(raw,key=lambda r:r['DataHora']);out=R/'all-qc'/p.with_suffix('.jsonl').name
 out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
 restored=[json.loads(s) for s in out.read_text().splitlines()]
 checks.append({'check':p.name+' all fields XML JSONL roundtrip','passed':sorted(restored,key=lambda r:r['_provenance']['xml_record_index_1based'])==raw})
 by=defaultdict(list)
 for r in rows:by[r['DataHora']].append(r)
 times=[dt.datetime.fromisoformat(r['DataHora']) for r in rows]
 start=dt.datetime.fromisoformat(m['start']);end=dt.datetime.fromisoformat(m['end'])+dt.timedelta(days=1)
 slots=[start+dt.timedelta(minutes=15*i) for i in range(int((end-start).total_seconds()/900))]
 def good(r):return numeric(r.get('NivelFinal')) is not None and r.get('CQ_NivelFinal')=='Dado aprovado'
 fields={}
 for f in sorted(set().union(*(r.keys() for r in rows)) if rows else []):
  if f.startswith(('_','CQ_')) or f in ['CodEstacao','DataHora']:continue
  vals=[(numeric(r.get(f)),r['DataHora'],r.get('CQ_'+f)) for r in rows];valid=[x for x in vals if x[0] is not None];approved=[x for x in valid if x[2]=='Dado aprovado']
  fields[f]={'absent':sum(f not in r for r in rows),'empty':sum(r.get(f)=='' for r in rows),'finite':len(valid),'nonempty_nonfinite':sum(r.get(f) not in ('',None) and numeric(r.get(f)) is None for r in rows),'finite_approved':len(approved),'qc':dict(Counter(r.get('CQ_'+f,'<absent>') for r in rows)),'zeros':sum(x[0]==0 for x in valid),'negatives':sum(x[0]<0 for x in valid),'approved_min':min(approved) if approved else None,'approved_discrete_max':max(approved) if approved else None}
 duplicates={t:len(rs) for t,rs in by.items() if len(rs)>1};conflicts={t:rs for t,rs in by.items() if len({json.dumps({k:v for k,v in r.items() if k!='_provenance'},sort_keys=True) for r in rs})>1}
 missing=[t for t in slots if t.isoformat(' ') not in by];missingapproved=[t for t in slots if not any(good(r) for r in by.get(t.isoformat(' '),[]))]
 summary={'station':m['station'],'start':m['start'],'end':m['end'],'url':m['url'],'source_file':m['file'],'sha256':m['sha256'],'http_status':m['http_status'],'status':'records' if rows else ('endpoint_sem_dados' if any('Sem dados' in (e or '') for e in errors) else 'failure_or_empty_unclassified'),'error_text':errors,'record_count':len(rows),'station_ids':sorted(set(r['CodEstacao'] for r in rows)),'first_literal':rows[0]['DataHora'] if rows else None,'last_literal':rows[-1]['DataHora'] if rows else None,'cadence_seconds':dict(Counter(str(int((b-a).total_seconds())) for a,b in zip(times,times[1:]))),'duplicates':duplicates,'conflicts':conflicts,'fields':fields,'quarter_hour':{'expected_slots':len(slots),'present':len(slots)-len(missing),'approved_level':len(slots)-len(missingapproved),'missing_record_ranges':ranges(missing),'missing_approved_level_ranges':ranges(missingapproved)},'exact_hour':{'expected_slots':sum(t.minute==0 for t in slots),'records':sum(t.minute==0 and t.isoformat(' ') in by for t in slots),'approved_level':sum(t.minute==0 and any(good(r) for r in by.get(t.isoformat(' '),[])) for t in slots)},'out_of_window':sum(t<start or t>=end for t in times),'off_quarter_grid':sum(t.minute%15!=0 or t.second!=0 for t in times),'qc_nonapproved_level_examples':[{'DataHora':r['DataHora'],'NivelFinal':r.get('NivelFinal'),'CQ_NivelFinal':r.get('CQ_NivelFinal'),'provenance':r['_provenance']} for r in rows if not good(r)][:12],'clock_datum_publication':'Unverified. Literal timestamps and raw values preserved; no offset, normalization or imputation applied.'}
 checks.extend([{'check':p.name+' identity or explicit station error','passed':summary['station_ids']==[m['station']] if rows else any(m['station'] in (e or '') for e in errors)},{'check':p.name+' rows in requested window','passed':summary['out_of_window']==0}])
 results.append(summary)
dump(R/'availability.json',results);dump(R/'source-manifest.json',receipts)
checks.append({'check':'bounded six requests','passed':len(receipts)==6})
dump(R/'verification.json',{'passed':all(c['passed'] for c in checks),'checks':checks,'request_count':len(receipts),'new_web_searches':0})
for s in results:print(s['station'],s['start'],s['status'],s['record_count'],s['fields'].get('NivelFinal'),s['exact_hour'])
print('checks',len(checks),all(c['passed'] for c in checks))
