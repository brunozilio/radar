"""Bounded public ANA collection of reserved inputs; never inference/training."""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError
import json,hashlib,re,sys
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def now():return datetime.now(timezone.utc).isoformat()
class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*a,**k):return None

def plan():
 assert not (P/'collection-plan.json').exists()
 wp=ROOT/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json';lp=ROOT/'outputs/auditoria-latencias-chuva-20260921/latencies.json';reservation=ROOT/'docs/radar-historical-evaluation-reservation.json'
 codes=sorted({c for x in json.loads(wp.read_text()) for c in x['weights']});assert len(codes)==27 and set(codes)=={x['station'] for x in json.loads(lp.read_text())['stations']}
 references=[wp,lp,reservation];reused=[]
 for year,folder,name in [(2021,'pesquisa-cobertura-reserva-2021-20260922','source-manifest.json'),(2022,'pesquisa-cobertura-reserva-2022-20260922','collection-manifest.json')]:
  d=ROOT/'outputs'/folder;mp=d/name;references.append(mp)
  for m in json.loads(mp.read_text()):
   if Path(m['file']).name=='response.xml':continue # probe is separately audited below
   f=d/m['file'];assert sha(f)==m['sha256'];assert m['http_status']==200
   reused.append(dict(station=m['station'],year=year,start=m['start'],end=m['end'],source_file=str(f.relative_to(ROOT)),sha256=m['sha256'],source_metadata=m,usage='primary_reuse'))
 assert len(reused)==10
 probe=ROOT/'outputs/pesquisa-fase-horaria-2022-20260921';pm=probe/'source.json';references.append(pm);meta=json.loads(pm.read_text());pf=probe/'response.xml';assert sha(pf)==meta['sha256']
 overlap=dict(station='86510000',year=2022,source_file=str(pf.relative_to(ROOT)),sha256=sha(pf),source_metadata=meta,usage='overlap_audit_only; not appended to canonical series')
 known={r['source_file'] for r in reused}|{overlap['source_file']};inventory=[];unknown=[]
 for f in sorted((ROOT/'outputs').rglob('*.xml')):
  if f.is_relative_to(P):continue
  if any(c in str(f) for c in codes) or ('2021' in str(f) or '2022' in str(f)) and f.name=='response.xml':
   b=f.read_bytes();dates=re.findall(rb'<DataHora>((?:2021|2022)-(?:04|05|06)-[^<]+)</DataHora>',b);relevant=[d for d in dates if (b'2021-04-28'<=d<b'2021-06-01') or (b'2022-04-28'<=d<b'2022-07-01')]
   path=str(f.relative_to(ROOT));r=dict(file=path,bytes=len(b),overlap_rows=len(relevant),known=path in known);inventory.append(r)
   if relevant and path not in known:unknown.append({**r,'sha256':sha(f),'first_literal':min(relevant).decode(),'last_literal':max(relevant).decode()})
 dump(P/'cache-inventory.json',dict(scope='Raw XML paths containing one of27station codes plus generic response.xml in2021/2022 folders; literal target-window DataHora scan. Other cached years not reused.',scanned=inventory,unknown_relevant=unknown))
 assert not unknown,'Additional relevant cache requires explicit reuse plan before network.'
 endpoint=meta['url'].split('?')[0];jobs=[]
 for year in (2021,2022):
  windows=[(f'{year}-04-28',f'{year}-04-30'),(f'{year}-05-01',f'{year}-05-31')]+([(f'{year}-06-01',f'{year}-06-30')] if year==2022 else [])
  for c in codes:
   if c in ('86510000','86472000'):continue
   for a,b in windows:
    args=dict(codEstacao=c,dataInicio=datetime.fromisoformat(a).strftime('%d/%m/%Y'),dataFim=datetime.fromisoformat(b).strftime('%d/%m/%Y'));jobs.append(dict(station=c,year=year,start=a,end=b,parameters=args,url=endpoint+'?'+urlencode(args),file=f'raw/{year}/ana-{c}-{a}--{b}.xml'))
 assert len(jobs)==125
 dump(P/'collection-plan.json',dict(registered_at_utc=now(),scope='ALL-QC acquisition and coverage only; reserved2021/2022 never used for training/inference/errors/selection.',stations=codes,windows={'2021':['2021-04-28','2021-05-31'],'2022':['2022-04-28','2022-06-30']},warmup='April28–30 each year',planned_new_gets=len(jobs),max_new_gets=125,max_parallel_connections=2,no_automatic_retries=True,no_redirect_requests=True,new_jobs=jobs,reused=reused,overlap_audit=overlap,reference_sha256={str(f.relative_to(ROOT)):sha(f) for f in references},normalization='Original fields at top level with original DataHora text and source file/hash/1-based XML record index. Identical duplicate observations may be deduplicated with all provenance; conflicts remain as separate rows and conflict catalog. No rounding/interpolation/zero fill/unit conversion.'))
 print('Plan registered:125GET,10primaryreused,1overlapaudit,cachefiles',len(inventory),flush=True)
def attempt(j,ph):
 dest=P/j['file'];dest.parent.mkdir(parents=True,exist_ok=True);side=dest.with_suffix('.source.json')
 if side.exists():return dict(station=j['station'],start=j['start'],status='already_attempted_no_retry')
 assert not dest.exists(),'Orphan body: no repeat request';r={**j,'status':'attempt_started','requested_at_utc':now(),'plan_sha256':ph,'attempt_number':1};dump(side,r)
 try:
  try:
   with build_opener(NoRedirect()).open(Request(j['url'],headers={'User-Agent':'Radar-public-reserved-input-coverage/1.0'}),timeout=45) as h:body=h.read(8*1024*1024+1);r.update(http_status=h.status,headers=dict(h.headers),response_url=h.url)
  except HTTPError as e:body=e.read(8*1024*1024+1);r.update(http_status=e.code,headers=dict(e.headers),response_url=e.url)
  assert len(body)<=8*1024*1024,'bounded response exceeds8MiB';dest.write_bytes(body);r.update(status='body_preserved',source_file=str(dest.relative_to(ROOT)),collected_at_utc=now(),bytes=len(body),sha256=sha(dest))
 except Exception as e:r.update(status='request_failed',error_type=type(e).__name__,error=str(e),body_available=False)
 r['finished_at_utc']=now();dump(side,r);print(j['year'],j['station'],j['start'],r['status'],r.get('http_status'),r.get('bytes'),flush=True);return r
def collect():
 plan=json.loads((P/'collection-plan.json').read_text());assert len(plan['new_jobs'])<=125;ph=sha(P/'collection-plan.json')
 with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda j:attempt(j,ph),plan['new_jobs']))
if __name__=='__main__':
 if sys.argv[1:]==['--plan']:plan()
 elif sys.argv[1:]==['--collect']:collect()
 else:raise SystemExit('Use --plan or --collect')
