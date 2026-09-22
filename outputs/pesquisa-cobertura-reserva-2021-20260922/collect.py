"""Coverage-only reserved-2021 ANA acquisition. No inference, retries or date repair."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlencode
from urllib.request import urlopen,Request
from urllib.error import HTTPError
import json,hashlib,sys,re
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def plan():
 assert not (P/'collection-plan.json').exists()
 inventory=[];hits=[]
 for f in sorted((ROOT/'outputs').rglob('*.xml')):
  if f.is_relative_to(P):continue
  if any(c in str(f) for c in ('86510000','86472000')) or '2021' in f.name or f.name=='response.xml':
   b=f.read_bytes();dates=re.findall(rb'<DataHora>(2021-(?:04|05)-[^<]+)</DataHora>',b)
   row={'file':str(f.relative_to(ROOT)),'bytes':len(b),'matching_2021_april_may_dates':len(dates)};inventory.append(row)
   if dates:hits.append({**row,'sha256':sha(f),'first':min(dates).decode(),'last':max(dates).decode()})
 dump(P/'cache-inventory.json',{'scope':'XMLs with either target station in path, 2021 in filename, or generic response.xml. Literal DataHora scan for April/May2021; excludes own folder. Not an unrestricted unrelated file search.','scanned':inventory,'hits':hits})
 assert not hits,'Existing relevant response needs manual reuse planning, no network.'
 ref=ROOT/'docs/radar-historical-evaluation-reservation.json';probe=ROOT/'outputs/pesquisa-fase-horaria-2022-20260921/source.json';endpoint=json.loads(probe.read_text())['url'].split('?')[0];jobs=[]
 for c in ('86510000','86472000'):
  for a,b in [('2021-04-28','2021-04-30'),('2021-05-01','2021-05-31')]:
   params={'codEstacao':c,'dataInicio':datetime.fromisoformat(a).strftime('%d/%m/%Y'),'dataFim':datetime.fromisoformat(b).strftime('%d/%m/%Y')}
   jobs.append(dict(station=c,start=a,end=b,url=endpoint+'?'+urlencode(params),parameters=params,file=f'raw/ana-{c}-{a}--{b}.xml'))
 dump(P/'collection-plan.json',dict(registered_at_utc=datetime.now(timezone.utc).isoformat(),scope='Coverage/QC only, reserved2021 remains excluded from fit/tuning. No model inference/errors/features/weights.',max_get_requests=4,no_automatic_retries=True,reused=[],jobs=jobs,reference_hashes={str(f.relative_to(ROOT)):sha(f) for f in (ref,probe)},timezone='Literal naive DataHora retained; BRT not certified by this audit.',normalization='No interpolation, rounding, zero filling or unit conversion; all original field text/QC retained.'))
 print('Plan registered:4GET,cache hits0,scanned',len(inventory),flush=True)
def collect():
 plan=json.loads((P/'collection-plan.json').read_text());assert len(plan['jobs'])<=4;(P/'raw').mkdir(exist_ok=True)
 for j in plan['jobs']:
  dest=P/j['file'];meta=dest.with_suffix('.source.json')
  if meta.exists():print('Already attempted; no retry:',j['file'],flush=True);continue
  assert not dest.exists();r={**j,'requested_at_utc':datetime.now(timezone.utc).isoformat(),'status':'started','plan_sha256':sha(P/'collection-plan.json')};dump(meta,r)
  try:
   try:
    with urlopen(Request(j['url'],headers={'User-Agent':'Radar-public-coverage-research/1.0'}),timeout=45) as h:body=h.read(8*1024*1024+1);r.update(http_status=h.status,headers=dict(h.headers),response_url=h.url)
   except HTTPError as e:body=e.read(8*1024*1024+1);r.update(http_status=e.code,headers=dict(e.headers))
   assert len(body)<=8*1024*1024,'response limit8MiB exceeded';dest.write_bytes(body);r.update(status='response_preserved',collected_at_utc=datetime.now(timezone.utc).isoformat(),bytes=len(body),sha256=sha(dest),source_file=str(dest.relative_to(ROOT)))
  except Exception as e:r.update(status='failed',error=str(e),finished_at_utc=datetime.now(timezone.utc).isoformat())
  dump(meta,r);print(j['station'],j['start'],r['status'],r.get('http_status'),r.get('bytes'),flush=True)
if __name__=='__main__':
 if sys.argv[1:]==['--plan']:plan()
 elif sys.argv[1:]==['--collect']:collect()
 else:raise SystemExit('Use --plan or --collect')
