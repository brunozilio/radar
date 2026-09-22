# Regressão após acrescentar setembro2023 ao RADAR

Diagnóstico posterior ao ensaio, sem novas previsões ou ajustes. As faixas abaixo usam a resposta observada alvo−base apenas para explicar resultados; não são entradas disponíveis antecipadamente nem filtros de avaliação.

Os28 alvos de cheia na validation são as mesmas28 observações em todos os horizontes, de2025-11-08T08:00:00-03:00 a2025-11-09T11:00:00-03:00, sem lacunas horárias. São336 pares de previsão, não336 observações ou eventos independentes. O trecho contínuo não foi certificado como um evento independente.

| Horizonte | Viés controle(m) | Viés +2023(m) | Deslocamento médio da previsão(m) | Casos que melhoram/pioram |
|---|---:|---:|---:|---:|
| 1h | 0.0201 | 0.0482 | +0.0281 | 12/16 |
| 2h | 0.0238 | 0.0117 | -0.0121 | 13/15 |
| 3h | 0.0481 | 0.1130 | +0.0649 | 10/18 |
| 4h | 0.0018 | 0.1768 | +0.1749 | 10/18 |
| 5h | 0.0094 | 0.3074 | +0.2980 | 8/20 |
| 6h | -0.0458 | 0.4812 | +0.5270 | 5/23 |
| 7h | 0.3297 | 0.5029 | +0.1732 | 7/21 |
| 8h | 0.3492 | 0.7912 | +0.4419 | 7/21 |
| 9h | 0.4582 | 0.9590 | +0.5008 | 6/22 |
| 10h | 0.6600 | 1.0314 | +0.3715 | 2/26 |
| 11h | 0.6935 | 1.1518 | +0.4583 | 5/23 |
| 12h | 0.6377 | 1.1022 | +0.4645 | 6/22 |

## Recorte de12h por resposta observada

| Fase | Resposta alvo−base | Versão | Pares | Acertos | MAE(m) | Viés(m) |
|---|---|---|---:|---:|---:|---:|
| validation | increase_gt_0.5m | observed_control | 15 | 6 | 0.9537 | 0.7782 |
| validation | decrease_gt_0.5m | observed_control | 4 | 0 | 1.0242 | 1.0242 |
| validation | within_0.5m | observed_control | 9 | 1 | 0.7817 | 0.2316 |
| validation | increase_gt_0.5m | augmented | 15 | 2 | 1.4702 | 1.4702 |
| validation | decrease_gt_0.5m | augmented | 4 | 0 | 1.1361 | 1.1361 |
| validation | within_0.5m | augmented | 9 | 1 | 0.8115 | 0.4739 |
| test | increase_gt_0.5m | observed_control | 104 | 23 | 1.9941 | -1.6132 |
| test | decrease_gt_0.5m | observed_control | 110 | 48 | 0.8904 | 0.4091 |
| test | within_0.5m | observed_control | 22 | 12 | 0.7300 | 0.2809 |
| test | increase_gt_0.5m | augmented | 104 | 26 | 1.7869 | -1.2237 |
| test | decrease_gt_0.5m | augmented | 110 | 52 | 0.8508 | 0.4351 |
| test | within_0.5m | augmented | 22 | 11 | 0.7799 | 0.5429 |

## Interpretação e limites

Os arquivos conservam os dois períodos, todos os12h, todos os alvos observados e as falhas com base ausente. As quatro classes de resposta reconciliam contagens, acertos e soma dos erros absolutos de96 grupos originais. Linhas sem alvo permanecem no experimento original.

Viés positivo significa previsão acima da observação. Um deslocamento médio positivo junto de viés previamente positivo indica piora descritiva da sobrestimação; não demonstra sozinho causa física, efeito de um preditor específico ou validade de subtrair uma constante na operação. O período já foi examinado, e corrigir com seu erro futuro seria vazamento.

Não se inferiu significância tratando horas correlacionadas como independentes. Nenhuma tolerância foi ampliada e nenhuma amostra foi retirada. Candidato não promovido; meta98% não demonstrada.
