from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
rows=[dict(file=str(f.relative_to(P)),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in sorted(P.rglob('*')) if f.is_file() and f.name!='artifact-hashes.json']
(P/'artifact-hashes.json').write_text(json.dumps(rows,indent=2)+'\n')
assert all(hashlib.sha256((P/r['file']).read_bytes()).hexdigest()==r['sha256'] for r in rows)
print(len(rows),'artifacts;',hashlib.sha256((P/'artifact-hashes.json').read_bytes()).hexdigest())
