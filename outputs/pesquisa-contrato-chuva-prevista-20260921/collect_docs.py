from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import json,hashlib,urllib.request
P=Path(__file__).resolve().parent
urls={'previous-runs':'https://open-meteo.com/en/docs/previous-runs-api','single-runs':'https://open-meteo.com/en/docs/single-runs-api','model-updates':'https://open-meteo.com/en/docs/model-updates','forecast':'https://open-meteo.com/en/docs'}
def fetch(kv):
 name,url=kv;r={'url':url,'requested_at':datetime.now(timezone.utc).isoformat()}
 try:
  with urllib.request.urlopen(url,timeout=30) as h:
   b=h.read();f=P/'sources'/f'{name}.html';f.write_bytes(b);r.update(file=str(f.relative_to(P)),status=h.status,headers=dict(h.headers),collected_at=datetime.now(timezone.utc).isoformat(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
 except Exception as e:r['error']=str(e)
 return r
with ThreadPoolExecutor(max_workers=4) as ex:rs=list(ex.map(fetch,urls.items()))
(P/'source-manifest.json').write_text(json.dumps(rs,ensure_ascii=False,indent=2)+'\n');print([{k:v for k,v in x.items() if k not in ['headers']} for x in rs])
