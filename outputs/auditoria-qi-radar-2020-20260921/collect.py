"""One bounded public ONS GET for June2020 warmup; July remains frozen."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
catalog=ROOT/'outputs/historico-vazoes-ceran/raw/catalog.json'
d=json.loads(catalog.read_text());d=d.get('result',d)
r=next(r for r in d['resources'] if '2020_06.csv' in r['url'])
plan={'month':'2020-06','purpose':'Warmup forJuly1..20 RADAR observed preparation; notraining.',
 'max_get_requests':1,'max_bytes':32*1024*1024,'catalog':str(catalog.relative_to(ROOT)),
 'catalog_sha256':hashlib.sha256(catalog.read_bytes()).hexdigest(),'resource_id':r['id'],'url':r['url'],
 'july_reused_csv':'outputs/historico-vazoes-ceran/ceran-2020-07-source-values.csv'}
(P/'collection-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
side=P/'raw/ons-2020-06.source.json';dest=P/'raw/ons-2020-06.csv'
if side.exists():raise SystemExit('Attempt already recorded; inspect before any retry.')
assert not dest.exists()
meta={'url':r['url'],'requested_at_utc':datetime.now(timezone.utc).isoformat(),'status':'request_started'}
side.write_text(json.dumps(meta,indent=2)+'\n')
try:
 with urlopen(Request(r['url'],headers={'User-Agent':'Radar-hydrology-public-research/1.0'}),timeout=180) as h:
  content=h.read(plan['max_bytes']+1);meta.update(http_status=h.status,headers=dict(h.headers),final_url=h.url)
 if len(content)>plan['max_bytes']:raise ValueError('Source exceeds32MiB bound')
 dest.write_bytes(content)
 meta.update(status='response_preserved',collected_at_utc=datetime.now(timezone.utc).isoformat(),file=str(dest.relative_to(P)),bytes=len(content),sha256=hashlib.sha256(content).hexdigest())
except Exception as exc:
 meta.update(status='request_failed',error=str(exc),finished_at_utc=datetime.now(timezone.utc).isoformat())
side.write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps({k:v for k,v in meta.items() if k!='headers'},indent=2))
