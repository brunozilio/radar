# Muçum86510000 — séries convencionais recuperadas

**Dados recuperados nas três janelas**, sem autenticação, pelo método público documentado `HidroSerieHistorica`. São leituras de escala às07h/17h e médias diárias, **não uma série horária**. Não houve interpolação, conversão de unidade nos artefatos, treino, inferência, promoção ou alteração dos acervos anteriores.

## Resultado e a diferença entre consultas semanais e mensais

As seis consultas iniciais das semanas, com `tipoDados=1` e `nivelConsistencia=1/2`, retornaram HTTP200 com `Sem dados`. O dicionário oficial HIDRO descreve a tabela de cotas por mês e por dia. Foram então pré-registrados e consultados somente os três meses encapsuladores, nos mesmos dois níveis de consistência: **as seis respostas mensais retornaram registros**. Nenhum outro mês/estação foi consultado;12GETs de dados no total, sem retries automáticos.

Os registros retornados têm `DataHora` no **dia1** e campos `Cota01`…`Cota31`. O comportamento observado é compatível com filtragem pela data do registro mensal. Portanto, **“Sem dados” no pedido semanal não é prova de ausência da série convencional daquela semana**. Não foi inspecionado o backend para certificar sua implementação. As respostas semanais continuam preservadas, e o resultado não modifica as sondagens anteriores da operação distinta `DadosHidrometeorologicosGerais` de telemetria.

| Semana | Leituras brutas07h/17h presentes | Média diária bruta / consistida | Maior leitura bruta recuperada na janela, cm | Maior média diária consistida na janela, cm |
|---|---:|---:|---|---|
| 18–24/07/2011 | 14/14 | 7/7 e7/7 | 2010 em21/07,07:00 | 1955 em21/07 |
| 08–14/10/2015 | 14/14 | 7/7 e7/7 | 1693 em09/10,17:00 | 1675 em09/10 |
| 24–30/05/2017 | 14/14 | 7/7 e7/7 | 1233 em28/05,07:00 | 1224 em28/05 |

Esses máximos são dos valores amostrados, **não picos contínuos certificados**. A leitura2011 situa uma marca de2010cm em21/07/2011 na própria estação e oferece evidência primária para o catálogo; não exige corrigir silenciosamente as datas conflitantes do artigo consultado anteriormente.

Cada mês forneceu três registros brutos (`MediaDiaria=0` às07h/17h e`MediaDiaria=1` às00h) e um registro consistido de média diária. Total:12registros mensais,372posições de calendário inventariadas,357valores presentes. As15posições ausentes são02–06/07/2011 nas três séries brutas; a média diária consistida desses dias está presente. Nas três semanas-alvo não há valor faltante nas42leituras brutas ou42médias diárias combinadas. Não se contam as médias como novas observações independentes.

## Identidade, unidade, cadência e consistência

O [contrato oficial legado](https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx?op=HidroSerieHistorica) documenta1=cotas para`tipoDados`,1=bruto e2=consistido para`nivelConsistencia`. Cada um dos12registros retornados identifica`EstacaoCodigo=86510000` e o nível solicitado. `TipoMedicaoCotas=1` em todos os registros.

O [dicionário oficial HIDRO1.2](https://www.ana.gov.br/arquivos/infohidrologicas/cadastro/OrientacoesParaEnvioDosDadosHidrologicosColetadosDuranteaResolucaoANEEL_396_1998.pdf), PDFpp.26–28/impressas22–24, descreve`Cota01..31` em **cm**,`TipoMedicaoCotas=1` como escala e`MediaDiaria` distinguindo média diária e instante. As leituras brutas têm intervalos alternados de10h e14h; a meia-noite das médias diárias é rótulo do registro agregado, **não leitura instantânea00h**. A média bruta de cada dia com as duas leituras presentes foi conferida como média aritmética exata de07h e17h (88dias no conjunto dos três meses). Isso não demonstra a metodologia de todos os dados consistidos.

**Atenção a códigos de versões diferentes:** esse manual antigo usa0/1 para nível de consistência, enquanto a documentação da operação legada usada e as respostas usam1/2. Para esta coleta adotamos apenas o mapeamento explícito da operação. Não misturamos o código de consistência com o status de cada valor ou com o QC da API telemétrica nova.

Nos dias das janelas, todas as21médias consistidas possuem`CotaDDStatus=1`. O dicionário antigo associa1 a valor real,2 a estimado,3 a duvidoso,4 a régua seca e0 a branco; é uma referência de formato, **não prova de equivalência integral dos códigos entre todas as versões de serviço**. Nas42leituras brutas,40não trazem a tag de status e duas —14/10/2015 às07h/17h — possuem status3. A média bruta do mesmo dia também tem status3. Ausência de tag foi mantida como desconhecida, nunca convertida em aprovado/zero. No mês2011, os sete primeiros dias consistidos têm status2, fora da semana-alvo. Todos os campos e estados foram preservados.

## Versões e datas posteriores ao evento

| Mês | `DataIns` bruto, literal | `DataIns` consistido, literal |
|---|---|---|
| julho2011 | 2011-10-27 00:00:00 | 2018-06-29 00:00:00 |
| outubro2015 | 2016-01-26 00:00:00 | 2024-04-09 00:00:00 |
| maio2017 | 2017-10-06 00:00:00 | 2024-04-09 00:00:00 |

A semântica normativa exata de`DataIns` não está definida no contrato genérico consultado. São valores administrativos retornados e posteriores aos episódios; **não foram interpretados como primeira publicação, recepção original ou instante em que o dado se tornou disponível para uma previsão**. Não há histórico completo de versões.

A comparação das médias diárias brutas e consistidas registra3diferenças em2011,14em2015 e17em2017, além dos cinco dias2011 ausentes no bruto e presentes no consistido. Em2011 há diferença de−60cm em07/07 e+6cm em01/07: não reduzir todas as diferenças a arredondamento. Muitas diferenças de2015/2017 são0,5cm, mas não inferimos política formal de arredondamento. `raw-versus-consistent-daily.csv` preserva ambos os valores e diferenças diagnósticas; nenhum substituiu o outro. Não há duplicatas por data/hora/tipo de agregado/consistência; versões diferentes são separadas, não conflitos resolvidos automaticamente.

## API nova e metadados ainda pendentes

A documentação pública atual foi rastreada desde [Swagger oficial](https://www.ana.gov.br/hidrowebservice/swagger-ui/index.html), pelo inicializador e configuração até a OpenAPIv1. O endpoint publicado`/EstacoesTelemetricas/HidroSerieCotas/v1` descreve coleta manual, limita cada período a366dias e permite filtro por leitura ou última atualização. **Exige BearerJWT**. O manual20/02/2026 já preservado exige cadastro prévio e autorização; nenhuma consulta de dados da API nova, autenticação, criação de conta, uso de credencial ou mensagem foi executada. O trecho do contrato está em`new-api-contract-excerpt.json`.

O contrato legado retorna timestamps sem timezone e não fornece monografia de régua, vigência/offset, datum ou fuso/DST desses horários históricos. Os apontadores e limites da investigação anterior permanecem referenciados por hash. Nenhum timestamp foi convertido paraUTC. Recuperar dados com o mesmo código da estação não certifica continuidade do zero até2026.

## Admissibilidade para Radar

O acervo comprova nível convencional disponível para os episódios, inclusive durante a manutenção telemétrica mencionada em2017. É útil para caracterizar amplitude, datas e confrontar documentos. **Não autoriza preencher a grade horária nem oferecer42leituras como série completa para treino1–12h.** Uma eventual avaliação apenas nos horários efetivamente medidos exigiria protocolo específico de âncora, alvo, cadência, QC, disponibilidade histórica e entradas contemporâneas, sem usar a média do dia como observação conhecida no início dele. Nenhum desses experimentos foi feito.

## Proveniência e reprodução

-18requisições diretas novas:12dados e6documentação, todasHTTP200; seis corpos de dados com mensagemSemdados e seis com registros mensais.
-`plan.json` e`monthly-plan.json` precedem as respectivas consultas; os pedidos mensais respondem à estrutura documentada, sem novo evento.
-`raw/` e`sources/`: corpos imutáveis, URL, UTC de coleta, cabeçalhos eSHA256 por requisição;`source-manifest.json` reúne os18recibos.
-`records-original-fields.jsonl`:12registros originais, com índiceXML1-based e proveniência; nenhuma transformação de valor.
-`day-field-inventory.jsonl`:372posições, com data derivada explicitamente do mês/nome do campo e strings originais;`candidate-window-cells.jsonl` recorta84posições, sem fabricar horários/valores.
-`audit.py` verificou191condições, incluindo identidade, hashes, plano anterior à rede, extração campo a campo e cadência. Não importa helpers operacionais.
-`artifact-hashes.json` cobre todos os artefatos desta pasta, exceto o próprio manifesto. Fontes e investigações anteriores foram apenas lidas e referenciadas em`reused-source-hashes.json`.
