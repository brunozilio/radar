from pathlib import Path
import json,hashlib,csv
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
url21='https://rigeo.sgb.gov.br/handle/doc/22570';url22='https://rigeo.sgb.gov.br/handle/doc/23700'
events=[dict(year=2021,event='maio',start='2021-05-28',end='2021-05-31',station='86510000',reported_peak_cm=715,reported_peak_literal='30/05/2021 07:45',peak_time_usable_as_documentary=True,pdf_page=28,printed_page=28,source=url21,proposed_query_start='2021-05-25',proposed_query_end='2021-06-02',note='Table3 observed maximum; not an isolated surveyed flood mark. Raw telemetric series not fetched.'),
 dict(year=2022,event='1',start='2022-05-01',end='2022-05-06',station='86510000',reported_peak_cm=1339,reported_peak_literal='04/05/2022 04:14',peak_time_usable_as_documentary=True,pdf_page=31,printed_page=27,source=url22,proposed_query_start='2022-04-28',proposed_query_end='2022-05-08',note='Table4; keep :14 literal, do not round.'),
 dict(year=2022,event='2',start='2022-05-28',end='2022-06-01',station='86510000',reported_peak_cm=1280,reported_peak_literal='04/05/2022 04:14',peak_time_usable_as_documentary=False,pdf_page=35,printed_page=31,source=url22,proposed_query_start='2022-05-25',proposed_query_end='2022-06-03',note='Conflict: narrative lateMay/earlyJune, table6 repeats earlyMay date; peak time unresolved, no correction by inference.'),
 dict(year=2022,event='3',start='2022-06-05',end='2022-06-10',station='86510000',reported_peak_cm=1243,reported_peak_literal='07/06/2022 05:44',peak_time_usable_as_documentary=True,pdf_page=40,printed_page=36,source=url22,proposed_query_start='2022-06-02',proposed_query_end='2022-06-12',note='Table8; literal :44 preserved.'),
 dict(year=2022,event='4',start='2022-06-21',end='2022-06-25',station='86510000',reported_peak_cm=1116,reported_peak_literal='23/06/2022 00:29',peak_time_usable_as_documentary=True,pdf_page=45,printed_page=41,source=url22,proposed_query_start='2022-06-18',proposed_query_end='2022-06-27',note='Table10; paragraph mistakenly says event3 under section4.4. Literal :29 preserved.')]
for event in events:
 event.update(documentary_inspected=True,raw_series_collected_this_stage=False,forecast_inference_performed_this_stage=False,training_performed_this_stage=False,reserved_for_future_test=False)
(OUT/'events.json').write_text(json.dumps(events,indent=2)+'\n')
with (OUT/'events.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(events[0]));w.writeheader();w.writerows(events)
catpath=ROOT/'outputs/historico-vazoes-ceran/raw/catalog.json';cat=json.loads(catpath.read_text())['result'];selected=[r for r in cat['resources'] if any(m in r['name'] for m in ['2021-05','2021-06','2022-04','2022-05','2022-06']) and r.get('format')=='PARQUET'];(OUT/'ons-next-resources.json').write_text(json.dumps(dict(catalog_source=str(catpath.relative_to(ROOT)),catalog_sha256=sha(catpath),license_id=cat.get('license_id'),license_title=cat.get('license_title'),resources=selected,payloads_fetched=False,plant_presence_verified=False),indent=2)+'\n')
prior=['outputs/historico-vazoes-ceran/raw/catalog.json','outputs/pesquisa-cobertura-meteorologica-antiga-20260921/documentary-evidence.md','outputs/historico-cheias-mucum/documentation/reference-investigation-report.md','outputs/viabilidade-historico-antigo-radar-20260921/README.md'];(OUT/'prior-input-hashes.json').write_text(json.dumps({s:sha(ROOT/s) for s in prior},indent=2)+'\n')
log=dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(),scope='Documentary only. Two searches, five distinct official URLs opened (two report landing pages, their twoPDFs, oneDefenseCivil page timeout). Repeated navigation within samePDFs is not additional source discovery. No ANA or ONS data requests.',search_queries=['site.sgb.gov.br Taquari 2022 inundação Muçum 2021 cheia','site.defesacivil.rs.gov.br 2022 Taquari Muçum cheia maio outubro'],sources=[dict(url=url21,status='metadata read',pdf='sources/sgb-2021.pdf'),dict(url=url22,status='metadata read',pdf='sources/sgb-2022.pdf'),dict(url='https://defesacivil.rs.gov.br/alerta-de-cheia-no-taquari',status='webopen timeout; search snippet only',snippet_publication='07/06/2022 09:21',independent_evidence_not_used_for_peak=True)],budgets=dict(searches=2,distinct_source_urls=5,combined=7,limit=8),limits='Web-tool exactrequesttimestamps unavailable; PDF directGETtimestamps and headers preserved separately.')
(OUT/'research-log.json').write_text(json.dumps(log,indent=2)+'\n')
(OUT/'documentary-evidence.md').write_text('''# Evidência documental — páginas identificadas

- SGB2021, PDF página28 (numeração impressa28), seção3.4/tabela3: janela28–31/05, estação86510000, máximo observado715cm em30/05 07:45. Figuras23–24 mostram evolução/chuva; não é somente marca de enchente nivelada posteriormente. Relatório cobre novembro2020–novembro2021, não prova ausência de eventos em dezembro2021. A edição permite reprodução com menção à fonte (PDFp4).
- SGB2022, PDFp22/impressa18, tabela2: identidadeMuçum86510000; LinhaJoséJúlio86472000; SantaTereza86472600. Nota curta: “Estação instalada no fim do ano de 2022 (em testes).” Aplica-se aSantaTereza. Texto adjacente descreve amostras15min agrupadas para transmissão horária; cadência de coleta não equivale a latência instantânea nem prova o fuso do legacy.
- SGB2022, PDFp31/impressa27 tabela4; p35/impressa31 tabela6; p40/impressa36 tabela8; p45/impressa41 tabela10: datas/máximos emevents.json. Evento2 contém conflito de datas; abertura fala três eventos, tabela3 enumera quatro e há quatro subseções. Não corrigidos silenciosamente.
- SGB2022 contém cotagramas e acumulados pluviométricos, mas não fornece nosPDFs o arquivo tabular de todas as amostras; pontos/curvas gráficas não foram digitalizados para treino.

Links estáveis: https://rigeo.sgb.gov.br/handle/doc/22570 e https://rigeo.sgb.gov.br/handle/doc/23700. PDFs completos preservados emsources comURL, UTC, HTTP, headers, tamanho eSHA256 no source-manifest.json.
''')
(OUT/'README.md').write_text('''# Pesquisa delimitada: episódios2021–2022 para Radar

Foram localizadas cinco janelas candidatas nos relatórios primários do SGB. Elas podem ampliar diversidade de subidas/recessões moderadas, mas **nenhuma série histórica foi coletada ou aprovada para treino nesta etapa**.

| Ano/evento | Janela descrita | Máximo Muçum86510000 | Horário literal publicado |
|---|---|---:|---|
|2021 maio|28–31/05|7,15m|30/05 07:45|
|2022 evento1|01–06/05|13,39m|04/05 04:14|
|2022 evento2|28/05–01/06|12,80m|Conflitante: tabela repete04/05 04:14|
|2022 evento3|05–10/06|12,43m|07/06 05:44|
|2022 evento4|21–25/06|11,16m|23/06 00:29|

Fontes: [SGB2021](https://rigeo.sgb.gov.br/handle/doc/22570), [SGB2022](https://rigeo.sgb.gov.br/handle/doc/23700). Páginas/tabelas emevents.json. São máximos reportados do monitoramento com cotagramas, não substitutos para rótulos horários. O segundo evento2022 exige resolver a data pela série bruta. A documentação2022 descreve coleta15min/transmissãohorária; SantaTereza aparece como instalação do fim de2022, em testes. [SGB2022](https://rigeo.sgb.gov.br/handle/doc/23700).

## Insumos e próxima coleta proposta

1. Priorizar pequenos pedidos públicos ANA de Muçum86510000 e LinhaJoséJúlio86472000 nas janelas propostas emevents.json, preservando todos timestamps/QC/NaNs. Confirmar cadence/phase, cobertura de subida/pico/recessão e dados disponíveis antes de montar matriz. Para reduzir pedidos sobrepostos em2022, unir25/05–12/06. Janelas incluem margem de aquecimento e futuro12h; não foram requisitadas aqui.
2. Consultar Carreiro86500000 e as27estações de chuva do modelo nas mesmas janelas somente após a triagem dos dois níveis principais. O relatório não prova cobertura dessas27 estações nem presença de Carreiro. Não esperar SantaTereza automaticamente em2021/maio–junho2022; tampouco extrapolar sua ausência documental para todo dado legado sem consulta.
3. Reutilizar catálogo oficial ONS já preservado: há recursos mensais Parquet maio/junho2021 e abril/maio/junho2022, listados emons-next-resources.json. Payloads não baixados; presença efetiva das três usinas, Q/I, falhas e convenção temporal precisam de auditoria. Manter23:59 literal; não converter máximo mensal em limite físico. Usinas identificadas para futura filtragem:JIUHQJ/JIUHMC/JIUHCA. O regime é anterior às avarias2024, sem certificação de equivalência física.
4. Para o Radar observado120/33/45/108, chuva medida é insumo possível, sujeito a cobertura/QC. A pesquisa Open-Meteo anterior não sustenta precipitation_previous_day1 dos mesmos três modelos em2021/2022; não presumir o conjunto180 disponível. Imagens/estimativas de precipitação posterior e reanálise não substituem previsões meteorológicas emitidas antes da origem. Não fizemos novas consultas meteorológicas.

## Risco específico da grade temporal

Os horários2022 terminam em:14/:29/:44/:59 nas tabelas. Isso é alerta de possível diferença de fase/representação: não demonstra que toda série tenha essa fase nem autoriza arredondar. O pipeline atual exige alvo exato na grade; inspecionar XML literal antes de dizer que dados faltam ou de mudar regra. Não converter horários emUTC nem declarar fuso/datum equivalente por coincidência do código da estação. Transmissãohorária não comprova disponibilidade pontual15min.

## Admissibilidade e limites

As janelas são pistas documentais, não observações prontas nem comprovação da meta. Inspecionamos documentos e máximos; **não houve inferência de previsões ou treino em2021/2022 nesta etapa**. Reservá-las explicitamente para teste histórico futuro antes de ajustar candidatos ainda é uma decisão possível, a ser registrada pelo responsável. Esta pesquisa não fez tal reserva, não chamou os anos de teste novo não inspecionado e não produziu evidência prospectiva. Máximos e gráficos não devem virar rótulos interpolados. Manter critérios de recorte e divisão temporal explícitos antes de qualquer ajuste. A comparação entre épocas depende de disponibilidade, revisão da fonte, referência de régua e operação das usinas. Ausência de um episódio no relatório não prova inexistência:2021cobre até novembro; esta pesquisa não foi exaustiva.

Foram duas buscas e cinco URLs oficiais distintas (sete itens úteis, limiteoito). O alerta DefesaCivil07/06/2022 apareceu na busca, mas a abertura expirou; não foi usado para validar horários ou picos. DoisPDFs totalizam10,6MB; nenhum arquivo anual de série, treino, consulta ANA/ONS, ação operacional ou mensagem externa. Manifestos preservamURL, UTC, headers eSHA256; todo acervo consultado anteriormente está referenciado porhash.
''')
(OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
for r in json.loads((OUT/'source-manifest.json').read_text()):assert sha(OUT/r['file'])==r['sha256']
print(len(events),'events;',len(selected),'ONS resources referenced;',len(json.loads((OUT/'artifact-hashes.json').read_text())),'artifacts hashed')
