"""Read only the public hydrology tables in the production D1 database."""
from pathlib import Path
import subprocess,json,datetime,hashlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/mucum-bacia-2026-09-21/raw/producao'
WRANGLER='/Users/brunozilio/.npm/_npx/32026684e21afda6/node_modules/wrangler/bin/wrangler.js'
def query(name,sql):
    assert sql.lstrip().upper().startswith('SELECT ')
    p=subprocess.run(['node',WRANGLER,'d1','execute','sofik-monitoramento-push','--remote','--config','wrangler.jsonc','--command',sql,'--json'],cwd=ROOT,capture_output=True,text=True,check=True)
    data=json.loads(p.stdout)
    assert all(x.get('success') and x['meta']['rows_written']==0 and not x['meta']['changed_db'] for x in data)
    (OUT/(name+'.json')).write_text(p.stdout)
    (OUT/(name+'-consulta.json')).write_text(json.dumps({'sql':sql,'read_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(p.stdout.encode()).hexdigest(),'rows':sum(len(x['results']) for x in data),'rows_written':0},indent=2))
    print(name,sum(len(x['results']) for x in data),flush=True)
if __name__=='__main__':
    OUT.mkdir(exist_ok=True,parents=True)
    for name,sql in [
      ('ceran', 'SELECT plant_id,timestamp,upstream_level,downstream_level,inflow,turbined,spilled,residual,outflow,status FROM ceran_readings ORDER BY timestamp'),
      ('sace', "SELECT station,timestamp,level,level_cm FROM sace_readings WHERE station NOT LIKE 'sace-%' ORDER BY timestamp"),
      ('chuva', 'SELECT station,timestamp,rain,level_cm,discharge,quality FROM rain_readings ORDER BY timestamp')]:query(name,sql)
