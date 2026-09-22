# Placar inicial da meta de 98%

Acerto = erro absoluto de até 0,50 m. **Este placar é retrospectivo; não comprova a meta prospectiva.**
Modelo atual: `arvores_previsao_chuva`; período rotulado `test` no arquivo de entrada.

| Antecedência nominal | Recorte | Pares válidos | Acertos até ±0,50 m | MAE (m) |
|---|---|---:|---:|---:|
| 1h | all | 1350 | 100.0% | 0.03 |
| 1h | level_ge_7m | 144 | 100.0% | 0.05 |
| 2h | all | 1348 | 99.6% | 0.05 |
| 2h | level_ge_7m | 143 | 99.3% | 0.09 |
| 3h | all | 1346 | 99.3% | 0.07 |
| 3h | level_ge_7m | 142 | 95.1% | 0.14 |
| 4h | all | 1345 | 98.2% | 0.09 |
| 4h | level_ge_7m | 141 | 87.2% | 0.22 |
| 5h | all | 1344 | 96.6% | 0.13 |
| 5h | level_ge_7m | 140 | 77.9% | 0.33 |
| 6h | all | 1343 | 92.1% | 0.18 |
| 6h | level_ge_7m | 140 | 72.1% | 0.42 |
| 7h | all | 1342 | 89.9% | 0.22 |
| 7h | level_ge_7m | 140 | 65.7% | 0.46 |
| 8h | all | 1341 | 86.1% | 0.28 |
| 8h | level_ge_7m | 140 | 60.0% | 0.59 |
| 9h | all | 1340 | 81.9% | 0.34 |
| 9h | level_ge_7m | 140 | 58.6% | 0.70 |
| 10h | all | 1339 | 75.6% | 0.39 |
| 10h | level_ge_7m | 140 | 42.9% | 0.83 |
| 11h | all | 1338 | 71.9% | 0.43 |
| 11h | level_ge_7m | 140 | 38.6% | 0.95 |
| 12h | all | 1337 | 69.9% | 0.45 |
| 12h | level_ge_7m | 140 | 37.1% | 1.07 |

O arquivo completo inclui os outros modelos, subida/recessão e as retrospectivas de hoje.
Não agrupar horizontes nem escolher o modelo vencedor por observação. Pares ausentes do
arquivo e fontes historicamente indisponíveis não podem ser auditados a partir deste CSV.
As previsões consecutivas não são amostras independentes.

Próximo requisito: registrar cada emissão real e confrontá-la com a medição posterior.
Não usar o bom desempenho de rio baixo para declarar sucesso em cheias.
