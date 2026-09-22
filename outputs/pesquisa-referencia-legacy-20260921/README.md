# Muçum — contrato legado e referência atual

Pesquisa delimitada em 21/09/2026. **Não foi encontrada certificação suficiente do fuso de `DataHora` na operação legada nem da vigência da referência de nível em 2025–2026.** Nenhuma flag de elegibilidade, fonte, modelo ou automação foi alterada. Nenhum contato externo foi realizado.

## Nova evidência primária

A documentação da operação já preservada publica um link de descoberta [DISCO da ANA](https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx?disco). Ele aponta expressamente para o [WSDL do serviço](http://telemetriaws1.ana.gov.br/ServiceANA.asmx?wsdl). O mesmo contrato está acessível pelo [endereço público HTTPS da ANA](https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx?wsdl). Foram exatamente três URLs novas: HTTP 200, respostas integrais preservadas, horários de coleta, cabeçalhos e SHA-256 em `new-source-manifest.json`. Os dois WSDLs têm 65.116 bytes e SHA-256 idêntico.

O contrato define `codEstacao`, `dataInicio` e `dataFim` como strings; a resposta de `DadosHidrometeorologicosGerais` usa schema/diffgram genérico. Não define individualmente `DataHora`, `NivelFinal`, unidade ou datum da estação. A documentação da operação contém o trecho “Sem a validação dos filtros (dados gerais).” Isso não especifica o algoritmo de QC e não autoriza reinterpretar os códigos de aprovação.

Os parâmetros `DataHora` encontrados em outras partes do WSDL pertencem a operações de inclusão/exclusão, não ao schema da resposta consultada. Nenhuma dessas operações foi chamada. A identidade entre os WSDLs confirma o contrato publicado nesses endereços; não prova o backend do portal gráfico, o fuso dos valores retornados ou versões históricas. `contract-evidence.json` registra a inspeção reproduzível e a busca literal limitada.

## Evidência anterior reutilizada

O [portal ANA de gráficos](https://www.snirh.gov.br/hidrotelemetria/gerarGrafico.aspx), já preservado com Muçum selecionada, declara UTC−3 e nível em cm. A auditoria anterior encontrou 73 níveis idênticos ao legado no relógio nominal; o último também coincide com o timestamp UTC do mapa oficial. É corroboração da convenção atual, não contrato explícito de `DataHora`. O HTML não revelou ligação pública do backend ao método legado. O manual do novo HidroWebService não foi usado para certificar o legado.

A [nota SGB de zeros, março/2026](https://rigeo.sgb.gov.br/handle/doc/25578.3), publica 33,985 m ortométricos/MAPGEO2015 para Muçum, marco PA008. A [nota SGB de marcas, agosto/2026](https://rigeo.sgb.gov.br/handle/doc/24939.21), usa 33,96 m e RN01/RN02. A diferença de 2,5 cm segue sem explicação documentada. Datas de edição não são datas de levantamento nem de início de validade. O [artigo sobre 2020](https://rigeo.sgb.gov.br/handle/doc/24429) não estende sua avaliação de estabilidade aos eventos de 2023–2026. PDFs existentes não foram baixados novamente; caminhos e hashes estão em `reused-evidence.json`.

## Lacunas exatas

- Declaração da ANA aplicável ao **campo `DataHora` dessa operação**, distinguindo UTC−3 fixo/DST, medição versus recepção, vigência e versões históricas.
- Monografia e nivelamento que liguem PA008/RN01/RN02 ao zero das réguas e sensor operacional, com manutenção, relocações, offsets e datas de validade em 2025–2026; explicação dos dois zeros publicados.
- Histórico de revisão e publicação necessário para provar disponibilidade dos dados ao emitir cada previsão passada.

Os canais públicos já documentados são `hidro@ana.gov.br` e `alerta.taquari@sgb.gov.br`; nenhum pedido foi enviado. Até haver resposta ou documento explícito, a conversão do legado permanece hipótese corroborada e a continuidade física do datum permanece não verificada. Esta busca negativa é limitada ao acervo e aos três recursos consultados; não demonstra inexistência de documentação em outros locais.

Reprodução local: `/usr/bin/python3 outputs/pesquisa-referencia-legacy-20260921/verify_evidence.py`. O verificador apenas lê as fontes e atualiza os artefatos deste diretório. Não consulta a rede nem modifica o pipeline.
