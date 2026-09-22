"""Bounded contract review from already preserved primary evidence; no requests."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent;R=P.parents[1];checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,d):(P/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def ck(n,b):checks.append({'check':n,'passed':bool(b)});assert b,n
sources=[
('outputs/pesquisa-ana-qualidade-20260921T231424Z/ana-telemetria1ws-2013.pdf','https://www.ana.gov.br/telemetria1ws/Telemetria1ws.pdf','manual2013; distinct operation DadosHidrometeorologicos','outputs/pesquisa-ana-qualidade-20260921T231424Z/source-manifest.json'),
('outputs/pesquisa-referencia-legacy-20260921/sources/legacy-wsdl-public-proxy.xml','https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx?wsdl','target-operation generic response schema','outputs/pesquisa-referencia-legacy-20260921/new-source-manifest.json'),
('outputs/pesquisa-referencia-legacy-20260921/contract-evidence.json',None,'prior bounded WSDL/DISCO interpretation',None),
('outputs/verificacao-contrato-temporal-mucum/raw/ana-form-mucum-data.html','https://www.snirh.gov.br/hidrotelemetria/gerarGrafico.aspx','selected86510000; public presentationUTC−3','outputs/verificacao-contrato-temporal-mucum/manifest.json'),
('outputs/verificacao-contrato-temporal-mucum/comparison-summary.json',None,'73nominal records comparison and ArcGIS crosscheck',None),
('outputs/verificacao-contrato-temporal-mucum/README.md',None,'prior public routing/backend trace limits',None),
('outputs/verificacao-contrato-temporal-mucum/raw/sace-root.html','https://sace.sgb.gov.br/taquari/','public SACE timezone session script','outputs/verificacao-contrato-temporal-mucum/manifest.json'),
('outputs/historico-cheias-mucum/documentation/ana-progestao-referencias-2020.pdf','https://progestao.ana.gov.br/destaque-superior/eventos/webinarios/cotas-de-alerta/3-definicao-de-valores-de-referencia.pdf','ANA2020 presentation interface timezone; not legacy operation contract','outputs/historico-cheias-mucum/documentation/manifest.json'),
('outputs/historico-cheias-mucum/documentation/ana-hidrowebservice-manual-2026.pdf','https://www.gov.br/ana/pt-br/assuntos/monitoramento-e-eventos-criticos/monitoramento-hidrologico/orientacoes-manuais/manuais/manual-hidrowebservice_publica.pdf','newAPI manual2026 distinct measurement/update times','outputs/historico-cheias-mucum/documentation/reference-investigation-manifest.json'),
('outputs/historico-cheias-mucum/documentation/ana-hidrowebservice-manual-2026.txt',None,'text derived from preceding PDF',None),
('outputs/pesquisa-hidroweb-convencional-mucum-20260922/sources/ana-formato-hidro.pdf','https://www.ana.gov.br/arquivos/infohidrologicas/cadastro/OrientacoesParaEnvioDosDadosHidrologicosColetadosDuranteaResolucaoANEEL_396_1998.pdf','HIDRO2012 month/hour/daily-mean layout','outputs/pesquisa-hidroweb-convencional-mucum-20260922/sources/ana-formato-hidro.pdf.source.json'),
('outputs/pesquisa-hidroweb-convencional-mucum-20260922/sources/ana-formato-hidro.txt',None,'text derived from preceding PDF',None),
('outputs/pesquisa-hidroweb-convencional-mucum-20260922/sources/new-api-v1-openapi.json','https://www.ana.gov.br/hidrowebservice/api-docs/Vers%C3%A3o%20-%20v1.0.3984.2','newAPI public OpenAPI; notlegacy','outputs/pesquisa-hidroweb-convencional-mucum-20260922/sources/new-api-v1-openapi.json.source.json'),
('outputs/pesquisa-hidroweb-convencional-mucum-20260922/records-original-fields.jsonl',None,'12conventional monthly source records',None),
('outputs/historico-cheias-mucum/documentation/reference-investigation-report.md',None,'gaugezero/currentvalidity limits',None)]
manifest=[]
for file,url,scope,meta in sources:
 p=R/file;ck('exists:'+file,p.exists());m={'file':file,'url':url,'scope':scope,'sha256':sha(p),'bytes':p.stat().st_size,'newly_downloaded':False}
 if meta:
  f=R/meta;ck('provenance exists:'+meta,f.exists());m['original_provenance_file']=meta;m['original_provenance_sha256']=sha(f)
 manifest.append(m)
dump('reused-source-manifest.json',manifest)
# Explicit lexical search of the new relevant document bodies, distinguishing false positives.
patterns={'utc':r'\bUTC\b','gmt':r'\bGMT\b','timezone':r'timezone','fuso':r'\bfuso\b','dst_or_summer':r'\bDST\b|hor[aá]rio\s+de\s+ver[aã]o','brasilia':r'Bras[ií]lia'}
texts={'legacy_manual_full':(P/'legacy-manual-extracted.txt').read_text(),'newAPI_manual':(R/sources[9][0]).read_text(),'hidro2012_layout':(R/sources[11][0]).read_text(),'legacy_wsdl':(R/sources[1][0]).read_text()}
search={}
for name,text in texts.items():
 search[name]={k:[{'line':i,'text':line[:500]} for i,line in enumerate(text.splitlines(),1) if re.search(p,line,re.I)] for k,p in patterns.items()}
ck('legacy manual operation differs','DadosHidrometeorologicosGerais' not in texts['legacy_manual_full'] and 'DadosHidrometeorologicos' in texts['legacy_manual_full'])
ck('legacy manual noUTC/GMT/DST/timezone/fuso',not any(search['legacy_manual_full'][k] for k in ('utc','gmt','timezone','fuso','dst_or_summer')))
ck('new manual separates update andmeasurement','Data_Atualizacao' in texts['newAPI_manual'] and 'Data_Hora_Medicao' in texts['newAPI_manual'])
html=(R/sources[3][0]).read_text();ck('portalUTC3stationidentity',bool(re.search('lblMensagemGmt[^\n]*UTC-3',html)) and '86510000' in html)
ck('portal no explicit operation binding','DadosHidrometeorologicosGerais' not in html and 'ServiceANA.asmx' not in html)
sace=(R/sources[6][0]).read_text();ck('SACE timezone dependent','getTimezoneOffset' in sace and 'setTimeZone' in sace)
api=json.loads((R/sources[12][0]).read_text());apihits=[]
def walk(x,path='$'):
 if isinstance(x,dict):
  for k,v in x.items():walk(v,path+'.'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,path+f'[{i}]')
 elif isinstance(x,str) and any(re.search(v,x,re.I) for v in patterns.values()):apihits.append({'jsonpath':path,'text':x})
walk(api);ck('OpenAPI no explicit timezone keywords',not apihits)
rr=[json.loads(x) for x in (R/sources[13][0]).read_text().splitlines()];ck('monthlyDataHora separate from dayfield',len(rr)==12 and all(r['DataHora'][8:10]=='01' for r in rr) and any(r['MediaDiaria']=='1' for r in rr) and any(r['MediaDiaria']=='0' for r in rr))
old=json.loads((R/sources[2][0]).read_text());ck('prior WSDL no DataHora contract',old['response_has_explicit_DataHora'] is False)
dump('bounded-text-search.json',{'source_search':search,'newAPI_openapi_hits':apihits,'scope':'Extracted text and publicHTML/OpenAPI only; lexicalabsence isnot globalproof. Brasilia occurrences in addresses are not timezone statements.'})
dump('conclusion.json',{'audited_at_utc':datetime.now(timezone.utc).isoformat(),'station':'86510000','target_operation':'DadosHidrometeorologicosGerais','target_field':'DataHora','target_years':[2025,2026],'explicit_timezone_contract_found':False,'explicit_DST_contract_found':False,'presentation_product_UTCminus3_found':True,'legacy_convention_currently_corroborated_not_certified':True,'new_network_requests':0,'new_primary_sources':0,'authentication_or_external_messages':False,'changed_eligibility_flags':False,'missing':['Official statement binding timezone/DST to this operation/field, with applicable dates/versions.','Meaning of measurement vs reception/publication timestamps in legacy response.','Historical release/revision evidence; administrativeDataIns isnot firstpublication.'],'reason_no_new_sources':'PreviousWSDL/DISCO/manual/backend tracing already completed; newly recovered conventionaldocumentation adds no targetoperation timezone link. No discovered unreviewed primary endpoint with stronger evidence; avoid repeating searches/downloads.'})
dump('verification.json',{'passed':all(c['passed'] for c in checks),'checks_count':len(checks),'checks':checks,'new_requests':0,'no_models_or_flags_changed':True})
print('PASS',len(checks),'checks; no newrequests; legacytimezone remains unverified')
