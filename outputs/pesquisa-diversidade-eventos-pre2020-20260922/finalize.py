from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
rows=[{'file':str(p.relative_to(P)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(P.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json']
(P/'artifact-hashes.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
assert all(hashlib.sha256((P/r['file']).read_bytes()).hexdigest()==r['sha256'] for r in rows)
print(len(rows),'artifact hashes;',hashlib.sha256((P/'artifact-hashes.json').read_bytes()).hexdigest())
