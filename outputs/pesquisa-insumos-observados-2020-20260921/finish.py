"""Verify raw field preservation and preidentified extreme-origin input coverage."""
import csv
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from datetime import datetime,timedelta
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):(P/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
plan=json.loads((P/'collection-plan.json').read_text());coverage=json.loads((P/'coverage.json').read_text())
manifest=json.loads((P/'source-manifest.json').read_text());total=0;bycode={}
for m in manifest:
 body=(P/m['file']).read_bytes();assert sha(P/m['file'])==m['sha256']
 source=[{c.tag.split('}')[-1]:c.text for c in e} for e in ET.fromstring(body).iter() if e.tag.split('}')[-1]=='DadosHidrometereologicos']
 source.sort(key=lambda r:r['DataHora'])
 saved=[json.loads(s) for s in (P/'stations'/f"ana-{m['station']}-all-qc.jsonl").read_text().splitlines()]
 assert source==saved
 assert all(plan['window_start']<=r['DataHora'][:10]<=plan['window_end'] and r['CodEstacao']==m['station'] for r in saved)
 assert len({r['DataHora'] for r in saved})==len(saved)
 bycode[m['station']]=saved;total+=len(saved)
weights_path=ROOT/plan['weights_source'];assert sha(weights_path)==plan['weights_sha256']
weights=json.loads(weights_path.read_text())
available={s['station'] for s in coverage['stations'] if s['fields']['ChuvaFinal']['approved_numeric']}
ceilings=[dict(group=g['group'],any_approved_stations=[c for c in g['weights'] if c in available],
 weight_sum_at_best=sum(w for c,w in g['weights'].items() if c in available)) for g in weights]
prior=ROOT/'outputs/viabilidade-historico-antigo-radar-20260921'
for r in json.loads((prior/'artifact-hashes.json').read_text()):assert sha(prior/r['file'])==r['sha256']
pairs=[r for r in csv.DictReader((prior/'potential-pairs.csv').open()) if r['window'].startswith('2020') and r['horizon_h']=='12' and r['response_m'] and float(r['response_m'])>8.09]
assert len(pairs)==9
levelrows=bycode['86472000'];trace=[]
for r in pairs:
 origin=datetime.fromisoformat(r['origin']).replace(tzinfo=None)
 for back in (0,.5,1,2,4,8):
  query=origin-timedelta(hours=back,minutes=30)
  previous=[v for v in levelrows if datetime.fromisoformat(v['DataHora'])<=query]
  last=previous[-1] if previous else None
  source_time=datetime.fromisoformat(last['DataHora']) if last else None
  age=(query-source_time).total_seconds() if source_time else None
  value=float(last['NivelFinal'])/100 if last and last.get('NivelFinal') is not None else math.nan
  usable=last is not None and age<=900 and math.isfinite(value) and value>=0 and last.get('CQ_NivelFinal') in (None,'Dado aprovado')
  trace.append(dict(origin=r['origin'],back_hours=back,query_naive=query.isoformat(),source_time_naive=last['DataHora'] if last else None,
   age_seconds=age,level_raw_cm=last.get('NivelFinal') if last else None,qc=last.get('CQ_NivelFinal') if last else None,
   eligible_level=bool(usable),level_m=value if usable else None))
with (P/'extreme-origin-linha-trace.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(trace[0]));w.writeheader();w.writerows(trace)
complete=sum(all(v['eligible_level'] for v in trace if v['origin']==r['origin']) for r in pairs)
write('verification.json',dict(raw_hashes_verified=len(manifest),raw_rows_exactly_preserved=total,
 existing_xmls_date_inspected=len(json.loads((P/'prior-source-review.json').read_text())),preidentified_extreme_origins=9,
 linha_level_lookups=len(trace),origins_with_all_six_linha_levels=complete,
 spatial_ceiling_warning='Sum of weights of probed stations with any approved rain, not observed temporal coverage. Other stations not queried.',
 spatial_ceilings=ceilings,reused_prior_pairs_file=str((prior/'potential-pairs.csv').relative_to(ROOT)),reused_prior_pairs_sha256=sha(prior/'potential-pairs.csv'),
 no_matrix=True,no_training=True,no_promotion=True))
lines=['# Insumos observados de julho de 2020: levantamento delimitado','',
 'Foram consultadas oito estações públicas ANA de 04 a 13/07/2020: três níveis auxiliares e o maior peso de cada uma das cinco regiões de chuva. A janela cobre as origens extremas previamente identificadas em07/07 e12/07; não é seleção de acertos de um modelo. Antes dos GETs,190 XMLs existentes dessas estações foram inspecionados e não continham registros nessa janela.','',
 f'As oito respostas HTTP200 estão preservadas com URL, horário, headers e SHA256. São {total:,} registros, conferidos campo a campo entre XML e JSONL, sem preenchimento, mudança de horário ou descarte dos valores/QC brutos. Não foi montada matriz ou ajustado modelo. Muçum e ONS foram reaproveitados por referência, sem novas consultas.','',
 '| Estação | Registros | Nível aprovado | Chuva aprovada | Cadência modal |', '|---|---:|---:|---:|---|']
for s in coverage['stations']:
 lines.append(f"| {s['station']} | {s['rows']} | {s['fields']['NivelFinal']['approved_numeric']} | {s['fields']['ChuvaFinal']['approved_numeric']} | {s['cadence_inferred_seconds']} s |")
lines+=['','## Lacunas relevantes','',
 'Santa Tereza86472600, Passo Carreiro86500000 e o posto principal Prata-Turvo86125050 retornaram ausência explícita de dados. HTTP200 não implica observações presentes.','',
 'Linha José Júlio86472000 tem todos960 timestamps de15min, mas só911 níveis aprovados:41 são suspeitos e oito estão vazios. A chuva está aprovada nas960 linhas. A diferença entre existência de linha e disponibilidade de nível foi mantida.', '',
 f'Nas nove origens de resposta>8,09m em12h já identificadas no acervo Muçum, os seis níveis necessários ao bloco Linha José Júlio (consultaO−30min e recuos0,5/1/2/4/8h, idade máxima15min após consulta) estão disponíveis em{complete}/9 origens. As54 consultas têm rastros em extreme-origin-linha-trace.csv. Isso não certifica Q/I, chuva regional, régua ou o futuro modelo.','',
 'O posto86450000 possui apenas46 chuvas, com ausência de linhas de05/07 00h a09/07 09h e de11/07 00h a13/07 23h. O posto Tainhas86160000 tem36 timestamps faltantes durante07–08/07 e106 chuvas vazias entre924 registros; apenas818 chuvas aprovadas. Alto Antas86060010 tem27 horários ausentes; Carreiro86479000 tem240/240 horários e chuvas aprovadas.','',
 '## Limite espacial da amostra','',
 '| Região | Soma máxima dos pesos dos postos consultados com alguma chuva aprovada |','|---|---:|']
for c in ceilings:lines.append(f"| {c['group']} | {c['weight_sum_at_best']:.6f} |")
lines+=['','Esses valores são tetos espaciais hipotéticos, não cobertura temporal de janelas nem chuva regional. Não renormalizar pesos ou tratar falta como zero. As demais estações com peso positivo precisam ser examinadas antes de formar os75 campos regionais.','',
 '## Limites e próximo passo','',
 'Os timestamps ingênuos e valores originais foram preservados. Datum/fuso, publicação histórica e comparabilidade dos regimes continuam pendentes. O acervo ONS previamente auditado contém zeros reportados suspeitos em Monte Claro/14 de Julho no pico de08/07; esta coleta não os corrige nem certifica. As origens extremas têm dados correntes de Q/I segundo a auditoria anterior, mas a matriz completa e a propagação de faltas pelos atrasos ainda precisam de verificação.', '',
 'Há dados úteis, mas lacunas importantes. O próximo passo de preparação exige completar as estações de chuva, preservar filtros QC explícitos e auditar valores/lags das usinas. Este lote2020 já é desenvolvimento inspecionado; não é um novo holdout. As janelas2021/2022 reservadas separadamente não foram consultadas ou usadas aqui.','',
 'Reprodução local: audit.py lê os oito XMLs; finish.py confere campos, hashes, tetos e rastros. collect.py registra cada tentativa e não repete automaticamente uma requisição com sidecar existente.']
(P/'README.md').write_text('\n'.join(lines)+'\n')
write('artifact-hashes.json',[dict(file=str(p.relative_to(P)),sha256=sha(p)) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'])
print(json.dumps(dict(raw_sources=len(manifest),rows_verified=total,linha_extreme_origins_complete=complete,artifacts=len(json.loads((P/'artifact-hashes.json').read_text()))),indent=2))
