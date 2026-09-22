from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode
from datetime import datetime,timezone
import json,hashlib,sys
P=Path(__file__).resolve().parent;R=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def fetch(j):
 p=P/j['file'];m=p.with_suffix(p.suffix+'.source.json');assert not m.exists() and not p.exists(),'Refuse duplicate request'
 d=dict(j,requested_at_utc=datetime.now(timezone.utc).isoformat(),status='started');dump(m,d)
 try:
  try:
   with urlopen(Request(j['url'],headers={'User-Agent':'Radar-public-research/1.0'}),timeout=45) as h:b=h.read(8*1024*1024+1);d.update(http_status=h.status,response_url=h.url,headers=dict(h.headers))
  except HTTPError as e:b=e.read(8*1024*1024+1);d.update(http_status=e.code,response_url=e.url,headers=dict(e.headers))
  assert len(b)<=8*1024*1024;p.write_bytes(b);d.update(status='body_preserved',bytes=len(b),sha256=sha(p))
 except Exception as e:d.update(status='failed',error=str(e))
 d['finished_at_utc']=datetime.now(timezone.utc).isoformat();dump(m,d);print(j['file'],d.get('http_status'),d.get('bytes'),flush=True);return d
if __name__=='__main__':
 if sys.argv[1]=='docs':
  fetch({'file':'sources/legacy-HidroSerieHistorica.html','url':'https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx?op=HidroSerieHistorica','kind':'official GET/POST/SOAP operation contract'})
 elif sys.argv[1]=='plan':
  contract=P/'sources/legacy-HidroSerieHistorica.html';assert 'HidroSerieHistorica' in contract.read_text();assert 'nivelConsistencia' in contract.read_text()
  # Inventory relevant cached XMLs, by fields identifying conventional monthly cotas.
  inv=[]
  for p in sorted((R/'outputs').rglob('*.xml')):
   if p.is_relative_to(P) or ('86510000' not in p.name and 'hidroserie' not in p.name.lower()):continue
   b=p.read_bytes();has=(b'Cota01' in b or b'Cotas01' in b)
   if has:inv.append({'file':str(p.relative_to(R)),'sha256':sha(p),'bytes':len(b)})
  dump(P/'cache-inventory.json',{'scope':'XML filenames86510000 or hidroserie; identifying conventional Cota01/Cotas01 fields','matches':inv});assert not inv,'Review cache before requesting'
  jobs=[]
  for a,b in [('2011-07-18','2011-07-24'),('2015-10-08','2015-10-14'),('2017-05-24','2017-05-30')]:
   for qc in (2,1):
    params={'codEstacao':'86510000','dataInicio':datetime.fromisoformat(a).strftime('%d/%m/%Y'),'dataFim':datetime.fromisoformat(b).strftime('%d/%m/%Y'),'tipoDados':'1','nivelConsistencia':str(qc)}
    jobs.append(dict(start=a,end=b,parameters=params,file=f'raw/hidro-86510000-{a}--{b}-consistencia{qc}.xml',url='https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/HidroSerieHistorica?'+urlencode(params)))
  dump(P/'plan.json',{'registered_at_utc':datetime.now(timezone.utc).isoformat(),'station':'86510000','max_data_requests':6,'windows':3,'contract_sha256':sha(contract),'strategy':'Consistido2 first per window. Bruto1 only if no HTTPauth/server error for same window; no automatic retry. Stop onauth. No newAPI credentials/login requests.','transformations':'None. Preserve raw bodies; no hourly interpolation or field/unit reinterpretation.','jobs':jobs})
 elif sys.argv[1]=='data':
  plan=json.loads((P/'plan.json').read_text());results=[]
  for j in plan['jobs']:
   if j['parameters']['nivelConsistencia']=='1' and (not results or results[-1].get('http_status')!=200):
    results.append(dict(j,status='not_attempted_due_previous_http_failure'));continue
   d=fetch(j);results.append(d)
   dump(P/'attempts.json',results)
   if d.get('http_status') in (401,403):break
  dump(P/'attempts.json',results)
