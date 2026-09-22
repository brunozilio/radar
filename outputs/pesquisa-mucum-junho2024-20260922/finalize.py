from pathlib import Path
import json,hashlib,datetime
P=Path(__file__).resolve().parent;R=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(P/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
paths=['outputs/mucum-propagacao-2026-09-21/raw/sgb-boletins-lista.html','outputs/historico-cheias-mucum/documentation/reference-investigation-report.md','outputs/historico-cheias-mucum/documentation/sgb-cheia2024-v19-2026.txt','outputs/pesquisa-mucum-manutencao-20260922T020248Z/README.md','outputs/pesquisa-armazenamento-ceran/README.md','outputs/historico-vazoes-ceran/raw/ons-sala-crise-2024-05-09.pdf','outputs/historico-vazoes-ceran/raw/ons-sala-crise-2024-05-09.txt','outputs/historico-vazoes-ceran/raw/ceran-situacao-2anos-2026.html','outputs/historico-vazoes-ceran/source-manifest.json']
old=json.loads((R/'outputs/historico-vazoes-ceran/source-manifest.json').read_text())
reused=[]
for p in paths:
 rec={'file':p,'sha256':sha(R/p),'bytes':(R/p).stat().st_size,'new_request':False}
 if isinstance(old,list):
  matches=[x for x in old if isinstance(x,dict) and (Path(p).name in str(x.get('path','')) or Path(p).name in str(x.get('file','')))]
  if matches:rec['prior_receipts']=matches
 reused.append(rec)
save('reused-source-hashes.json',reused)
receipts=[json.loads(p.read_text()) for p in sorted((P/'raw').glob('*.receipt.json'))]
assert len(receipts)==3 and all(x['http_status']==200 for x in receipts)
for x in receipts:assert sha(P/x['file'])==x['sha256']
save('source-manifest.json',{'collected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'new_searches':4,'new_direct_gets':3,'limit_searches':4,'limit_gets':4,'no_more_requests_planned':True,'receipts':receipts,'reused_sources':'reused-source-hashes.json','original_operational_source_receipts':'outputs/historico-vazoes-ceran/source-manifest.json','scope_note':'Only station86510000 for15–21June2024; noauxiliary/NWP/ONS requests, nofit/inference.'})
files=[p for p in P.rglob('*') if p.is_file() and p.name not in ('manifest.json','manifest-check.json') and '__pycache__' not in p.parts]
manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[{'file':str(p.relative_to(P)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)]}
save('manifest.json',manifest)
checks=[sha(P/x['file'])==x['sha256'] for x in manifest['files']]
save('manifest-check.json',{'passed':all(checks),'checked_artifacts':len(checks),'manifest_sha256':sha(P/'manifest.json'),'verified_raw_receipts':len(receipts)})
print((P/'manifest-check.json').read_text())
