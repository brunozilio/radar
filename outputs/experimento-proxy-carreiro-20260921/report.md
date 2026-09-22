# Experimento de entradas estimadas para o Carreiro

O teste recuperou **4.122 pares de previsões** antes inviáveis por falta de vazão do Carreiro. Os **38.256 valores de nível anteriormente calculáveis permaneceram idênticos**, com diferença máxima de 0 m. São dois modelos por par. Nenhum resultado foi promovido à rotina horária.

Foram ajustados 12 modelos auxiliares com alvos observados anteriores a 01/07/2026. Eles usam 49 variáveis de chuva e das usinas, excluindo todas as quatro variáveis de vazão do próprio Carreiro. As estimativas substituem somente entradas ausentes dentro deste cálculo e ficam identificadas; nenhuma medição ou alvo foi preenchido. Modelos principais e parâmetros HGE permaneceram congelados.

## Cobertura e precisão do conjunto completo

| Prazo | Recorte | Modelo | Pares | Cobertura | Dentro de ±0,50 m | MAE |
|---|---|---|---:|---:|---:|---:|
| 1 h | all | reference | 1938 | 99.69% | 97.73% | 0.136 m |
| 1 h | all | julho_levels | 1938 | 99.69% | 97.57% | 0.138 m |
| 1 h | level_ge_7m | reference | 235 | 99.16% | 92.77% | 0.210 m |
| 1 h | level_ge_7m | julho_levels | 235 | 99.16% | 91.91% | 0.209 m |
| 6 h | all | reference | 1926 | 99.33% | 78.61% | 0.350 m |
| 6 h | all | julho_levels | 1926 | 99.33% | 75.70% | 0.364 m |
| 6 h | level_ge_7m | reference | 235 | 99.16% | 49.79% | 0.785 m |
| 6 h | level_ge_7m | julho_levels | 235 | 99.16% | 48.94% | 0.758 m |
| 12 h | all | reference | 1914 | 99.02% | 49.90% | 0.670 m |
| 12 h | all | julho_levels | 1914 | 99.02% | 60.55% | 0.558 m |
| 12 h | level_ge_7m | reference | 235 | 99.16% | 24.26% | 1.469 m |
| 12 h | level_ge_7m | julho_levels | 235 | 99.16% | 30.21% | 1.375 m |

## Somente os pares recuperados

| Prazo | Recorte | Modelo | Pares | Dentro de ±0,50 m | MAE |
|---|---|---|---:|---:|---:|
| 1 h | all | reference | 340 | 98.82% | 0.117 m |
| 1 h | all | julho_levels | 340 | 98.82% | 0.120 m |
| 1 h | observed_ge_7m | reference | 70 | 97.14% | 0.097 m |
| 1 h | observed_ge_7m | julho_levels | 70 | 97.14% | 0.097 m |
| 6 h | all | reference | 344 | 86.63% | 0.255 m |
| 6 h | all | julho_levels | 344 | 86.05% | 0.266 m |
| 6 h | observed_ge_7m | reference | 64 | 89.06% | 0.263 m |
| 6 h | observed_ge_7m | julho_levels | 64 | 96.88% | 0.245 m |
| 12 h | all | reference | 344 | 53.20% | 0.531 m |
| 12 h | all | julho_levels | 344 | 66.86% | 0.412 m |
| 12 h | observed_ge_7m | reference | 52 | 57.69% | 0.495 m |
| 12 h | observed_ge_7m | julho_levels | 52 | 73.08% | 0.362 m |

A melhoria de cobertura muda a população avaliada. A diferença nas métricas agregadas em relação ao experimento sem estimativas não representa melhoria nas previsões antigas: elas são exatamente iguais. O erro das vazões estimadas nos intervalos sem observações não pode ser medido diretamente.

A precisão do candidato em 12 h nas cheias é de **30,21%**, apesar de cobertura de **99,16%** nesse recorte. O alvo continua sendo 98% de acertos por horizonte e nas cheias; ele não foi atingido.

## Limites e integridade

Este é um experimento histórico em períodos já examinados, com disponibilidade histórica das entradas ainda presumida. Não é evidência prospectiva, nem validação independente. Restam 147 alvos exatos ausentes e 288 âncoras ausentes, sem substituição por valores estimados.

O protocolo e código efetivamente executados estão preservados em `protocol.json` e `code/`. A redação herdada dizia indevidamente que não haveria ajuste ou preenchimento, embora os campos explícitos já especificassem os 12 modelos auxiliares e seu uso. A correção posterior de texto está registrada em `documentation-clarification.json`; ela não altera os números nem reescreve o protocolo original.

`verification.json` verifica os hashes das 22 entradas usando cópias executadas quando disponíveis, o corte temporal e a comparação completa das previsões. `population-metrics.csv` separa todas as métricas dos pares antigos e recuperados. A suíte local passou 89 testes antes desta consolidação documental.
