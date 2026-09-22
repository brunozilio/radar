from pathlib import Path
import sys,json,datetime,concurrent.futures
sys.path.insert(0,str(Path(__file__).parent))
from hydro_collect import get,R
stations=json.loads((R/'stations-inside.json').read_text())
# Archive every public-network gauge inside the drainage polygon; private networks remain contextual.
selected=[s for s in stations if s['network'] in ['cemaden','inmet','dcrs','sgb_cprm','epagri']]
urls={}
for s in selected:
 for i in range(31):
  d=datetime.date(2026,8,22)+datetime.timedelta(days=i)
  name=f'station-{s["id"]}-{d}.txt'
  if not (R/name).exists():urls[name]=f'https://sigmameteorologia.com/produtos/stations/{d}/{s["id"]}.txt'
print('Archive gauges',len(selected),'remaining requests',len(urls),flush=True)
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for i,r in enumerate(ex.map(lambda kv:get(*kv),urls.items()),1):
  results.append(r)
  if i%200==0:print('Fetched',i,'/',len(urls),'errors',sum('error' in r for r in results),flush=True)
(R/'archive-fetch-manifest.json').write_text(json.dumps(results,indent=2));print('Complete',len(results),'errors',sum('error' in r for r in results),flush=True)
