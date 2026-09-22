"""One read-only ANA timestamp-phase probe; no predictions or timestamp repair."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import urlopen
from urllib.parse import urlencode
from collections import Counter
import hashlib,json,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent
args={'codEstacao':'86510000','dataInicio':'04/05/2022','dataFim':'04/05/2022'}
url='https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?'+urlencode(args)
plan={'station':'86510000','date':'2022-05-04','max_get_requests':1,'scope':'Timestamp and QC audit only, reservation permits source coverage inspection. No model errors or training.','url':url}
(P/'collection-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
meta=P/'source.json';raw=P/'response.xml'
assert not meta.exists() and not raw.exists(),'Existing attempt requires inspection; no automatic retry.'
m={'url':url,'requested_at_utc':datetime.now(timezone.utc).isoformat(),'status':'started'};meta.write_text(json.dumps(m,indent=2)+'\n')
try:
 with urlopen(url,timeout=45) as h:
  body=h.read(4*1024*1024+1);m.update(http_status=h.status,headers=dict(h.headers))
 assert len(body)<=4*1024*1024
 raw.write_bytes(body);m.update(status='preserved',collected_at_utc=datetime.now(timezone.utc).isoformat(),bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
except Exception as exc:
 m.update(status='failed',error=str(exc));meta.write_text(json.dumps(m,indent=2)+'\n');raise
meta.write_text(json.dumps(m,indent=2)+'\n')
tree=ET.fromstring(body);rows=[{c.tag.split('}')[-1]:c.text for c in e} for e in tree.iter() if e.tag.split('}')[-1]=='DadosHidrometereologicos']
assert all(r['CodEstacao']=='86510000' and r['DataHora'].startswith('2022-05-04') for r in rows)
times=[datetime.fromisoformat(r['DataHora']) for r in rows]
result={'rows':len(rows),'minute_phase_counts':dict(Counter(t.minute for t in times)), 'second_counts':dict(Counter(t.second for t in times)),
 'exact_whole_hour_records':sum(t.minute==t.second==0 for t in times),'level_qc_counts':dict(Counter(str(r.get('CQ_NivelFinal')) for r in rows)),
 'source_errors':[e.text for e in tree.iter() if e.tag.split('}')[-1]=='Error'],
 'timestamp_modified':False,'model_inference':False,'training':False,'reservation_still_excludes_fitting':True}
(P/'rows-all-qc.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
(P/'phase-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(P/'artifact-hashes.json').write_text(json.dumps([{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(P.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
print(json.dumps(result,indent=2))
