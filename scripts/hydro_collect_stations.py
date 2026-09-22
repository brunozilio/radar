from pathlib import Path
import json,sys,datetime,concurrent.futures,math
sys.path.insert(0,str(Path(__file__).parent))
from hydro_collect import get,manifest,R
stations=json.loads((R/'stations-inside.json').read_text())
# Deterministic spatial coverage: farthest-point selection among public official networks.
# Station IDs never imply separate rainfall volumes and are not summed across sites.
candidates=[s for s in stations if s['network'] in ['cemaden','inmet','dcrs','sgb_cprm'] and float(s['rain'][1])>=0]
selected=[min(candidates,key=lambda s:s['lon'])]
def distance(a,b):return ((a['lon']-b['lon'])*math.cos(math.radians(-29)))**2+(a['lat']-b['lat'])**2
while len(selected)<12:
 remaining=[s for s in candidates if s not in selected]
 selected.append(max(remaining,key=lambda s:min(distance(s,o) for o in selected)))
(R/'rain-model-stations.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2))
print('History sample:',[(s['id'],s['name']) for s in selected],flush=True)
start=datetime.date(2026,8,22);today=datetime.date(2026,9,21)
urls={}
for s in stations:
 for d in [today,today-datetime.timedelta(days=1)]:
  urls[f'station-{s["id"]}-{d}.txt']=f'https://sigmameteorologia.com/produtos/stations/{d}/{s["id"]}.txt'
for s in selected:
 for day in range((today-start).days+1):
  d=start+datetime.timedelta(days=day)
  urls[f'station-{s["id"]}-{d}.txt']=f'https://sigmameteorologia.com/produtos/stations/{d}/{s["id"]}.txt'
urls={k:v for k,v in urls.items() if not (R/k).exists()}
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for i,result in enumerate(ex.map(lambda kv:get(*kv),urls.items()),1):
  results.append(result)
  if i%50==0 or 'error' in result:print(i,len(urls),result['file'],result.get('status',result.get('error')),flush=True)
(R/'station-fetch-manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print('Complete:',len(results),'failed',sum('error' in r for r in results),flush=True)
