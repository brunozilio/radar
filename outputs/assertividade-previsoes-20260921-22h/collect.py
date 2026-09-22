"""Read public observations and saved rounds. No refresh or provider mutation."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, urllib.request, urllib.parse, subprocess
OUT=Path(__file__).resolve().parent
TZ=timezone(timedelta(hours=-3));at=datetime.now(TZ)
manifest=json.loads((OUT/'collection.json').read_text()) if (OUT/'collection.json').exists() else []
def get(name,url):
 if (OUT/name).exists():
  return (OUT/name).read_bytes()
 data=subprocess.run(['curl','-fsS','--max-time','30',url],check=True,capture_output=True).stdout
 if len(data)>5000000: raise ValueError('Unexpected response size')
 (OUT/name).write_bytes(data)
 manifest.append({'file':name,'url':url,'status':200,'retrieved_at':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256(data).hexdigest()})
 (OUT/'collection.json').write_text(json.dumps(manifest,indent=2))
 return data
params={'codEstacao':'86510000','dataInicio':(at-timedelta(days=1)).strftime('%d/%m/%Y'),'dataFim':at.strftime('%d/%m/%Y')}
get('ana-mucum.xml','https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?'+urllib.parse.urlencode(params))
d=json.loads(get('site-latest.json','https://radar.brunozilio.com/api/projection'))
for n,ref in enumerate(d.get('rounds',[])):
 get(f'site-round-{n}.json','https://radar.brunozilio.com/api/projection?'+urllib.parse.urlencode({'round':ref}))
print(json.dumps(manifest,indent=2))
