"""Independent full XML↔ALL-QC JSONL accounting plus grids/QC and attempt limits."""
from pathlib import Path
from datetime import datetime,timedelta
from collections import Counter,defaultdict
import json,hashlib,math,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def num(v):
 try:n=float(v)
 except (ValueError,TypeError):return None
 return n if math.isfinite(n) else None
checks=[]
def ok(name,v):assert v,name;checks.append(name)
plan=json.loads((P/'collection-plan.json').read_text());sources=json.loads((P/'source-manifest.json').read_text());cov=json.loads((P/'coverage.json').read_text());bycode={(s['year'],s['station']):s for s in cov['stations']};parsed={};metadata={};expected_refs=set();get_events=[];flags=[]
ok('135primarysources',len(sources)==135);ok('125new10reused',Counter(m['usage'] for m in sources)=={'primary_new':125,'primary_reuse':10})
for path,h in plan['reference_sha256'].items():ok('reference_unchanged:'+path,sha(ROOT/path)==h)
for m in sources:
 if m['usage']=='primary_new':
  ok('preregistered:'+m['file'],m['requested_at_utc']>plan['registered_at_utc']);ok('attempt_bound:'+m['file'],m['attempt_number']==1 and m['plan_sha256']==sha(P/'collection-plan.json'));get_events.extend([(m['requested_at_utc'],1),(m['finished_at_utc'],-1)])
 if 'source_file' not in m:continue
 path=m['source_file'];metadata[path]=m;ok('raw_hash:'+path,sha(ROOT/path)==m['sha256']);ok('bytes:'+path,(ROOT/path).stat().st_size==m['bytes']);tree=ET.parse(ROOT/path);rr=[{c.tag.split('}')[-1]:c.text for c in e} for e in tree.iter() if e.tag.split('}')[-1]=='DadosHidrometereologicos'];parsed[path]=rr;ok('source_count:'+path,len(rr)==m['record_count'])
 errors=[e.text for e in tree.iter() if e.tag.split('}')[-1]=='Error']
 ok('source_status:'+path,(len(rr)>0 and m['audit_status']=='parsed') or (not rr and any('sem dados' in str(e).lower() for e in errors) and m['audit_status']=='no_data_api'))
 for idx,r in enumerate(rr,1):
  t=datetime.fromisoformat(r['DataHora']);assert r['CodEstacao']==m['station'] and m['start']<=t.date().isoformat()<=m['end'] and t.tzinfo is None;expected_refs.add((path,idx))
active=maxactive=0
for time,change in sorted(get_events):active+=change;maxactive=max(active,maxactive);assert active>=0
ok('at_most_two_concurrent_requests',active==0 and maxactive<=2);ok('exactly125attempts',len(get_events)==250)
consumed=Counter();total=0;nc=0
for year in (2021,2022):
 lo=datetime(year,4,28);hi=datetime(year,6 if year==2021 else 7,1)
 for code in plan['stations']:
  path=P/'stations'/str(year)/f'ana-{code}-all-qc.jsonl';rr=[json.loads(x) for x in path.read_text().splitlines()];tt=[datetime.fromisoformat(r['DataHora']) for r in rr];ok(f'sorted_literal:{year}:{code}',tt==sorted(tt) and all(lo<=t<hi and t.tzinfo is None for t in tt));s=bycode[(year,code)];ok(f'counts:{year}:{code}',len(rr)==s['normalized_rows'] and len(set(tt))==s['unique_timestamps'])
  for r in rr:
   raw={k:v for k,v in r.items() if not k.startswith('source_')};primary={k:r[k] for k in ('source_file','source_sha256','source_record_index')};assert primary==r['source_references'][0]
   for ref in r['source_references']:
    f=ref['source_file'];idx=ref['source_record_index'];assert f in parsed and 1<=idx<=len(parsed[f]);assert raw==parsed[f][idx-1] and ref['source_sha256']==metadata[f]['sha256'];consumed[(f,idx)]+=1
   for field in s['fields']:
    value=num(r.get(field));qc=r.get('CQ_'+field)
    if value is not None and (value<0 or qc not in (None,'','Dado aprovado')):flags.append(dict(year=year,station=code,field=field,value_text=r[field],qc=qc,flags=(['negative_numeric'] if value<0 else [])+(['nonapproved_qc'] if qc not in (None,'','Dado aprovado') else []),record=r))
  ok(f'all_fields_provenance:{year}:{code}',True);total+=len(rr);nc+=1
  for field,fs in s['fields'].items():
   pairs=[(num(r.get(field)),r.get('CQ_'+field)) for r in rr];numeric=[(n,q) for n,q in pairs if n is not None];qc=dict(Counter(str(q) for _,q in pairs));assert qc==fs['qc_counts'];assert sum(n<0 for n,q in numeric)==fs['negative_numeric'];assert sum(q=='Dado aprovado' for n,q in numeric)==fs['approved_numeric'];assert sum(q=='Dado suspeito' for n,q in numeric)==fs['suspect_numeric'];assert sum(q in (None,'') for n,q in numeric)==fs['numeric_missing_qc'];assert sum(r.get(field) in (None,'') for r in rr)==fs['empty_values'];assert len(numeric)==fs['numeric'];ok(f'QC:{year}:{code}:{field}',True)
  for step,label in ((900,'exact_15min'),(3600,'exact_hour')):
   grid={lo+timedelta(seconds=step*i) for i in range(int((hi-lo).total_seconds())//step)};g=s['grids'][label];assert len(grid)==g['expected'] and len(grid&set(tt))==g['timestamp_present'] and len(set(tt)-grid)==g['off_grid_records']
   for field in s['fields']:
    good={t for t,r in zip(tt,rr) if num(r.get(field)) is not None and r.get('CQ_'+field)=='Dado aprovado'};assert len(grid&good)==g['fields'][field]['approved_numeric'];assert len(grid-good)==g['fields'][field]['unavailable_or_not_approved']
   ok(f'grid:{year}:{code}:{label}',True)
  diffs=Counter(int((b-a).total_seconds()) for a,b in zip(sorted(set(tt)),sorted(set(tt))[1:]));ok(f'cadence:{year}:{code}',{str(k):v for k,v in diffs.items()}==s['delta_seconds_counts'])
ok('54series',nc==54);ok('all_primary_records_accounted_exactly_once',set(consumed)==expected_refs and all(v==1 for v in consumed.values()));ok('retainedtotal',sum(consumed.values())==cov['retained_raw_records']==cov['all_primary_raw_records']);ok('normalizedtotal',total==cov['normalized_rows']);ok('no_records_discarded',cov['record_contract_anomalies']==cov['out_of_request_window']==0)
dup=json.loads((P/'duplicate-audit.json').read_text());ok('no_primary_duplicate_or_conflict',dup['identical_extra_records']==dup['conflicting_timestamps']==len(dup['duplicate_groups'])==0)
ov=plan['overlap_audit'];ok('probehash',sha(ROOT/ov['source_file'])==ov['sha256']);probe=json.loads((P/'probe-overlap-audit.json').read_text());pr=[{c.tag.split('}')[-1]:c.text for c in e} for e in ET.parse(ROOT/ov['source_file']).iter() if e.tag.split('}')[-1]=='DadosHidrometereologicos'];monthly={r['DataHora']:r for f,rr in parsed.items() if metadata[f]['station']=='86510000' and metadata[f]['year']==2022 for r in rr};same=sum(monthly.get(r['DataHora'])==r for r in pr);ok('probe_match96',same==len(pr)==probe['records']==probe['identical']==96);ok('probe_not_in_canonical',ov['source_file'] not in {f for f,i in consumed})
with (P/'numeric-qc-flags.jsonl').open('w') as f:
 for r in flags:f.write(json.dumps(r,ensure_ascii=False)+'\n')
result=dict(passed=True,checks=checks,xml_records_compared=sum(consumed.values()),canonical_rows=total,series_verified=nc,primary_XML_hashes_verified=len(parsed),probe_XML_hash_verified=True,new_gets=125,maximum_simultaneous_attempt_intervals=maxactive,numeric_qc_flag_rows=len(flags),no_model_access=True,limitations='Source QC/timezone/datum/operational historical availability not independently certified; coverage inspection only.')
dump(P/'verification.json',result)
readme=P/'README.md';text=readme.read_text().split('\nVerificação integral independente:')[0];readme.write_text(text+'\nVerificação integral independente: '+str(len(checks))+' checks; '+str(sum(consumed.values()))+' registros comparados campo a campo com os XMLs; 54 séries, 135 hashes XML primários e um probe conferidos; máximo de duas tentativas simultâneas. Código em verify.py, resultado em verification.json. Manifesto final de todos os artefatos em artifact-hashes.json.\n')
dump(P/'artifact-hashes.json',[dict(file=str(f.relative_to(P)),bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(P.rglob('*')) if f.is_file() and f.name!='artifact-hashes.json'])
m=json.loads((P/'artifact-hashes.json').read_text());assert all(sha(P/r['file'])==r['sha256'] for r in m);print(dict(checks=len(checks),records=sum(consumed.values()),artifacts=len(m),max_concurrent=maxactive,flags=len(flags)))
