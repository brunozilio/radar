from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import urllib.request,json,hashlib
ROOT=Path('/Users/brunozilio/Documents/radar')
P=ROOT/'outputs/historico-ceran-2023-complemento-20260921'
P.mkdir(parents=True,exist_ok=True);(P/'raw').mkdir(exist_ok=True)
months=[2,3,4,5,7,8]
catpath=ROOT/'outputs/pesquisa-qc-semantica-fontes/sources/catalog.json'
cat=json.loads(catpath.read_text());cat=cat.get('result',cat)
resources=[r for r in cat['resources'] if r['format']=='CSV' and any(r['name'].endswith(f'2023-{m:02d}') for m in months)]
assert len(resources)==6
(P/'selected-resources.json').write_text(json.dumps(resources,indent=2,ensure_ascii=False)+'\n')
def fetch(r):
 url=r['url'];p=P/'raw'/url.rsplit('/',1)[-1];start=datetime.now(timezone.utc).isoformat()
 assert not p.exists(), 'Do not duplicate download '+str(p)
 try:
  with urllib.request.urlopen(url,timeout=60) as h:
   with p.open('wb') as f:
    while True:
     data=h.read(1024*1024)
     if not data:break
     f.write(data)
   return {'url':url,'catalog_resource_id':r['id'],'started_at':start,'collected_at':datetime.now(timezone.utc).isoformat(),'file':str(p.relative_to(P)),'status':h.status,'headers':dict(h.headers),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
 except Exception as e:return {'url':url,'started_at':start,'error':str(e)}
with ThreadPoolExecutor(max_workers=2) as ex:manifest=list(ex.map(fetch,resources))
(P/'source-manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k!='headers'} for r in manifest],indent=2))

