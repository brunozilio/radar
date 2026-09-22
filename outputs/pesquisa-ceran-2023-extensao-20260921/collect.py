from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import urllib.request,json,hashlib
ROOT=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent
catalog=ROOT/'outputs/pesquisa-qc-semantica-fontes/sources/catalog.json';d=json.loads(catalog.read_text());d=d.get('result',d)
resources=[r for r in d['resources'] if r['format']=='PARQUET' and any(r['name'].endswith(f'2023-{m:02d}') for m in range(1,9))]
(P/'next-monthly-resources.json').write_text(json.dumps(resources,ensure_ascii=False,indent=2)+'\n')
rows=[r for r in d['resources'] if r['format']=='CSV' and any(r['name'].endswith(f'2023-{m:02d}') for m in [1,6])]
def fetch(r):
 url=r['url'];p=P/'raw'/url.rsplit('/',1)[-1];start=datetime.now(timezone.utc).isoformat()
 try:
  with urllib.request.urlopen(url,timeout=45) as h:
   data=h.read();p.write_bytes(data)
   return {'url':url,'catalog_resource_id':r['id'],'started_at':start,'collected_at':datetime.now(timezone.utc).isoformat(),'file':str(p.relative_to(P)),'status':h.status,'headers':dict(h.headers),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
 except Exception as e:return {'url':url,'started_at':start,'error':str(e)}
with ThreadPoolExecutor(max_workers=2) as ex:manifest=list(ex.map(fetch,rows))
(P/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k!='headers'} for r in manifest],indent=2))
