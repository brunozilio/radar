from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
P=Path(__file__).resolve().parent;R=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(P/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
receipts=[json.loads(p.read_text()) for p in sorted((P/'raw').glob('*.receipt.json'))]
assert len(receipts)==3
for r in receipts:assert sha(P/r['file'])==r['sha256'] and r['http_status']==200
reused=[]
for n in ['sgb-20240617-22.pdf','sgb-20240620-07.pdf']:
 f=R/'outputs/pesquisa-mucum-junho2024-20260922/raw'/n
 receipt=Path(str(f)+'.receipt.json')
 reused.append({'file':str(f.relative_to(R)),'sha256':sha(f),'receipt':str(receipt.relative_to(R)),'receipt_sha256':sha(receipt),'original_receipt':json.loads(receipt.read_text()),'role':'Primary station identity page2; contemporaneous level and cm page1; maintenance/metadata limits.'})
save('source-manifest.json',{'created_utc':datetime.now(timezone.utc).isoformat(),'new_gets':3,'new_searches':0,'receipts':receipts,'reused_sources':reused})
files=[{'file':str(p.relative_to(P)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(P.rglob('*')) if p.is_file() and p.name not in ('manifest.json','manifest-check.json') and '__pycache__' not in p.parts]
save('manifest.json',{'generated_utc':datetime.now(timezone.utc).isoformat(),'files':files})
assert all(sha(P/x['file'])==x['sha256'] for x in files)
v=json.loads((P/'verification.json').read_text());assert v['passed']
save('manifest-check.json',{'passed':True,'checked_artifacts':len(files),'verified_raw_receipts':3,'manifest_sha256':sha(P/'manifest.json'),'audit_checks':v['checks'],'xml_jsonl_records':v['xml_jsonl_roundtrip_records']})
print((P/'manifest-check.json').read_text())
