"""Read-only source inspection; writes only this investigation's evidence artifacts."""
from pathlib import Path
import hashlib, json, datetime, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, value):
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

manifest = json.loads((OUT/'new-source-manifest.json').read_text())
assert len(manifest) == 3
for x in manifest:
    p = OUT/x['file']
    assert sha(p) == x['sha256'] and p.stat().st_size == x['bytes']
assert sha(OUT/manifest[1]['file']) == sha(OUT/manifest[2]['file'])
p = OUT/'sources/legacy-wsdl-advertised.xml'
s = p.read_text()
r = ET.fromstring(s)
ns = {'w':'http://schemas.xmlsoap.org/wsdl/', 's':'http://www.w3.org/2001/XMLSchema'}
request = r.find('.//s:element[@name="DadosHidrometeorologicosGerais"]', ns)
response = r.find('.//s:element[@name="DadosHidrometeorologicosGeraisResponse"]', ns)
terms = ['UTC','GMT','Brasília','Brasilia','timezone','fuso','86510000','NivelFinal','datum']
matches = {term:[{'line':i+1,'text':line.strip()} for i,line in enumerate(s.splitlines()) if term.casefold() in line.casefold()] for term in terms}
datahora_owners = []
for e in r.findall('.//s:schema/s:element', ns):
    if e.findall('.//s:element[@name="DataHora"]', ns):
        datahora_owners.append(e.get('name'))
evidence = {
  'inspected_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'new_urls_count':len(manifest),
  'same_wsdl_bytes_at_advertised_and_public_proxy':True,
  'request_parameters':[e.attrib for e in request.findall('.//s:element',ns)],
  'response_schema':ET.tostring(response,encoding='unicode'),
  'response_has_explicit_DataHora':bool(response.findall('.//s:element[@name="DataHora"]',ns)),
  'other_operations_owning_DataHora_parameter':datahora_owners,
  'operation_documentation_excerpt':'Sem a validação dos filtros (dados gerais).',
  'operation_documentation_line':next(i+1 for i,line in enumerate(s.splitlines()) if 'Sem a validação dos filtros (dados gerais)' in line),
  'bounded_literal_search':matches,
  'conclusion':{'legacy_DataHora_timezone_certified':False,'station_level_reference_validity_2025_2026_certified':False,'absence_scope':'Only inspected WSDL and reused public evidence; not a claim that no documentation exists elsewhere.'},
  'caution':'DataHora parameters belong to write/delete methods, not to the target read response. No such write/delete method was called. No QC flags changed.'
}
save('contract-evidence.json', evidence)
files = [
'outputs/historico-cheias-mucum/documentation/reference-investigation-report.md',
'outputs/historico-cheias-mucum/documentation/ana-legado-service-doc.html',
'outputs/historico-cheias-mucum/documentation/sgb-zeros-ortometricos-v3-2026.pdf',
'outputs/historico-cheias-mucum/documentation/sgb-cheia2024-v19-2026.pdf',
'outputs/historico-cheias-mucum/documentation/sgb-mucum-cheia2020-artigo.pdf',
'outputs/historico-cheias-mucum/documentation/reference-latest-version-manifest.json',
'outputs/historico-cheias-mucum/documentation/reference-investigation-manifest.json',
'outputs/historico-cheias-mucum/documentation/ana-progestao-referencias-2020.pdf',
'outputs/verificacao-contrato-temporal-mucum/README.md',
'outputs/verificacao-contrato-temporal-mucum/manifest.json',
'outputs/verificacao-contrato-temporal-mucum/raw/ana-form-mucum-data.html',
'outputs/verificacao-contrato-temporal-mucum/comparison-summary.json',
'outputs/pesquisa-mucum-referencia-20260921T214433Z/search-log.json']
save('reused-evidence.json',[{'path':f,'sha256':sha(ROOT/f),'bytes':(ROOT/f).stat().st_size,'provenance':'Existing local evidence; not downloaded again. Earlier report supplies interpretation of PDFs.'} for f in files])
save('artifact-hashes.json',[{'path':str(p.relative_to(OUT)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'])
print(json.dumps({'new_sources_verified':len(manifest),'wsdl_identical':True,'timezone_search_matches':sum(len(v) for v in matches.values()),'other_DataHora_operations':datahora_owners},ensure_ascii=False))
