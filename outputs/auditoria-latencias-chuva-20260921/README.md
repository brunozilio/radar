# Latências de chuva do Radar congelado às 15h

Reprodução somente local de prepare_current na origem **21/09/2026 15h00 UTC−3**. Os 27 caches normalized-*.npz foram lidos diretamente, sem chamar load_ana, merged ou prepare_current. Cada XML fresh substituiu o cache no mesmo timestamp, inclusive quando seu valor era ausente ou rejeitado. Nenhum modelo foi executado nem arquivo anterior alterado.

**Resultado: os 60 campos regionais de chuva e cobertura reproduzem exatamente a telemetria congelada**, incluindo as máscaras NaN: 51.709 linhas por campo, 3.102.540 posições comparadas, diferença numérica zero. Campos P/C dos cinco grupos nas janelas1/3/6/12/24/48h. Esta verificação comprova equivalência com aquele snapshot, não validade física dos valores ou publicação histórica de cada observação.

## Interface para o builder2024

Consumir latencies.json → stations[]:

- station: código ANA como string.
- delay_seconds: idade real da última ChuvaFinal finita em relação à origem15h.
- shift_steps_15min: int(delay_seconds/900), usado de fato no preparo.
- last_finite_rain_at: timestamp original interpretado no UTC−3 presumido pelo parser.

rain-delays.json fornece a mesma lista com os aliases station, rain_delay_seconds, rain_delay_steps e last_rain_time, solicitados durante a auditoria. Não há diferença de conteúdo; o builder pode usar diretamente latencies.json.

**Caso importante: 86125000 tem última chuva às11h59, idade181min=10.860s; o código aplica12passos=180min=10.800s.** O minuto restante é truncado. Para reproduzir o congelado, conservar essa regra; uma alteração posterior precisaria de novo protocolo e avaliação.

| Estação | Última chuva (21/09/2026) | Idade real min | Passos15min |
|---|---|---:|---:|
| 86060010 | 08:00 | 420 | 28 |
| 86099000 | 14:00 | 60 | 4 |
| 86102000 | 10:00 | 300 | 20 |
| 86117000 | 14:00 | 60 | 4 |
| 86125000 | 11:59 | 181 | 12 |
| 86125050 | 14:00 | 60 | 4 |
| 86160000 | 14:45 | 15 | 1 |
| 86163000 | 14:00 | 60 | 4 |
| 86200900 | 11:00 | 240 | 16 |
| 86280500 | 14:00 | 60 | 4 |
| 86298000 | 14:00 | 60 | 4 |
| 86403000 | 14:00 | 60 | 4 |
| 86410800 | 14:00 | 60 | 4 |
| 86447000 | 14:00 | 60 | 4 |
| 86448000 | 14:00 | 60 | 4 |
| 86450000 | 14:45 | 15 | 1 |
| 86471000 | 14:45 | 15 | 1 |
| 86472000 | 14:30 | 30 | 2 |
| 86472600 | 14:45 | 15 | 1 |
| 86479000 | 14:00 | 60 | 4 |
| 86488000 | 14:00 | 60 | 4 |
| 86493000 | 14:00 | 60 | 4 |
| 86495500 | 14:00 | 60 | 4 |
| 86500000 | 14:30 | 30 | 2 |
| 86504900 | 14:00 | 60 | 4 |
| 86505500 | 14:00 | 60 | 4 |
| 86510000 | 14:45 | 15 | 1 |

Todas as27últimas chuvas finitas vêm dos XMLs fresh e têm CQ Dado aprovado. Não houve estação sem chuva finita anterior à origem. Há valores fresh vazios em86200900(4),86493000(1),86495500(1), preservados como NaN. Em86200900 existe um registro vazio posterior à última chuva finita e não posterior à origem. Nenhuma revisão fresh nesta leitura transformou valor finito do cache em ausente. No conjunto histórico mesclado existem5.050 valores não finitos; eles não foram preenchidos.

## Método e limites

Caches existentes já representam o tratamento histórico anterior; esta auditoria não reparseia todos os XMLs históricos para certificar a construção desses caches. Nos XMLs fresh, reproduziu-se número finito e não negativo, QC aprovado ou ausente, limite150mm de ChuvaFinal. O valor mais recente finito até15h determina a idade; isso é diferente de selecionar a última linha independentemente da qualidade.

O integrador observado foi extraído por AST da função pura observed_rain_windows, sem importar módulos operacionais. Integra intervalos válidos e calcula cobertura; o atraso é aplicado aos acumulados e coberturas por shift. Pesos e ordem dos grupos são os originais. Os totais regionais usam nan_to_num como no preparo, e a precipitação fica NaN quando a cobertura ponderada é menor que0,5. Nenhuma renormalização espacial foi acrescentada.

Para2024, estas idades são uma hipótese fixa de atraso emprestada do snapshot2026, não evidência de disponibilidade histórica. Preservar timestamps originais, cadências/segundos, ausências e regra do integrador. Não converter automaticamente falta de estação em chuva zero com cobertura completa. Esta auditoria não construiu a matriz2024 nem treinou candidatos.

## Integridade

- source-manifest.json: SHA256 e tamanho dos27caches,27XMLs fresh, telemetria congelada, pesos e cinco fontes de código lidas.
- regional-comparison.json: cada comparação integral com máximos de diferença, máscaras, contagens e valores da última origem.
- latencies.json: dados de proveniência, QC, contagens e atrasos por estação.
- audit.py: reprodução somente local; escreve apenas neste diretório.
- artifact-hashes.json: SHA256 dos demais artefatos deste diretório.

Os nomes de campos mismatches_gt1e10 e total_mismatches_gt1e10 no JSON de comparação denotam a tolerância **1e−10** aplicada no código (atol=1e−10, rtol=0); ambos contam zero. A igualdade exata também foi testada independentemente dessa tolerância.
