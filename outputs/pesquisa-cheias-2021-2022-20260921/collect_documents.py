"""Fetch only the already discovered official report documents; no time-series downloads."""
from pathlib import Path
import urllib.request,hashlib,json
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent;manifest=[]
urls=[('sgb-2021.pdf','https://rigeo.sgb.gov.br/bitstreams/f617bac6-f19e-4396-a657-26bc5b353a00/download'),('sgb-2022.pdf','https://rigeo.sgb.gov.br/bitstreams/cfb7f9ef-3abf-4a2d-8f27-6ef599577287/download')]
for name,url in urls:
 p=OUT/'sources'/name
 if p.exists():raise RuntimeError('Existing source; refuse duplicate request')
 start=datetime.now(timezone.utc).isoformat()
 with urllib.request.urlopen(url,timeout=45) as r:
  data=r.read(10_000_001);assert len(data)<=10_000_000 and data.startswith(b'%PDF');meta=dict(file='sources/'+name,url=url,final_url=r.url,http_status=r.status,headers=dict(r.headers),collected_at_utc=start,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
 p.write_bytes(data);manifest.append(meta);(OUT/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print([(r['file'],r['bytes']) for r in manifest])
