"""Independently compare preserved XML records with normalized ALL-QC artifacts."""
import csv,json,hashlib,math,xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
def check(name,ok):checks.append(dict(check=name,passed=bool(ok)));assert ok,name
def save(name,rs):
 with (OUT/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def numeric(s):
 try:v=float(s)
 except (ValueError,TypeError):return np.nan
 return v if math.isfinite(v) else np.nan
plan=json.loads((OUT/'collection-plan.json').read_text());coverage=json.loads((OUT/'coverage.json').read_text());sources=json.loads((OUT/'source-manifest.json').read_text());sourcehash={r['source_path']:r['sha256'] for r in sources if 'source_path' in r};duplicates=json.loads((OUT/'duplicate-audit.json').read_text());xml={};fields=Counter();qcrows=[];fieldflags=[];rawcomparison=0
new=[r for r in sources if r.get('status')!='verified_reuse'];check('34GETs_under36',len(new)==34<=plan['max_new_gets']);check('all34HTTP200',all(r.get('http_status')==200 for r in new));check('plan_before_all_requests',all(plan['registered_at_utc']<r['requested_at_utc'] for r in new));check('11XMLreuse',len(sources)-len(new)==11);check('no_conflict',duplicates['conflicting_occurrences']==0)
for p,h in plan['reference_hashes'].items():check('priorhash '+p,sha(ROOT/p)==h)
for r in sources:
 if 'source_path' not in r:continue
 p=ROOT/r['source_path'];check('rawhash '+r['source_path'],sha(p)==r['sha256']);xml[r['source_path']]=[{c.tag.split('}')[-1]:c.text for c in e} for e in ET.parse(p).getroot().iter() if e.tag.split('}')[-1]=='DadosHidrometereologicos']
for r in new:check('planlink '+r['file'],r['plan_sha256']==sha(OUT/'collection-plan.json'))
for info in coverage['stations']:
 code=info['station'];rows=[json.loads(s) for s in (OUT/'stations'/f'ana-{code}-all-qc.jsonl').read_text().splitlines()];a=dict(np.load(OUT/'stations'/f'ana-{code}-normalized-all-qc.npz'));times=[r['DataHora'] for r in rows];check('station rows '+code,len(rows)==info['records']);check('unique sorted times '+code,times==sorted(set(times)));check('literal dates '+code,list(a['time_original'])==times)
 for r in rows:
  original={k:v for k,v in r.items() if not k.startswith('source_')};fields.update(original.keys())
  for field in ['NivelFinal','VazaoFinal','ChuvaFinal','ChuvaAcumAdotada']:
   v=numeric(r.get(field));qc=r.get('CQ_'+field)
   if not np.isfinite(v) or v<0 or qc not in ('Dado aprovado',None):fieldflags.append(dict(station=code,time=r['DataHora'],field=field,value_literal=r.get(field),qc=qc,nonnumeric_or_missing=not np.isfinite(v),negative=bool(v<0),source_file=r['source_file'],source_record_index=r['source_record_index']))
  for ref in r['source_references']:
   assert original==xml[ref['source_file']][ref['source_record_index']-1];assert ref['source_sha256']==sourcehash[ref['source_file']];rawcomparison+=1
 for key in ['source_file','source_sha256','source_record_index']:check('NPZ provenance '+code+key,list(a[key])==[r[key] for r in rows])
 for field,key,scale in [('NivelFinal','level_m_raw',100),('VazaoFinal','flow_m3s_raw',1),('ChuvaFinal','rain_mm_raw',1),('ChuvaAcumAdotada','counter_mm_raw',1)]:
  expected=np.array([numeric(r.get(field))/scale for r in rows]);check('rawnumeric '+code+field,np.array_equal(expected,a[key],equal_nan=True));check('QC '+code+field,list(a[field+'_qc'])==[r.get('CQ_'+field) or '' for r in rows]);f=info['fields'][field];qcrows.append(dict(station=code,field=field,records=len(rows),modal_cadence_seconds=info['modal_cadence_seconds'],**{k:f[k] for k in ['numeric','empty','nonempty_nonnumeric','approved_numeric','suspect_numeric','numeric_without_qc','parser_compatible','negative','first_approved','last_approved']}))
 check('all_fields_source_identical '+code,True)
save('qc-summary.csv',qcrows);save('field-flags.csv',fieldflags);(OUT/'raw-field-inventory.json').write_text(json.dumps(dict(fields_record_counts=dict(fields),normalized_fields=['NivelFinal cm→m','VazaoFinal m3/s','ChuvaFinal mm','ChuvaAcumAdotada mm'],all_other_fields_preserved_in_jsonl=True),indent=2)+'\n')
report=dict(passed=True,verified_at_utc=datetime.now(timezone.utc).isoformat(),check_count=len(checks),checks=checks,raw_record_comparisons=rawcomparison,total_unique_rows=sum(r['records'] for r in coverage['stations']),total_rain_approved=sum(r['fields']['ChuvaFinal']['approved_numeric'] for r in coverage['stations']),total_level_approved=sum(r['fields']['NivelFinal']['approved_numeric'] for r in coverage['stations']),new_GETs=len(new),reused_XMLs=len(sources)-len(new),duplicates=duplicates['duplicate_occurrences'],conflicts=duplicates['conflicting_occurrences'],statuses=coverage['statuses'],all_QC_preserved=True,no_interpolation=True,no_rounding=True,no_zero_fill=True,trained=False,matrix_built=False,network_scope='Only2020ANA34GETs; no2021/22,ONS,NWP requests',no_operational_edits=True)
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
lines=['# Acervo ANA observado Radar — 28/06 a20/07/2020','',f"**34 novos GETs, abaixo do teto36, sem retentativas;11 XMLs reutilizados.** Todos os pedidos novos retornaramHTTP200. O plano foi registrado antes da rede. Foram preservadas27séries e{report['total_unique_rows']:,}linhas únicas, com{report['total_level_approved']:,}níveis e{report['total_rain_approved']:,}valores de chuva numericamentes presentes e CQaprovado.",'',
'Os oito XMLs da triagem04–13/07 foram reaproveitados; apenas28/06–03/07 e14–20/07 foram pedidos para esses postos. Outros18postos receberam a janela inteira. Muçum reutiliza junho/julho já preservados, sem novo pedido. A amostra Muçum09/07 foi reutilizada para comparação de versão:96 registros sobrepostos idênticos em todos os campos, sem conflito; normalização mantém uma linha e todas as referências.','',
'## Inventário por estação','', '| Estação | Registros | H aprovado | Chuva aprovada | Cadência modal/min | Primeiro | Último |','|---|---:|---:|---:|---:|---|---|']
for r in coverage['stations']:lines.append(f"| {r['station']} | {r['records']} | {r['fields']['NivelFinal']['approved_numeric']} | {r['fields']['ChuvaFinal']['approved_numeric']} | {r['modal_cadence_seconds']/60 if r['modal_cadence_seconds'] else '—'} | {r['first'] or '—'} | {r['last'] or '—'} |")
lines+=['',f"Estados das45 respostas preservadas/referenciadas: {coverage['statuses']}. Semdados é conteúdo XML comHTTP200, distinto de falha de rede. Não representa valor hidrológico zero.",'',
'## Lacunas e qualidade','',
'Cinco postos não possuem registros em toda a janela:86125000,86125050,86472600(SantaTereza),86500000(Carreiro),86504900. Não foram preenchidos. O acervo não satisfaz complete24 devido aos dois níveis auxiliares sem observação; esta coleta não altera critérios de treino.','']
for code in ['86510000','86472000','86160000','86450000','86125050','86479000']:
 r=next(r for r in coverage['stations'] if r['station']==code);h=r['fields']['NivelFinal'];rain=r['fields']['ChuvaFinal'];lines.append(f"- {code}: {r['records']} registros; H {h['approved_numeric']}aprovados, {h['suspect_numeric']}suspeitos, {h['empty']}vazios; chuva {rain['approved_numeric']}aprovados, {rain['suspect_numeric']}suspeitos, {rain['empty']}vazios. Último H aprovado: {h['last_approved']}; última chuva aprovada: {rain['last_approved']}.")
lines+=['',
'coverage.json preserva todas as lacunas, cadências, fases da grade e distribuição dos segundos. São23dias:2.208slots para postos de15min e552para os horários; não usar2.208 como denominador universal. A presença do timestamp tampouco implica H/chuva aprovado. Muçum e LinhaJoséJúlio possuem2.208timestamps cada, mas incluem QC não aprovado/ausência de valores. Marcas retrospectivas do pico não foram inseridas.','',
'## Normalização e verificação','',
'Cada JSONL contém todos os campos do XML, QC literal, DataHora original, source_file/source_sha256/source_record_index e source_references. O NPZ preserva datas literais e a proveniência principal; apenas NivelFinal passa de cm para m. Vazão, chuva e contador mantêm valores, incluindo negativos ou suspeitos, acompanhados de QC. NaN representa campo ausente/não numérico, cujo texto permanece no JSONL. Nenhuma seleção por qualidade, arredondamento temporal, interpolação ou preenchimento por zero.','',f"Foram comparadas{rawcomparison:,}referências de registro diretamente com osXMLs originais, campo por campo;{len(checks)}verificações passaram. Índices são1-based na ordem original XML. Duplicatas idênticas e seus hashes estão emduplicate-audit.json; conflitos impediriam a seleção automática. Numericamente aprovado significa CQ da fonte, não certificação física nova.",'',
'EssesNPZ ALL-QC não são matrizes prontas do modelo. O futuro preparo deverá declarar QC, causalidade, atrasos e seleção temporal, preservando faltas. Fuso, datum, revisões históricas e disponibilidade na emissão não foram certificados por esta coleta.','',
'## Escopo e reprodução','',
'collect.py --plan preregistra; --collect respeita sidecars e não repete tentativas existentes. audit.py e finalize.py usam apenas fontes locais. source-manifest.json contém URL, horários, HTTP, headers/hash das novas respostas e metadados do cache. O acervo antigo foi referenciado, não modificado. Referências de consulta emcollection-plan.json e todos os artefatos próprios emartifact-hashes.json.','',
'Nenhuma consulta2021/2022, ONS, meteorologia, treino, matriz ou ação operacional. Nenhuma alteração de pesos/latências; sem modelos retirados, promoção ou declaração de meta.']
(OUT/'README.md').write_text('\n'.join(lines)+'\n');(OUT/'artifact-hashes.json').write_text(json.dumps(dict(generated_at_utc=datetime.now(timezone.utc).isoformat(),files={str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'}),indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
