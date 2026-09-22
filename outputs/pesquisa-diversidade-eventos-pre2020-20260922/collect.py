from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode
import hashlib,json,re,sys
P=Path(__file__).resolve().parent;R=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def fetch(j):
 dst=P/j['file'];meta=dst.with_suffix(dst.suffix+'.source.json')
 if meta.exists():raise RuntimeError('Already attempted; no retry:'+str(meta))
 m=dict(j,requested_at_utc=datetime.now(timezone.utc).isoformat(),status='started');dump(meta,m)
 try:
  try:
   with urlopen(Request(j['url'],headers={'User-Agent':'Radar-public-research/1.0'}),timeout=45) as h:
    b=h.read(16*1024*1024+1);m.update(http_status=h.status,headers=dict(h.headers),response_url=h.url)
  except HTTPError as e:b=e.read(16*1024*1024+1);m.update(http_status=e.code,headers=dict(e.headers),response_url=e.url)
  assert len(b)<=16*1024*1024
  dst.write_bytes(b);m.update(status='body_preserved',bytes=len(b),sha256=sha(dst))
 except Exception as e:m.update(status='failed',error=str(e))
 m['completed_at_utc']=datetime.now(timezone.utc).isoformat();dump(meta,m);print(j['file'],m.get('http_status'),m.get('bytes'),m['status'],flush=True)
def plan():
 inv=[]
 for f in sorted((R/'outputs').rglob('*.xml')):
  if f.is_relative_to(P):continue
  if '86510000' not in str(f) and not any(y in f.name for y in ('2011','2015','2017','2019')):continue
  ds=re.findall(rb'<DataHora>((?:2011|2015|2017|2019)-[^<]+)</DataHora>',f.read_bytes())
  inv.append(dict(file=str(f.relative_to(R)),sha256=sha(f),matching_pre2020_timestamps=len(ds),first=min(ds).decode() if ds else None,last=max(ds).decode() if ds else None))
 dump(P/'cache-inventory.json',inv);assert not any(x['matching_pre2020_timestamps'] for x in inv)
 endpoint=json.loads((R/'outputs/pesquisa-fase-horaria-2022-20260921/source.json').read_text())['url'].split('?')[0]
 jobs=[]
 for a,b,basis in [('2011-07-18','2011-07-24','Official-hosted research citing AVADAN: Encantado event21July; local SGB article Muçum annualmax2011; no exactMuçumpeak certification.'),('2015-10-08','2015-10-14','State CivilDefence contemporary bulletin11Oct2015, affected Taquari-region towns; not Muçum-specific peak.'),('2017-05-24','2017-05-30','SGB extraordinary bulletin26May2017; Muçum maintenance explicitly.')]:
  params={'codEstacao':'86510000','dataInicio':datetime.fromisoformat(a).strftime('%d/%m/%Y'),'dataFim':datetime.fromisoformat(b).strftime('%d/%m/%Y')}
  jobs.append(dict(start=a,end=b,station='86510000',basis=basis,url=endpoint+'?'+urlencode(params),file=f'raw/ana-86510000-{a}--{b}.xml'))
 dump(P/'collection-plan.json',dict(registered_at_utc=datetime.now(timezone.utc).isoformat(),max_ana_requests=3,selected_without_model_errors=True,scope='Documentary candidates and Muçum availability only; no training/features/normalization/interpolation/unit conversion. Literal timestamps and all QC preserved.',cache_inventory_sha256=sha(P/'cache-inventory.json'),jobs=jobs,year2019='Unresolved event date; no arbitrary week selected.'))
 print('Planned3ANArequests;cache scans',len(inv))
def docs():
 jobs=[
 ('sgb-2017-05-26.pdf','https://www.sgb.gov.br/sace/boletins/Taquari/20170526_22-20170527%20-%20001639.pdf','2017-05-26','SGB contemporary official bulletin'),
 ('defesa-civil-2015-10-11.html','https://www.estado.rs.gov.br/defesa-civil-divulga-novo-boletim-sobre-situacao-nos-municipios-e-nas-estradas','2015-10-11','StateCivilDefence contemporary account'),
 ('estudo-encantado-2011.pdf','https://revistas.planejamento.rs.gov.br/index.php/boletim-geografico-rs/article/download/4444/4124','2021','Official-hosted research; documentary AVADAN analysis, primary analysis not rawAVADAN'),
 ('bom-retiro-balanco-2017.html','https://bomretirodosul.rs.gov.br/noticia/view/2550','2017 retrospective; verify body','Municipal primary operational retrospective')]
 for fn,url,date,kind in jobs:fetch(dict(file='sources/'+fn,url=url,document_date=date,kind=kind))
if __name__=='__main__':
 if sys.argv[1]=='plan':plan()
 elif sys.argv[1]=='ana':
  for j in json.loads((P/'collection-plan.json').read_text())['jobs']:fetch(j)
 elif sys.argv[1]=='docs':docs()
