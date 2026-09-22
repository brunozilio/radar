# Muçum 86510000 — referência vertical e fuso

Pesquisa pública delimitada em 21/09/2026. Foram preservados PDFs/HTML, URLs, instantes de obtenção e SHA-256 nos três manifestos `reference-*-manifest.json`. Páginas relevantes foram conferidas visualmente. Nenhum dado, hipótese de fuso ou correção foi incorporado a treino ou pipeline.

## Resultado

**Zero ortométrico publicado encontrado; continuidade temporal e contrato de fuso atual ainda não verificados.** Manter o status de datum não validado para pareamento entre 2020, 2024 e 2026. UTC−03 tem suporte primário histórico e corroboração operacional atual, mas não há declaração explícita localizada que vincule o campo `DataHora` do endpoint legado atual à convenção.

## Referência vertical: o que as fontes demonstram

| Fonte primária | Evidência | Limite |
|---|---|---|
| [Nota SGB de zeros, versão 3, março/2026](https://rigeo.sgb.gov.br/handle/doc/25578.3), pp. 9, 11–12 | Muçum 86510000, marco PA 008, zero ortométrico **33,985 m**, modelo MAPGEO2015. Coordenadas do marco publicadas: 29°10′01,8947″ S, 51°52′07,8212″ W. | Não informa nesta linha data do levantamento, validade por período nem relação entre marco, réguas e sensor antes/depois das cheias. A edição é uma publicação de 2026, não prova de vistoria em 2026. |
| [Artigo SGB sobre a cheia de 2020](https://rigeo.sgb.gov.br/handle/doc/24429), p. 5 | Relata seção estável e ausência de registro de mudança do zero no histórico estudado; seção levantada em 22/07/2022; dados disponíveis até 08/2022. Pico de 22,02 m em 08/07/2020 obtido por nivelamento posterior, em 31/08/2020. | A afirmação não cobre as intervenções ou eventos de 2023–2026; máximo reconstruído posteriormente não equivale à telemetria disponível na hora. |
| [Nota SGB de marcas de cheia, versão 19, agosto/2026](https://rigeo.sgb.gov.br/handle/doc/24939.21), pp. 15, 18–19 | Tabela de Muçum adota zero **33,96 m** nas marcas; mantém RN01/RN02. Para 02/05/2024, máximo manual de **26,00 m** à noite versus sensor **25,57 m**, às 07:30. | Diferença entre máximos de 43 cm, com horários/métodos distintos; não é offset calibrável de toda a série. Diferença de 2,5 cm entre zeros publicados permanece sem explicação. |
| [Boletim SGB de 21/09/2026, 12h](https://www.sgb.gov.br/sace/boletins/Taquari/20260921_12-20260921%20-%20132721.pdf), pp. 2 e 4 | Identifica a estação no endereço Rua Marechal Floriano Peixoto e esclarece que cotas usam referência local arbitrária de cada régua. | Não fornece certificado de continuidade do zero nem offset do sensor atual. |

A nota de zeros v2/fevereiro2026 também foi preservada; a v3 é a referência mais recente localizada. A v3 esclarece na metodologia a exceção de Estrela em altura normal; a linha de Muçum continua sob MAPGEO2015/altura ortométrica. **Não somar 33,985 m à série automaticamente**, não misturar altura normal e ortométrica e não chamar a diferença 33,985–33,96 de arredondamento ou deslocamento físico confirmado.

## Fuso: evidência e lacuna precisa

A [apresentação ANA de 21/10/2020](https://progestao.ana.gov.br/destaque-superior/eventos/webinarios/cotas-de-alerta/3-definicao-de-valores-de-referencia.pdf), p. 4, reproduz o sistema oficial com a frase:

> Dados disponibilizados no horário UTC-3.

A interface também descreve Brasília sem horário de verão. O PDF e a captura já constavam da auditoria anterior (`manifest.json`, `ana-progestao-page4.png`). Isso sustenta a hipótese, mas não especifica o contrato da operação `DadosHidrometeorologicosGerais` em setembro/2026.

Foram consultados e preservados a [documentação atual da operação legada](https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx?op=DadosHidrometeorologicosGerais), [página Dados](https://www.ana.gov.br/telemetria1ws/Dados.aspx), [página Contato](https://www.ana.gov.br/telemetria1ws/Contato.aspx) e o [manual público HidroWebService](https://www.gov.br/ana/pt-br/assuntos/monitoramento-e-eventos-criticos/monitoramento-hidrologico/orientacoes-manuais/manuais/manual-hidrowebservice_publica.pdf). Não foi localizada declaração de fuso para esse campo. O manual novo tem escopo diferente do serviço legado. A página legada avisa de descontinuação e possível defasagem da base secundária; responder HTTP 200 hoje não garante atualização ou contrato futuro.

Corroboração limitada: o boletim SGB de 21/09/2026 às 12h indica 708 cm; a resposta ANA já coletada no projeto apresenta `DataHora=2026-09-21 12:00:00`, `NivelFinal=708.00`, aprovado. Às 09h o XML contém 493 cm. Isso confirma coincidência do relógio nominal e valor neste caso, **não prova o fuso**. A evidência e hash do XML de origem estão em `reference-status.json`.

A tentativa pública de `HidroInventario` para 86510000 retornou HTTP 500; foi registrada sem contornar acesso. Não foi encontrada publicamente, nesta rodada, monografia atual completa da estação nem histórico de manutenção que resolva as lacunas.

## Próximo passo exato, sem mensagem enviada

1. **SGB/SAH Taquari:** canal público `alerta.taquari@sgb.gov.br`, publicado no boletim atual. Solicitar monografia PA008 e RN01/RN02; datas GNSS, modelo/datum e processamento; vínculo nivelado marco–zero–sensor; validade e eventuais correções/relocações em 2020, setembro/2023, maio/2024 e 2026; motivo da diferença 33,985 m versus 33,96 m; curvas-chave, medições de descarga e seções com respectivas datas de validade. Pedir confirmação de que o nível operacional atual e os históricos pertencem ao mesmo referencial, ou tabela de offsets e vigências.
2. **ANA:** canal técnico público `hidro@ana.gov.br`, indicado na página do serviço. Solicitar confirmação escrita de fuso fixo/DST do campo `DataHora` em `DadosHidrometeorologicosGerais`, inclusive versões históricas; significado dos instantes de medição/recepção; política de revisão e defasagem; documentação/migração oficial aplicável à estação.
3. Até receber os metadados, preservar valores originais, timestamps ingênuos e conversão explicitamente presumida. Aprovação de QC do fornecedor não substitui verificação de datum, fuso, representatividade do pico ou disponibilidade histórica. Usar marcas retrospectivas apenas com essa proveniência; não apresentá-las como observações disponíveis ao emitir previsão no passado.

Nenhum contato externo foi realizado. Não houve alocação de teste oculto, treinamento, alteração do coletor ou promoção de modelo nesta investigação.
