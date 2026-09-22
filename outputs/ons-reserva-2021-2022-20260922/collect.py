"""Five catalogued public ONS CSVs for reserved-window input coverage, no model use."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import hashlib,json,subprocess
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
MONTHS=('2021-04','2021-05','2022-04','2022-05','2022-06')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
assert not (P/'collection-plan.json').exists(),'Inspect existing attempt; no automatic repeat.'
catalog=ROOT/'outputs/historico-vazoes-ceran/raw/catalog.json'
d=json.loads(catalog.read_text());d=d.get('result',d)
scan=subprocess.run(['rg','--files','outputs','-g','*2021*.csv','-g','*2022*.csv'],cwd=ROOT,text=True,capture_output=True)
assert scan.returncode in (0,1),scan.stderr
inventory=scan.stdout.splitlines()
relevant=[f for f in inventory if any(s in Path(f).name.lower() for s in ('ons-','ceran-','dados_hidrologicos'))]
assert not relevant, relevant
jobs=[]
for month in MONTHS:
    rr=[r for r in d['resources'] if month.replace('-','_')+'.csv' in r['url']];assert len(rr)==1
    r=rr[0];jobs.append(dict(month=month,url=r['url'],resource_id=r['id'],file=f'raw/ons-{month}.csv'))
dump(P/'collection-plan.json',dict(registered_at_utc=datetime.now(timezone.utc).isoformat(),catalog=str(catalog.relative_to(ROOT)),catalog_sha256=sha(catalog),
    license_id=d.get('license_id'),existing_csv_inventory=inventory,jobs=jobs,max_gets=5,max_bytes_per_response=32*1024*1024,
    automatic_retries=0,scope='Literal Q/I source and coverage diagnostics only; reserve2021/2022 remains outside fitting/inference. April files provide warmup.'))
(P/'raw').mkdir()
manifest=[]
for j in jobs:
    m={**j,'requested_at_utc':datetime.now(timezone.utc).isoformat(),'status':'started'};manifest.append(m);dump(P/'source-manifest.json',manifest)
    try:
        try:
            with urlopen(Request(j['url'],headers={'User-Agent':'Radar-public-history-research/1.0'}),timeout=45) as r:
                body=r.read(32*1024*1024+1);m.update(http_status=r.status,headers=dict(r.headers),final_url=r.url)
        except HTTPError as e:
            body=e.read(32*1024*1024+1);m.update(http_status=e.code,headers=dict(e.headers))
        assert len(body)<=32*1024*1024
        dest=P/j['file'];dest.write_bytes(body)
        m.update(status='preserved',collected_at_utc=datetime.now(timezone.utc).isoformat(),bytes=len(body),sha256=sha(dest))
    except Exception as e:m.update(status='failed',error=str(e),finished_at_utc=datetime.now(timezone.utc).isoformat())
    dump(P/'source-manifest.json',manifest)
    print(json.dumps({k:m.get(k) for k in ('month','status','http_status','bytes','error')}),flush=True)
