# Evidências de fuso e referência de nível

Consultado em 21/09/2026. Esta nota não promove a hipótese de fuso do XML a contrato confirmado, nem valida o datum físico atual da régua.

## Evidência primária de UTC−03

A apresentação de Vinícius Roman/ANA, de 21/10/2020, “Definição de Valores de Referência para Sistemas de Alerta”, página 4, reproduz a interface oficial Hidro-Telemetria. O trecho foi verificado visualmente em `ana-progestao-page4.png`:

> Dados disponibilizados no horário UTC-3.

O quadro inferior direito explica, em paráfrase, que o horário é o de Brasília sem ajuste de verão, chuva em mm, nível em cm e vazão em m³/s. [Fonte ANA/Progestão](https://progestao.ana.gov.br/destaque-superior/eventos/webinarios/cotas-de-alerta/3-definicao-de-valores-de-referencia.pdf). O PDF bruto e seu hash estão nesta pasta.

Isso fundamenta UTC−03 como hipótese informada pela documentação do sistema. Ainda falta vincular explicitamente essa convenção à resposta de `DadosHidrometeorologicosGerais` e verificar se houve mudanças entre versões. O [manual do webservice legado](https://www.ana.gov.br/telemetria1ws/Telemetria1ws.pdf), seção 2.1, lista DataHora, mas na leitura desta seção não informa o fuso. Por isso CSVs mantêm coluna original ingênua e coluna `timestamp_utc_assuming_minus03`, com status explícito de hipótese.

Outra fonte primária, o [manual ANA de envio de dados horários do setor elétrico](https://www.gov.br/ana/pt-br/assuntos/monitoramento-e-eventos-criticos/monitoramento-hidrologico/monitoramento-hidrologico-do-setor-eletrico/resolucao-conjunta-ana-aneel-127-2022/ManualparaEnvioDadosHidrologicosHorarios.pdf), estabelece Brasília sem verão para envio. Seu escopo é o setor elétrico e não prova sozinho o contrato da estação Muçum.

## Referência da régua permanece pendente

O [relatório SGB de marcas de cheia 2024](https://rigeo.sgb.gov.br/handle/doc/24939.5) possui muitas revisões. A versão antiga indexada apresenta zero ortométrico e referências levantadas em Muçum, mas não estabeleci validade dessa referência no sensor atual nem continuidade com 2020. Não foi aplicada qualquer conversão altimétrica. A próxima auditoria deve obter a versão vigente, RN/zero, histórico de manutenção/relocação e datas das curvas-chave e seções.

Não confundir a telemetria contínua com máximos obtidos por leitura manual/marca de cheia. O [artigo SGB sobre marcas de 2024](https://rigeo.sgb.gov.br/handle/doc/25517) distingue esses procedimentos. A ausência de um máximo reportado na série do sensor precisa ser investigada, não corrigida automaticamente.
