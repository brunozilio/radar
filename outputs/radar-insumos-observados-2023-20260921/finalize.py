"""Validate local collection/normalization and write a bounded human report."""
from pathlib import Path
from datetime import datetime,timezone
import json,csv,hashlib,math
import numpy as np
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((P/'collection-plan.json').read_text());coverage=json.loads((P/'coverage.json').read_text());sources=json.loads((P/'source-manifest.json').read_text());ons=json.loads((P/'ons-references.json').read_text());checks=[]
def check(name,ok):checks.append({'check':name,'passed':bool(ok)})
new=[r for r in sources if 'requested_at_utc' in r];check('new_GET_count27',len(new)==27);check('all_new_HTTP200',all(r.get('http_status')==200 for r in new));check('plan_before_requests',all(plan['registered_at_utc']<r['requested_at_utc'] for r in new));check('reused_XML_count11',sum(r.get('status')=='verified_reuse' for r in sources)==11)
for r in sources:check('raw_hash:'+r['source_path'],sha(ROOT/r['source_path'])==r['sha256'])
for f,h in plan['reference_hashes'].items():check('prior_reference_hash:'+f,sha(ROOT/f)==h)
for r in ons:
    check('ONS_CSV_hash:'+r['month'],sha(ROOT/r['literal_csv'])==r['csv_sha256']);check('ONS_raw_hash:'+r['month'],sha(ROOT/r['raw_source_path'])==r['raw_source_sha256'])
mapping={'NivelFinal':('level_m_raw',100),'VazaoFinal':('flow_m3s_raw',1),'ChuvaFinal':('rain_mm_raw',1),'ChuvaAcumAdotada':('counter_mm_raw',1)}
def numeric(v):
    try:x=float(v)
    except (ValueError,TypeError):return np.nan
    return x if math.isfinite(x) else np.nan
qcrows=[]
for station in coverage['stations']:
    c=station['station'];rr=[json.loads(l) for l in (P/'stations'/f'ana-{c}-all-qc.jsonl').read_text().splitlines()];a=np.load(P/'stations'/f'ana-{c}-normalized-all-qc.npz');check('literal_times:'+c,list(a['time_original'])==[r['DataHora'] for r in rr]);check('record_count:'+c,len(rr)==station['records'])
    for f,(key,scale) in mapping.items():
        check('numeric_preservation:'+c+':'+f,np.array_equal(a[key],np.array([numeric(r.get(f))/scale for r in rr]),equal_nan=True));check('QC_preservation:'+c+':'+f,list(a[f+'_qc'])==[r.get('CQ_'+f) or '' for r in rr]);v=station['fields'][f];qcrows.append({'station':c,'field':f,'records':len(rr),'modal_cadence_seconds':station['modal_cadence_seconds'],**{k:v[k] for k in ['numeric','empty','nonempty_nonnumeric','approved_numeric','suspect_numeric','numeric_without_qc','parser_compatible','negative','first_approved','last_approved']}})
with (P/'qc-summary.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(qcrows[0]));w.writeheader();w.writerows(qcrows)
status={'verified_at_utc':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in checks),'check_count':len(checks),'checks':checks,'all_series_count':len(coverage['stations']),'total_rows':sum(r['records'] for r in coverage['stations']),'all_QC_preserved':True,'trained':False,'matrix_built':False,'imputed':False,'no_new_ONS_or_NWP_requests':True};(P/'validation.json').write_text(json.dumps(status,indent=2)+'\n');assert status['passed']
lines=['# Acervo observado Radar — 29/08 a 30/09/2023','',
       '**Coleta concluída dentro do limite: 27 novos GETs ANA, 11 XMLs reutilizados e nenhuma consulta nova ONS/NWP.** O plano foi gravado antes de todas as requisições. As respostas novas foram HTTP200; ausência de dados da estação permanece distinta de falha de transporte.',
       '', 'São **27 séries com 19.265 registros**, 17.083 valores de chuva aprovados. No conjunto de 38 respostas novas/reutilizadas, 31 contêm registros e sete informam Sem dados. Não há duplicação de timestamps dentro de estação. Isso não significa cobertura integral dos 33 dias.',
       '', '## Procedência e escopo', '',
       'collection-plan.json preserva data do pré-registro, inventário, pesos/latências por hash e cada janela autorizada. Os oito postos da coleta anterior foram consultados apenas de05 a30/09; seus XMLs29/08–04/09 foram reutilizados. Os18outros postos receberam uma consulta29/08–30/09. Muçum recebeu apenas29–31/08, pois todo setembro já estava preservado em três respostas. Não houve retentativa automática ou sobreposição deliberada de consultas.',
       '', '## Inventário por estação', '',
       '| Estação | Registros | Níveis aprovados | Chuvas aprovadas | Cadência modal (min) | Último registro original |',
       '|---|---:|---:|---:|---:|---|']
for r in coverage['stations']:lines.append(f"| {r['station']} | {r['records']} | {r['fields']['NivelFinal']['approved_numeric']} | {r['fields']['ChuvaFinal']['approved_numeric']} | {r['modal_cadence_seconds']//60 if r['modal_cadence_seconds'] else '—'} | {r['last'] or 'Sem registro'} |")
lines += ['', 'QC aprovado é atributo da fonte, não nova certificação física. approved_numeric exige valor numérico e CQ aprovado; valores aprovados negativos permanecem explicitamente contabilizados. parser_compatible é uma contagem diagnóstica separada, sem modificar as séries.',
          '', '## Ausências e ressalvas principais', '',
          '- **Muçum86510000:** 2.652registros, 2.311níveis aprovados,11suspeitos e330vazios. Nenhum registro após25/09 22h45. A interrupção no pico já conhecida continua: último nível aprovado04/09 19h30, retorno08/09 14h15. A marca retrospectiva não foi inserida. Os516slots sem registro incluem28em04/09 22h–05/09 04h45,4em07/09 10h–10h45 e484após25/09 22h45.',
          '- **Linha José Júlio86472000:** 2.683registros,2.682níveis aprovados e1vazio;2.681chuvas aprovadas e2vazias. Último registro25/09 22h30;485slots de15min ausentes no fim da janela.',
          '- **Santa Tereza86472600:** a primeira resposta29/08–04/09 é Sem dados. A extensão contém apenas16registros de30/09 20h–23h45, todos sem nível e chuva finais. Não interpretar como recuperação de observações utilizáveis.',
          '- **Passo Carreiro86500000,86125000 e86504900:** zero registros em toda a janela. Não são zeros de nível, vazão ou chuva.',
          '- **86450000 e86479000:** as extensões05–30/09 retornaram Sem dados; seus registros permanecem limitados à coleta anterior, encerrando04/09 às03h e09h respectivamente. São postos de peso importante nas regiões Baixo Antas e Carreiro.',
          '- **86160000:**3.128registros;2.639chuvas aprovadas e489vazias, última chuva aprovada25/09 22h45 embora os registros continuem até30/09. 36timestamps faltam no início29/08 00h–08h45 e4em24/09 20h–20h45. Seus níveis incluem11suspeitos e4vazios, preservados.',
          '- **86200900,86493000,86495500:** contêm registros, mas nenhum valor numérico aprovado de ChuvaFinal. QC isolado não constitui chuva observada.',
          '- Nas estações predominantemente horárias, o diagnóstico usa792slots em33dias, não3.168slots de15min. Cobertura menor pode resultar de lacunas reais, início/fim antecipado ou cadência diferente. coverage.json mantém ambos os diagnósticos e todos os intervalos; nenhum deles implica precipitação zero.',
          '', 'Respostas Sem dados no acervo:86472600 e86500000 em29/08–04/09;86125000 e86504900 em29/08–30/09;86450000,86479000 e86500000 em05–30/09. São mensagens Error no XML com HTTP200, preservadas em source-manifest.json. Não ocorreu falha de rede registrada no lote novo.',
          '', '## Normalização sem apagar QC', '',
          'stations/ contém27JSONL integrais com todos os campos/QC originais, data literal, arquivo de origem, SHA256 e índice do registro XML; e27NPZ com time_original, source_file, source_record_index, level_m_raw, flow_m3s_raw, rain_mm_raw, counter_mm_raw e quatro arrays deQC. A única transformação de unidade é NivelFinal cm→m. Números suspeitos/negativos continuam presentes; NaN representa ausência/não-numérico e o texto original permanece noJSONL. Não se aplicou máscara de elegibilidade, interpretação de época/fuso, interpolação, ajuste de curva ou preenchimento.',
          '', 'OsNPZ são acervo normalizado comQC, **não arquivos prontos para o pipeline**. Um futuro builder deve aplicar explicitamente seu protocolo causal/QC e cobertura, mantendo separados dado ausente e valor zero. As duas estações auxiliares sem nível impedem complete24, mas nenhuma política de treino foi alterada aqui.',
          '', '## ONS reaproveitado,23h59 literal', '',
          '- Agosto: outputs/historico-ceran-2023-complemento-20260921/ceran-source-values.csv, filtrado apenas por din_instante iniciado em2023-08 para esta auditoria.744registros por usina,31horários23h59 por usina. EsseCSV também contém outros meses; um futuro consumidor precisa selecionar a janela.',
          '- Setembro: outputs/historico-cheia-setembro-2023/ons-ceran-source-values.csv.714registros por usina,30horários23h59 por usina. As lacunas previamente conhecidas não foram preenchidas.',
          'Ambos osCSVs coincidem com os hashes dos manifestos originais; oCSV bruto deagosto e oParquet desetembro também foram conferidos. ons-references.json inclui links oficiais, metadados prévios e hashes. Foi lida apenas a coluna din_instante; a coluna histórica hour_end_interpreted_assumed doCSV deagosto foi ignorada. Nenhum23h59 foi convertido para00h e nenhum download ONS foi realizado.',
          '', '## Limites e arquivos', '',
          'Nenhuma previsão meteorológica foi coletada ou substituída por reanálise/chuva futura. O acervo apenas permite desenhar depois um estudo observado de120campos. Não foram montados acumulados regionais, matriz, alvos, treino ou inferências. Fuso histórico, disponibilidade na emissão, referência vertical e comparabilidade dos regimes permanecem não certificados. Setembro2023 já foi inspecionado e não é um holdout novo.',
          '', 'Scripts: collect.py --plan registra o plano; collect.py --collect respeita sidecars existentes e não repete pedidos; audit.py processa apenas fontes locais; finalize.py verifica a normalização, hashes e este relatório. Não executar novamente o plano existente. source-manifest.json e ons-references.json vinculam fontes completas; coverage.json e qc-summary.csv detalhamQC/cadências/lacunas; validation.json registra verificações; artifact-hashes.json cobre os artefatos próprios.',
          '', f'**{len(checks)} verificações de integridade/normalização passaram.** Nenhum arquivo anterior, modelo, pipeline ou automação foi alterado. Sem HGE/ARNO, promoção ou comunicação externa.']
(P/'README.md').write_text('\n'.join(lines)+'\n')
hashes={str(f.relative_to(P)):sha(f) for f in sorted(P.rglob('*')) if f.is_file() and f.name!='artifact-hashes.json'};(P/'artifact-hashes.json').write_text(json.dumps({'generated_at_utc':datetime.now(timezone.utc).isoformat(),'files':hashes},indent=2)+'\n');print('checks',len(checks),'pass',status['passed'],'artifacts',len(hashes),'sources',len(sources),'rows',status['total_rows'])
