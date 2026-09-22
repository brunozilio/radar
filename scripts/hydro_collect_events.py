from pathlib import Path
import sys,json,datetime,concurrent.futures
sys.path.insert(0,str(Path(__file__).parent))
from hydro_collect import get,R
start=datetime.date(2026,7,1); end=datetime.date(2026,9,21)
urls={}
for station in ['86510000','86472000','86472600','86500000']:
 for i in range((end-start).days+1):
  d=start+datetime.timedelta(days=i);name=f'station-{station}-{d}.txt'
  if not (R/name).exists():urls[name]=f'https://sigmameteorologia.com/produtos/stations/{d}/{station}.txt'
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for i,r in enumerate(ex.map(lambda kv:get(*kv),urls.items()),1):
  results.append(r)
  if i%80==0:print(i,len(urls),'errors',sum('error' in r for r in results),flush=True)
(R/'events-fetch-manifest.json').write_text(json.dumps(results,indent=2));print('complete',len(results),'errors',sum('error' in r for r in results),flush=True)
