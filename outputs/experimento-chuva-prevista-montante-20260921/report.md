# Chuva prevista nos preditores de vazão

Foram acrescentadas 20 variáveis de chuva prevista à referência com níveis das usinas: acumulados de 3, 6, 9 e 12 h em cinco pontos, usando GFS/ECMWF/ICON. Cada média usa apenas membros com janela completa; dado ausente não vira chuva zero. Não foi utilizada chuva observada futura.

Foram ajustados 48 modelos e preservadas 48 referências, sem busca de hiperparâmetros. A referência reproduziu exatamente os valores anteriores. As duas famílias têm os mesmos 197.206 pares, com corte de treino anterior ao período avaliado. Contagens somadas entre prazos contêm alvos repetidos, não eventos independentes.

## Resultado

MAE agregado ponderado por contagem, em m³/s:

| Fonte | Período | Família | Geral | Vazões altas |
|---|---|---|---:|---:|
| julho | validation | level_and_slopes | 70.50 | 266.58 |
| julho | validation | levels_forecast_rain | 68.82 | 241.57 |
| julho | test | level_and_slopes | 142.36 | 396.03 |
| julho | test | levels_forecast_rain | 141.16 | 389.60 |
| carreiro | validation | level_and_slopes | 12.88 | 79.18 |
| carreiro | validation | levels_forecast_rain | 13.02 | 81.41 |
| carreiro | test | level_and_slopes | 29.49 | 77.33 |
| carreiro | test | levels_forecast_rain | 29.92 | 78.06 |

Em Julho, o erro em vazões altas caiu de 266,58 para 241,57 m³/s na validação e de 396,03 para 389,60 m³/s no teste. No prazo de 11 h, a queda foi 601,77→480,29 m³/s na validação e 687,95→669,61 m³/s no teste. Esses ganhos são de vazão, não porcentagens de acerto do nível do rio.

## Diferenças entre prazos

- julho, validation, all: MAE menor em 9/12 prazos.
- julho, validation, high_flow: MAE menor em 8/12 prazos.
- julho, test, all: MAE menor em 11/12 prazos.
- julho, test, high_flow: MAE menor em 11/12 prazos.
- carreiro, validation, all: MAE menor em 0/12 prazos.
- carreiro, validation, high_flow: MAE menor em 3/12 prazos.
- carreiro, test, all: MAE menor em 1/12 prazos.
- carreiro, test, high_flow: MAE menor em 2/12 prazos.

## Decisão e limites

Levar somente o candidato de Julho à comparação local de propagação até Muçum. A extensão de Carreiro piorou os resultados agregados e não foi selecionada. **Nenhuma promoção à rotina horária.**

Os arquivos usam `precipitation_previous_day1`: cada tempo válido está associado à antecedência nominal de 24 h. Para alvos origem+1…+12 h, isso sugere inicializações anteriores à origem, mas não há `run`, `issued_at` ou recibo histórico de publicação por registro. Vintages podem variar dentro de uma janela; não é uma rodada única. A disponibilidade histórica permanece presumida.

A previsão operacional mais recente tem distribuição de antecedências diferente deste arquivo. Antes de integrar, é preciso lidar com essa diferença e provar ganho no nível, em eventos separados e prospectivamente. Os cinco pontos não são médias espaciais completas das bacias. Os períodos avaliados já foram examinados e continuam desenvolvimento.

Os 97 testes passaram. Parâmetros, entradas e saídas permanecem preservados; a meta de 98% não foi atingida.
