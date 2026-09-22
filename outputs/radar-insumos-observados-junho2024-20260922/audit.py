"""Preserve ALL-QC fields, merge only fully identical records, audit source roundtrip."""
from pathlib import Path
from collections import Counter,defaultdict
import csv,json,hashlib,datetime as dt,xml.etree.ElementTree as ET,math
R=Path(__file__).resolve().parent;W=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,o):p.write_text(json.dumps(o,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def number(v):
 try:x=float(v);return x if math.isfinite(x) else None
 except (ValueError,TypeError):return None
def intervals(times,step):
 groups=[]
 for t in times:
  if groups and (t-groups[-1][-1]).total_seconds()==step:groups[-1].append(t)
  else:groups.append([t])
 return [{'start_literal':g[0].isoformat(' '),'end_literal':g[-1].isoformat(' '),'slots':len(g)} for g in groups]
plan=json.loads((R/'plan.json').read_text());manifest=json.loads((R/'source-manifest.json').read_text())
checks=[]
def ck(name,v):checks.append({'check':name,'passed':bool(v)})
ck('27 station scope',len(plan['stations'])==27)
ck('27 new +4 reused',len(manifest)==31 and sum(not s['reused'] for s in manifest)==27 and sum(s['reused'] for s in manifest)==4)
ck('frozen latency station list unchanged',sha(W/plan['weights_source'])==plan['weights_sha256'])
ck('requests registered before network',all(dt.datetime.fromisoformat(m['started_utc'])>=dt.datetime.fromisoformat(plan['registered_utc']) for m in manifest if not m['reused']))
ck('new request scope exactly plan',Counter((m['station'],m['window'],m['start'],m['end']) for m in manifest if not m['reused'])==Counter((m['station'],m['window'],m['start'],m['end']) for m in plan['new_requests']))
ck('27 preserved attempt records',len(list((R/'raw').glob('*.attempt.json')))==27)
pool=defaultdict(list);sourceaudit=[];record_lookup={};rawcount=0
for m in manifest:
 p=R/m['file'];ck(m['file']+' hash',sha(p)==m['sha256'])
 if m['reused']:ck(m['file']+' original hash',sha(W/m['original_source_path'])==m['sha256'])
 parse_error=None
 try:root=ET.fromstring(p.read_bytes());els=list(root.iter('DadosHidrometereologicos'));errors=[e.text for e in root.iter('Error')]
 except ET.ParseError as e:els=[];errors=[];parse_error=str(e)
 status='parsed' if els else ('no_data_api' if any('Sem dados' in (v or '') for v in errors) else ('http_failure' if m.get('http_status')!=200 else 'parse_or_other_empty'))
 sourceaudit.append({**m,'record_count':len(els),'parsed_status':status,'api_errors':errors,'parse_error':parse_error})
 local=[]
 for i,e in enumerate(els,1):
  values={c.tag:c.text for c in e};ref={'source_file':str(p.relative_to(W)),'source_sha256':m['sha256'],'source_record_index':i}
  record_lookup[(ref['source_file'],i)]=values;rawcount+=1
  row={**values,**ref,'source_references':[ref]};pool[(m['window'],m['station'])].append(row);local.append(values)
 ck(m['file']+' identity',all(r.get('CodEstacao')==m['station'] for r in local))
 ck(m['file']+' segment bounds',all(m['start']<=r['DataHora'][:10]<=m['end'] for r in local))
 dump(R/'source-status.json',sourceaudit)
summaries=[];fieldrows=[];conflicts=[];identicalmerged=0;allrefs=[];totalout=0;daily=[]
prov={'source_file','source_sha256','source_record_index','source_references','timestamp_conflict'}
for win in plan['windows']:
 for station in plan['stations']:
  key=(win['id'],station);raw=pool[key];dedup={}
  for row in raw:
   original={k:v for k,v in row.items() if k not in prov};signature=json.dumps(original,sort_keys=True,ensure_ascii=False)
   if signature in dedup:dedup[signature]['source_references'].extend(row['source_references']);identicalmerged+=1
   else:dedup[signature]=row
  rows=sorted(dedup.values(),key=lambda r:(r['DataHora'],r['source_file'],r['source_record_index']));by=defaultdict(list)
  for row in rows:by[row['DataHora']].append(row)
  ctimes=[t for t,rs in by.items() if len(rs)>1]
  for t in ctimes:
   for r in by[t]:r['timestamp_conflict']=True
   conflicts.append({'window':win['id'],'station':station,'DataHora':t,'records':by[t]})
  directory=R/'stations';directory.mkdir(parents=True,exist_ok=True);out=directory/f'ana-{station}-all-qc.jsonl'
  out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows));restored=[json.loads(l) for l in out.read_text().splitlines()];totalout+=len(rows)
  good_roundtrip=True
  for r in restored:
   values={k:v for k,v in r.items() if k not in prov}
   for ref in r['source_references']:
    refkey=(ref['source_file'],ref['source_record_index']);allrefs.append(refkey)
    good_roundtrip &= values==record_lookup[refkey]
  ck(str(out.relative_to(R))+' full XML dictionary roundtrip',good_roundtrip)
  times=sorted(dt.datetime.fromisoformat(t) for t in by);steps=Counter(int((b-a).total_seconds()) for a,b in zip(times,times[1:]));mode=steps.most_common(1)[0][0] if steps else None
  start=dt.datetime.fromisoformat(win['start']);stop=dt.datetime.fromisoformat(win['end'])+dt.timedelta(days=1)
  fields={}
  for f in ['NivelFinal','ChuvaFinal','VazaoFinal','NivelSensor','NivelDisplay','NivelManual','ChuvaAcumAdotada']:
   numeric=[r for r in rows if number(r.get(f)) is not None];approved=[r for r in numeric if r.get('CQ_'+f)=='Dado aprovado'];values=[number(r[f]) for r in numeric]
   stat={'field_absent':sum(f not in r for r in rows),'empty':sum(f in r and r[f] in (None,'') for r in rows),'finite':len(numeric),'finite_approved':len(approved),'finite_other_qc':len(numeric)-len(approved),'nonempty_nonfinite':sum(r.get(f) not in (None,'') and number(r.get(f)) is None for r in rows),'negative':sum(v<0 for v in values),'zero_reported':sum(v==0 for v in values),'qc':dict(Counter(r.get('CQ_'+f,'<absent>') for r in rows))}
   fields[f]=stat;fieldrows.append({'window':win['id'],'station':station,'field':f,**{k:v for k,v in stat.items() if k!='qc'},'qc_json':json.dumps(stat['qc'],ensure_ascii=False)})
  grids={}
  for step in [900,3600]:
   expected=[start+dt.timedelta(seconds=step*i) for i in range(int((stop-start).total_seconds()/step))];missing=[t for t in expected if t.isoformat(' ') not in by]
   grids[str(step)]={'expected':len(expected),'timestamps_present':len(expected)-len(missing),'missing_ranges':intervals(missing,step),'finite_approved_level_at_timestamp':sum(any(number(r.get('NivelFinal')) is not None and r.get('CQ_NivelFinal')=='Dado aprovado' for r in by.get(t.isoformat(' '),[])) for t in expected),'finite_approved_rain_at_timestamp':sum(any(number(r.get('ChuvaFinal')) is not None and r.get('CQ_ChuvaFinal')=='Dado aprovado' for r in by.get(t.isoformat(' '),[])) for t in expected)}
  for day in range((stop-start).days):
   label=(start+dt.timedelta(days=day)).date().isoformat();rs=[r for r in rows if r['DataHora'].startswith(label)]
   daily.append({'window':win['id'],'station':station,'day':label,'records':len(rs),'approved_level':sum(number(r.get('NivelFinal')) is not None and r.get('CQ_NivelFinal')=='Dado aprovado' for r in rs),'approved_rain':sum(number(r.get('ChuvaFinal')) is not None and r.get('CQ_ChuvaFinal')=='Dado aprovado' for r in rs)})
  summaries.append({'window':win['id'],'station':station,'raw_records':len(raw),'output_records':len(rows),'distinct_timestamps':len(by),'identical_records_merged':len(raw)-len(rows),'conflicting_timestamps':ctimes,'first_literal':min(by) if by else None,'last_literal':max(by) if by else None,'modal_step_seconds':mode,'step_counts':dict(steps),'fields':fields,'grids':grids,'source_status_counts':dict(Counter(s['parsed_status'] for s in sourceaudit if s['station']==station and s['window']==win['id'])),'series_file':str(out.relative_to(R)),'series_sha256':sha(out),'clock_datum_publication':'Unverified; original literal values/timestamps retained. No imputation or timezone/latency transformation.'})
  summaries[-1]['off_hour_timestamps']=[t.isoformat(' ') for t in times if t.minute!=0 or t.second!=0]
  summaries[-1]['off_quarter_hour_timestamps']=[t.isoformat(' ') for t in times if t.minute%15!=0 or t.second!=0]
ck('each source record represented once',Counter(allrefs)==Counter(record_lookup.keys()))
ck('raw minus exact duplicate merges equals output',rawcount-identicalmerged==totalout)
ck('27 series output',len(summaries)==27)
for s in sourceaudit:ck(s['file']+' final source hash',sha(R/s['file'])==s['sha256'])
dump(R/'coverage.json',summaries);dump(R/'conflicts.json',conflicts)
for name,data in [('field-coverage.csv',fieldrows),('daily-coverage.csv',daily)]:
 with (R/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
result={'passed':all(c['passed'] for c in checks),'check_count':len(checks),'new_gets':27,'reused_sources':4,'source_count':31,'raw_records':rawcount,'output_records':totalout,'identical_records_merged':identicalmerged,'conflicting_timestamps':len(conflicts),'status_counts':dict(Counter(s['parsed_status'] for s in sourceaudit)),'http_status_counts':dict(Counter(str(s.get('http_status')) for s in sourceaudit)),'checks':checks}
dump(R/'verification.json',result);print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
if not result['passed']:raise SystemExit(1)
