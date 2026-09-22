# Pesquisa delimitada: episódios2021–2022 para Radar

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
