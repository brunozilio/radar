from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;R=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((P/'verification.json').read_text())['passed']
assert json.loads((P/'expected-weight-verification.json').read_text())['passed']
band=json.loads((P/'band-check.json').read_text());assert band['passed']
for mapping in (json.loads((P/'input-hashes.json').read_text()),json.loads((P/'expected-input-hashes.json').read_text()),band['input_sha256']):
 for path,digest in mapping.items():assert sha(R/path)==digest,path
items=[dict(file=str(p.relative_to(P)),sha256=sha(p)) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json']
(P/'artifact-hashes.json').write_text(json.dumps(items,indent=2)+'\n')
print(len(items),sha(P/'artifact-hashes.json'))
