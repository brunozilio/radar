"""Independent raw XML and ALL-QC normalized-source reconstruction."""
from pathlib import Path
import hashlib,json,math,xml.etree.ElementTree as ET
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
DATA=ROOT/'outputs/radar-insumos-observados-2020-20260921'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((DATA/'artifact-hashes.json').read_text())
for name,digest in m['files'].items():assert sha(DATA/name)==digest
sources={};source_hashes={}
for s in json.loads((DATA/'source-manifest.json').read_text()):
 p=ROOT/s['source_path'];assert sha(p)==s['sha256'];source_hashes[s['source_path']]=s['sha256']
 sources[s['source_path']]=[{c.tag.split('}')[-1]:c.text for c in e} for e in ET.fromstring(p.read_bytes()).iter() if e.tag.split('}')[-1]=='DadosHidrometereologicos']
fields={'level_m_raw':('NivelFinal',100),'flow_m3s_raw':('VazaoFinal',1),'rain_mm_raw':('ChuvaFinal',1),'counter_mm_raw':('ChuvaAcumAdotada',1)}
rows_count=refs_count=stations=0
for path in sorted((DATA/'stations').glob('*-all-qc.jsonl')):
 rows=[json.loads(s) for s in path.read_text().splitlines()];code=path.name.split('-')[1]
 z=np.load(DATA/'stations'/f'ana-{code}-normalized-all-qc.npz')
 assert all(len(z[k])==len(rows) for k in z.files)
 assert len({r['DataHora'] for r in rows})==len(rows)
 for i,r in enumerate(rows):
  for ref in r['source_references']:
   raw=sources[ref['source_file']][ref['source_record_index']-1]
   assert all(r[k]==v for k,v in raw.items())
   assert ref['source_sha256']==source_hashes[ref['source_file']]
   refs_count+=1
  assert z['time_original'][i]==r['DataHora']
  assert z['source_file'][i]==r['source_file'] and z['source_sha256'][i]==r['source_sha256'] and int(z['source_record_index'][i])==r['source_record_index']
  for k,(rawfield,scale) in fields.items():
   try:value=float(r[rawfield])/scale
   except (TypeError,ValueError):value=math.nan
   if not math.isfinite(value):assert np.isnan(z[k][i])
   else:assert z[k][i]==value
   assert z[rawfield+'_qc'][i]==(r.get('CQ_'+rawfield) or '')
 rows_count+=len(rows);stations+=1
result=dict(manifest_files_verified=len(m['files']),raw_sources_verified=len(sources),stations=stations,
 records_verified=rows_count,source_references_verified=refs_count,all_qc_numeric_time_provenance_exact=True,
 trained=False,promoted=False)
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
(OUT/'README.md').write_text(f"# Verificação independente do acervo2020\n\nConferidos{len(m['files'])} hashes do acervo e{len(sources)} XMLs de origem. As{rows_count} linhas de27 séries foram comparadas campo a campo aos registros XML indicados nas{refs_count} referências, incluindo duplicatas idênticas. Todos os campos numéricos ALL-QC, QC, timestamps e proveniência dos NPZs coincidem com os JSONLs. Não foi aplicado filtro de admissão, preenchimento ou treino.\n")
(OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
print(json.dumps(result,indent=2))
