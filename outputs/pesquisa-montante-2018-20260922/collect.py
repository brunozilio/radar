from pathlib import Path
import json, hashlib, datetime, urllib.request, urllib.error, urllib.parse
R=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
 (R/'raw').mkdir(exist_ok=True)
 for station in ['86472000','86472600','86500000']:
  for start,end in [('2018-08-30','2018-09-05'),('2018-09-30','2018-10-06')]:
   name=f'ana-{station}-{start}-{end}.xml';p=R/'raw'/name;receipt=p.with_suffix('.receipt.json')
   if receipt.exists():
    m=json.loads(receipt.read_text());assert p.exists() and sha(p.read_bytes())==m['sha256'];continue
   url='https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?'+urllib.parse.urlencode({'codEstacao':station,'dataInicio':datetime.date.fromisoformat(start).strftime('%d/%m/%Y'),'dataFim':datetime.date.fromisoformat(end).strftime('%d/%m/%Y')})
   meta={'station':station,'start':start,'end':end,'url':url,'started_utc':now(),'automatic_retries':0}
   try:
    with urllib.request.urlopen(url,timeout=40) as r:body=r.read();meta.update(http_status=r.status,headers=dict(r.headers),final_url=r.url)
   except urllib.error.HTTPError as e:body=e.read();meta.update(http_status=e.code,headers=dict(e.headers),error=str(e))
   except Exception as e:body=b'';meta.update(http_status=None,error=repr(e))
   p.write_bytes(body);meta.update(finished_utc=now(),file=str(p.relative_to(R)),bytes=len(body),sha256=sha(body))
   receipt.write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n');print(name,meta.get('http_status'),len(body),flush=True)
if __name__=='__main__':main()
