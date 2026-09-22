from pathlib import Path
import hashlib,json,datetime
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
items=[{'file':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(R.rglob('*')) if p.is_file() and p.name not in {'manifest.json','manifest-check.json'}]
(R/'manifest.json').write_text(json.dumps({'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':items},indent=2)+'\n')
checks=[{'file':i['file'],'passed':sha(R/i['file'])==i['sha256']} for i in items]
(R/'manifest-check.json').write_text(json.dumps({'passed':all(i['passed'] for i in checks),'count':len(checks),'manifest_sha256':sha(R/'manifest.json'),'checks':checks},indent=2)+'\n')
print(len(checks),sha(R/'manifest.json'),all(i['passed'] for i in checks))
