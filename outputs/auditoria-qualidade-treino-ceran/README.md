# Auditoria local da qualidade das entradas CERAN/ONS do treino

Executada em21/09/2026, sem downloads, correções, interpolação, ajuste ou avaliação de modelos. Leitura limitada às entradas, transformação e proveniência; não foram usados alvos de nível para selecionar limpeza. Artefatos, fontes e código lidos têm SHA-256 em `source-fingerprints.json`. O script independente `audit_local.py` só escreve nesta pasta.

## Conclusão

**Há uma anomalia concreta de Monte Claro no arquivo efetivamente usado no treino final.** Os zeros da cheia de22/07/2026 sobrevivem à normalização e ao atraso de uma hora. Não foi encontrado padrão equivalente de zeros em Castro Alves. A subida atual de Castro Alves está fora das subidas históricas disponíveis, mas permanece compatível com os dados e componentes consultados; não foi declarada inválida.

O histórico mensal contém38.764linhas ONS, em18CSV deabril2025 asetembro2026, até21/09/2026 às11h. Há mais9instantes aproveitados do JSON CERAN e3do HTML recente na fusão. A reconstrução das seis séries Q/I de `telemetria.npz` produziu **zero divergências em51.701pontos por série**. Todas as32exposições de15min das8linhas sinalizadas foram também localizadas, com Q/I idênticos, no arquivo congelado `outputs/mucum-atualizacao-15h-2026-09-21/telemetria-latencia.npz`.

## O que entra no modelo

No `scripts/hydro_routing_data.py`, linhas85–111:

- `julho:Q`, `monte:Q`, `castro:Q` vêm de `val_vazaodefluente`; `*:I` vem de `val_vazaoafluente`, em m³/s.
- Turbinada, vertida e outras estruturas **não são usadas para validar Q/I**. `number()` aceita zero e remove valores negativos/não finitos; não há coluna de QC do fornecedor.
- Nas sobreposições, ONS prevalece. JSON/HTML CERAN cobrem apenas instantes ausentes; Q/I vêm das colunas finais de saída e afluência, respectivamente.
- `asof` mantém o último registro por até90min na grade de15min; não interpola. O timestamp23:59 é mantido como publicado. Fuso fixoUTC−03 é assumido.

`hydro_latency_forecast.py` aplica ao histórico a latência da referência atual. No congelado de15h, as três usinas têm atraso60min. `hydro_hourly_models.py:upstream_features` usa Q/I divididos por1000 e suas diferenças de1h,3h e6h; por isso um zero espúrio afeta também várias tendências posteriores. `fit_ridge` preenche não finitos com a mediana do treino e acrescenta indicadores de ausência, mas trata zero como valor válido. Isso mostra um caminho possível de contaminação; não mede quanto cada anomalia alterou os coeficientes.

## Anomalias verificáveis e suspeitas separadas

### Contradição entre campos: Monte Claro,22/07/2026

Fonte: `outputs/mucum-propagacao-2026-09-21/raw/DADOS_HIDROLOGICOS_HO_2026_07-ceran.csv`, linhas2000–2002 (cabeçalho é linha1).

| Hora original UTC−03 presumido | Linha | Afluente | Defluente | Turbinada | Vertida | Outras |
|---|---:|---:|---:|---:|---:|---:|
|07h|2000|0|0|0|0|6|
|08h|2001|0|0|0|0|6|
|09h|2002|9969|0|0|0|6|

Unidade:m³/s. A soma de componentes declarada pelo ONS não coincide com Qdef=0. Além disso, Qdef era9907 às06h e volta9907 às10h; I era9999 às06h, cai a zero e volta9969 às09h. Esse padrão é **suspeita de falha/saturação/registro**, sem diagnóstico causal confirmado. O número9999 isolado não prova limite do sensor.

No congelado com atraso60min:

- `monte:Q=0` nos12slots de08h00 até10h45.
- `monte:I=0` nos8slots de08h00 até09h45; de10h00 a10h45,I=9969.
- As diferenças de1/3/6h podem tocar nove origens horárias, de08h a16h, apenas por dependência dessas entradas. Não foram reavaliados os alvos dessas origens.

Rastreio completo em `frozen-training-anomaly-trace.csv`; valores, campos, linhas e razões em `anomalies.csv`. Todos os zeros Q/I, inclusive os não sinalizados como contraditórios, estão em `all-zero-QI-rows.csv`; componentes ausentes em `missing-components.csv`.

### Outras contradições pequenas

Em03/05/2025 às15h, as três usinas têm componentes turbinada/vertida/outras zerados e Qdef positivo:14deJulho28,CastroAlves18,MonteClaro20m³/s. Linhas64,808,1551 do CSVmaio2025. Em24/08/2026 às04h, MonteClaro tem residual de balanço−2m³/s, pequeno e potencialmente relacionado a arredondamento, sem confirmação. Não zerar, somar ou substituir campos para forçar fechamento.

### Suspeita sem contradição direta

MonteClaro em07/08/2025 às11h tem I=0,Q=200; a soma de saída fecha. Pode haver armazenamento, método de cálculo ou erro; não é contradição física demonstrada.14deJulho tem dois valoresI=0 com saídas pequenas, sem descumprimento do diagnóstico de balanço. Zeros não foram automaticamente invalidados.

## Lacunas e cobertura

| Usina | Linhas ONS | Horas sem linha* | Nulos Q/I nas linhas | Zeros Q / I | Residuais de balanço >1m³/s |
|---|---:|---:|---:|---:|---:|
|Castro Alves|12921|2|0/0|0/0|1|
|14deJulho|12922|1|0/0|0/2|1|
|MonteClaro|12921|2|0/0|3/3|5|

\*Somente entre primeiro e último registro, tratando23:59 como fechamento24h para contar a grade, hipótese não aplicada aos valores de produção. Lacunas:CastroAlves30/05/2025 02h e03/08/2026 14h;14deJulho22/12/2025 10h;MonteClaro30/05/2025 01–02h. O `asof` cobre parte da lacuna com leitura anterior e depois produzNaN. Na grade original completa há6/5/10pontos ausentes por série deCastro/Julho/Monte, incluindo início anterior ao primeiro dado. Sem datas duplicadas. Um registro deCastro possui componente ausente e não permite testar o balanço; nenhum nulo deQ/I foi preenchido no inventário bruto.

## Castro Alves: extremo atual, não erro demonstrado

Não há Q/I zero, negativo ou nulo nas12921linhas; há duas horas sem linha e a contradição pequena de03/05/2025 já descrita. Antes de21/09, a maior subida horária afluente encontrada foi+693m³/s; na manhã de21/09 passa de605→1372→2834m³/s, subidas+767 e+1462. Qdef vai279→513→1205; o nível montante cresce240,53→241,11→242,21m. Os componentes ONS às11h somam152+1032+21=1205. O HTML CERAN publica I=2833,81,Q=1205,20 no mesmo relógio nominal. Isso reforça consistência interna, não comprova o valor físico nem autoriza truncar a subida ao máximo histórico. Ver `jumps-ge500-review.csv`: limiar500m³/s/h é apenas triagem, também captura subidas legítimas de cheia.

### Semântica CERAN versus ONS

Nos85pares sobrepostos por usina (JSON/HTML incluem observações repetidas), diferenças absolutas Q/I ficam abaixo de0,50m³/s, compatíveis com arredondamento. No HTML, `Q=turbinada+vertida`; somar novamente a coluna remanescente gera excesso. No exemploCastro11h, CERANvertida1053,20, enquantoONSvertida1032 eoutras21. Portanto **não aplicar a equação ONS diretamente às colunas CERAN como se tivessem partições iguais**. A correspondência observada é evidência de semântica distinta; requer documentação da operadora antes de automatizar reconciliação. Todas as comparações estão em `ceran-ons-overlaps.csv`.

## Limitações e próximo experimento

A documentação primária ONS previamente preservada em `outputs/historico-vazoes-ceran/raw/` estabelece hora-fim, unidades e convençãoBrasília da rotina; o catálogo alerta que os dados horários dos agentes não são consistidos pelo ONS e podem ser revisados. O contrato histórico do exportador e disponibilidade na hora original permanecem pendentes. Nove hashes2025 coincidem com o manifesto de coleta; os nove registros2026 nele dizem apenas `cached:true`, sem URL/hash original. Foram criadas impressões digitais atuais, que não restauram a proveniência perdida. Não foi baixada outra versão para sobrescrever os arquivos.

A [nota CERAN de04/05/2026](https://ceran.com.br/sem-categoria/ceran-atualiza-a-situacao-das-usinas-hidreletricas-apos-2-anos-das-cheias/), já preservada no lote anterior, registra obras preventivas emCastroAlves desde novembro2025; faltam curvas hidráulicas e vigências. Não afirmar mudança de calibração só a partir da obra.

Próximo passo proposto: criar candidato separado com uma política de qualidade definida previamente, distinguindo contradições de componentes, suspeita de falha e extremos legítimos; conservar série original e resultados anteriores. Auditar disponibilidade/latência e medir impacto em blocos temporais separados. Não selecionar exclusões pelo erro do teste nem promover um modelo por remover retrospectivamente os casos difíceis. Esta auditoria não alterou dados, definições do teste ou previsão.
