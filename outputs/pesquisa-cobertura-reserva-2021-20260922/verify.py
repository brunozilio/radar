"""Independent complete raw-to-JSONL provenance and coverage checks, offline."""
from pathlib import Path
from datetime import datetime,timedelta
import json,hashlib,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((P/'collection-plan.json').read_text());sources=json.loads((P/'source-manifest.json').read_text());checks=[]
def ok(n,x):assert x,n;checks.append(n)
ok('four_attempts',len(sources)==len(plan['jobs'])==4)
parsed={}
for m in sources:
 f=ROOT/m['source_file'];ok('raw_hash:'+f.name,sha(f)==m['sha256']);ok('success:'+f.name,m['http_status']==200 and m['audit_status']=='parsed');ok('preregistered:'+f.name,plan['registered_at_utc']<m['requested_at_utc']);parsed[m['source_file']]=[{c.tag.split('}')[-1]:c.text for c in e} for e in ET.parse(f).iter() if e.tag.split('}')[-1]=='DadosHidrometereologicos']
coverage=json.loads((P/'coverage.json').read_text());total=0
for c in ('86510000','86472000'):
 rows=[json.loads(x) for x in (P/'stations'/f'ana-{c}-all-qc.jsonl').read_text().splitlines()];tt=[]
 for r in rows:
  raw=parsed[r['source_file']][r['source_record_index']-1];assert r['fields']==raw and sha(ROOT/r['source_file'])==r['source_sha256'];tt.append(datetime.fromisoformat(raw['DataHora']));total+=1
 ok('full_provenance:'+c,True);expected=[datetime(2021,4,28)+timedelta(minutes=15*i) for i in range(3264)];ok('literal_complete_15min:'+c,tt==expected)
 s=next(s for s in coverage['stations'] if s['station']==c);ok('3264records:'+c,s['raw_records']==s['unique_timestamps']==len(rows)==3264);ok('no_duplicate_or_conflict:'+c,s['duplicate_extra_records']==s['conflicting_timestamps']==0)
 level=[r['fields'] for r in rows]
 if c=='86510000':ok('all_levels_approved_finite',all(r.get('CQ_NivelFinal')=='Dado aprovado' and r.get('NivelFinal') is not None for r in level))
 else:ok('all_final_levels_empty',all(r.get('CQ_NivelFinal') is None and r.get('NivelFinal') is None for r in level))
for f,h in plan['reference_hashes'].items():ok('unchanged_reference:'+f,sha(ROOT/f)==h)
result={'passed':True,'checks':checks,'all_qc_records_compared_to_xml':total,'reserved_window_model_access':False,'limits':'No timestamp/datum certification or forecast evaluation; independent checks only coverage and provenance.'}
(P/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
(P/'artifact-hashes.json').write_text(json.dumps([{'file':str(f.relative_to(P)),'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(P.rglob('*')) if f.is_file() and f.name!='artifact-hashes.json'],indent=2)+'\n')
manifest=json.loads((P/'artifact-hashes.json').read_text());assert all(sha(P/r['file'])==r['sha256'] for r in manifest);print({'checks':len(checks),'records':total,'hashed_artifacts':len(manifest)})
