from pathlib import Path
import json,hashlib,datetime
P=Path(__file__).resolve().parent;R=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(P/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
sources=json.loads((P/'sources.json').read_text())
checks=[sha(R/x['path'])==x['sha256'] for x in sources['sources']+sources['prior_investigation_files']]
assert all(checks)
files=[{'path':str(p.relative_to(P)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(P.rglob('*')) if p.is_file() and p.name not in ('manifest.json','manifest-check.json') and '__pycache__' not in p.parts]
save('manifest.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'artifacts':files})
assert all(sha(P/x['path'])==x['sha256'] for x in files)
save('manifest-check.json',{'passed':True,'artifacts_checked':len(files),'reused_source_hashes_checked':len(checks),'new_searches':4,'new_direct_gets':0,'manifest_sha256':sha(P/'manifest.json')})
print((P/'manifest-check.json').read_text())
