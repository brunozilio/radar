# RADAR: comparação dos blocos de chuva e níveis auxiliares

Comparação fatorial local: presença/ausência dos blocos de chuva e níveis auxiliares, com/sem acréscimo de setembro de 2023. São oito famílias com 120, 108, 45 ou 33 entradas. Mesmas máscaras, parâmetros, pesos e 102.084 previsões; 96 novos modelos e 96 controles congelados. Nenhuma promoção operacional.

Acerto: erro absoluto ≤0,50 m; cheia: observado ≥7 m, recorte analítico. As duas fases são desenvolvimento já inspecionado; não são prova prospectiva.

| Fase | Horizonte | Família | Acertos/pares cheia | Acertos/alvos com falhas | MAE (m) | Maior erro (m) |
|---|---:|---|---:|---:|---:|---:|
| validation | 1h | observed_control | 28/28 | 28/28 | 0.0667 | 0.2537 |
| validation | 1h | augmented | 28/28 | 28/28 | 0.0759 | 0.2845 |
| validation | 1h | core_original | 28/28 | 28/28 | 0.0705 | 0.1843 |
| validation | 1h | core_augmented | 28/28 | 28/28 | 0.0602 | 0.1625 |
| validation | 1h | levels45_original | 28/28 | 28/28 | 0.0643 | 0.2149 |
| validation | 1h | levels45_augmented | 28/28 | 28/28 | 0.0577 | 0.2062 |
| validation | 1h | rain108_original | 28/28 | 28/28 | 0.0711 | 0.1870 |
| validation | 1h | rain108_augmented | 28/28 | 28/28 | 0.0713 | 0.2333 |
| validation | 6h | observed_control | 24/28 | 24/28 | 0.2587 | 1.0963 |
| validation | 6h | augmented | 18/28 | 18/28 | 0.5313 | 2.1068 |
| validation | 6h | core_original | 18/28 | 18/28 | 0.3660 | 0.8063 |
| validation | 6h | core_augmented | 20/28 | 20/28 | 0.3287 | 1.0186 |
| validation | 6h | levels45_original | 25/28 | 25/28 | 0.2612 | 1.0616 |
| validation | 6h | levels45_augmented | 27/28 | 27/28 | 0.2738 | 1.4183 |
| validation | 6h | rain108_original | 20/28 | 20/28 | 0.3455 | 1.2312 |
| validation | 6h | rain108_augmented | 17/28 | 17/28 | 0.5194 | 1.6895 |
| validation | 12h | observed_control | 7/28 | 7/28 | 0.9085 | 2.6195 |
| validation | 12h | augmented | 3/28 | 3/28 | 1.2107 | 2.9068 |
| validation | 12h | core_original | 8/28 | 8/28 | 1.0979 | 3.0612 |
| validation | 12h | core_augmented | 9/28 | 9/28 | 1.0936 | 2.6819 |
| validation | 12h | levels45_original | 3/28 | 3/28 | 1.1743 | 2.2577 |
| validation | 12h | levels45_augmented | 2/28 | 2/28 | 1.2433 | 2.0138 |
| validation | 12h | rain108_original | 8/28 | 8/28 | 0.8103 | 2.3722 |
| validation | 12h | rain108_augmented | 4/28 | 4/28 | 1.1071 | 2.7360 |
| test | 1h | observed_control | 230/236 | 230/237 | 0.0775 | 1.2848 |
| test | 1h | augmented | 229/236 | 229/237 | 0.1006 | 0.7767 |
| test | 1h | core_original | 230/236 | 230/237 | 0.0863 | 1.3129 |
| test | 1h | core_augmented | 232/236 | 232/237 | 0.0814 | 0.7725 |
| test | 1h | levels45_original | 230/236 | 230/237 | 0.0781 | 1.3521 |
| test | 1h | levels45_augmented | 233/236 | 233/237 | 0.0769 | 0.6959 |
| test | 1h | rain108_original | 230/236 | 230/237 | 0.0845 | 1.2710 |
| test | 1h | rain108_augmented | 231/236 | 231/237 | 0.0925 | 0.8388 |
| test | 6h | observed_control | 149/236 | 149/237 | 0.5993 | 5.7173 |
| test | 6h | augmented | 154/236 | 154/237 | 0.5457 | 4.5135 |
| test | 6h | core_original | 144/236 | 144/237 | 0.6349 | 5.6757 |
| test | 6h | core_augmented | 143/236 | 143/237 | 0.6168 | 5.6087 |
| test | 6h | levels45_original | 151/236 | 151/237 | 0.6374 | 6.1690 |
| test | 6h | levels45_augmented | 151/236 | 151/237 | 0.6052 | 5.5016 |
| test | 6h | rain108_original | 134/236 | 134/237 | 0.6448 | 5.5447 |
| test | 6h | rain108_augmented | 142/236 | 142/237 | 0.6028 | 4.9849 |
| test | 12h | observed_control | 83/236 | 83/237 | 1.3618 | 7.5900 |
| test | 12h | augmented | 89/236 | 89/237 | 1.2567 | 7.3628 |
| test | 12h | core_original | 83/236 | 83/237 | 1.3703 | 10.0287 |
| test | 12h | core_augmented | 79/236 | 79/237 | 1.2930 | 9.4211 |
| test | 12h | levels45_original | 75/236 | 75/237 | 1.4276 | 10.2112 |
| test | 12h | levels45_augmented | 78/236 | 78/237 | 1.3700 | 9.3472 |
| test | 12h | rain108_original | 78/236 | 78/237 | 1.3578 | 7.5134 |
| test | 12h | rain108_augmented | 81/236 | 81/237 | 1.2383 | 7.4620 |

## Efeito de acrescentar 2023 aos dois novos conjuntos de entradas

| Fase | Horizonte | Entradas | Diferença acertos cheia | Diferença MAE (m) | Diferença maior erro (m) |
|---|---:|---|---:|---:|---:|
| validation | 1h | levels45_original | +0 | -0.0066 | -0.0088 |
| validation | 1h | rain108_original | +0 | +0.0002 | +0.0463 |
| validation | 1h | rain108_original | +0 | -0.0044 | +0.0667 |
| validation | 1h | levels45_original | +0 | +0.0024 | +0.0387 |
| validation | 2h | levels45_original | +0 | -0.0118 | -0.1235 |
| validation | 2h | rain108_original | +0 | -0.0117 | -0.0262 |
| validation | 2h | rain108_original | +0 | -0.0254 | -0.0169 |
| validation | 2h | levels45_original | +0 | -0.0034 | -0.0111 |
| validation | 3h | levels45_original | +0 | +0.0435 | +0.0312 |
| validation | 3h | rain108_original | +4 | -0.0528 | -0.2167 |
| validation | 3h | rain108_original | +2 | -0.0711 | -0.0229 |
| validation | 3h | levels45_original | -2 | +0.0397 | +0.1785 |
| validation | 4h | levels45_original | -1 | +0.0622 | +0.0353 |
| validation | 4h | rain108_original | +0 | +0.0193 | +0.1167 |
| validation | 4h | rain108_original | +1 | -0.1070 | -0.4416 |
| validation | 4h | levels45_original | -1 | +0.0340 | +0.0413 |
| validation | 5h | levels45_original | +0 | +0.0344 | +0.1259 |
| validation | 5h | rain108_original | +0 | +0.0636 | +0.0016 |
| validation | 5h | rain108_original | +5 | -0.1095 | -0.2487 |
| validation | 5h | levels45_original | +1 | -0.0067 | +0.1605 |
| validation | 6h | levels45_original | +2 | +0.0126 | +0.3567 |
| validation | 6h | rain108_original | -3 | +0.1739 | +0.4583 |
| validation | 6h | rain108_original | +4 | -0.0868 | -0.1349 |
| validation | 6h | levels45_original | -1 | -0.0025 | +0.0347 |
| validation | 7h | levels45_original | +2 | -0.0551 | -1.0731 |
| validation | 7h | rain108_original | +1 | +0.1038 | +1.0525 |
| validation | 7h | rain108_original | -1 | +0.0586 | +0.3369 |
| validation | 7h | levels45_original | +0 | -0.0241 | +0.1934 |
| validation | 8h | levels45_original | +3 | -0.1380 | -1.0429 |
| validation | 8h | rain108_original | -6 | +0.2336 | +1.0050 |
| validation | 8h | rain108_original | +1 | -0.0367 | +0.2968 |
| validation | 8h | levels45_original | +8 | -0.1772 | -0.6014 |
| validation | 9h | levels45_original | +5 | -0.1465 | -0.7994 |
| validation | 9h | rain108_original | -7 | +0.4466 | +1.4097 |
| validation | 9h | rain108_original | +1 | +0.0371 | +0.6367 |
| validation | 9h | levels45_original | +8 | -0.0779 | -0.4223 |
| validation | 10h | levels45_original | +3 | -0.1358 | -0.7282 |
| validation | 10h | rain108_original | -5 | +0.5033 | +1.7127 |
| validation | 10h | rain108_original | -4 | +0.1813 | +0.3067 |
| validation | 10h | levels45_original | +5 | -0.0582 | -0.3952 |
| validation | 11h | levels45_original | +0 | -0.1194 | -0.0572 |
| validation | 11h | rain108_original | -7 | +0.4935 | +1.2188 |
| validation | 11h | rain108_original | -3 | +0.2155 | +0.3337 |
| validation | 11h | levels45_original | +4 | -0.1491 | +0.1270 |
| validation | 12h | levels45_original | -1 | +0.0690 | -0.2438 |
| validation | 12h | rain108_original | -4 | +0.2968 | +0.3638 |
| validation | 12h | rain108_original | -1 | +0.0982 | +0.2472 |
| validation | 12h | levels45_original | +4 | -0.2658 | +0.3618 |
| test | 1h | levels45_original | +3 | -0.0013 | -0.6562 |
| test | 1h | rain108_original | +1 | +0.0080 | -0.4322 |
| test | 1h | rain108_original | +0 | -0.0070 | +0.0138 |
| test | 1h | levels45_original | +0 | -0.0007 | -0.0673 |
| test | 2h | levels45_original | -6 | -0.0024 | -0.9084 |
| test | 2h | rain108_original | -7 | +0.0340 | -1.0251 |
| test | 2h | rain108_original | +10 | -0.0258 | +0.2714 |
| test | 2h | levels45_original | -2 | -0.0016 | +0.0119 |
| test | 3h | levels45_original | -3 | -0.0125 | -0.3525 |
| test | 3h | rain108_original | +4 | -0.0136 | -0.3245 |
| test | 3h | rain108_original | +9 | -0.0441 | +0.1329 |
| test | 3h | levels45_original | -8 | +0.0032 | -0.1002 |
| test | 4h | levels45_original | -1 | -0.0111 | -0.3483 |
| test | 4h | rain108_original | +6 | -0.0321 | -0.7042 |
| test | 4h | rain108_original | +8 | -0.0522 | -0.0638 |
| test | 4h | levels45_original | -6 | -0.0062 | -0.2741 |
| test | 5h | levels45_original | -4 | -0.0239 | -0.7877 |
| test | 5h | rain108_original | +0 | -0.0334 | -0.8871 |
| test | 5h | rain108_original | +16 | -0.0643 | -0.1187 |
| test | 5h | levels45_original | +1 | -0.0486 | -0.9914 |
| test | 6h | levels45_original | +0 | -0.0322 | -0.6674 |
| test | 6h | rain108_original | +8 | -0.0420 | -0.5598 |
| test | 6h | rain108_original | +15 | -0.0456 | +0.1726 |
| test | 6h | levels45_original | -2 | -0.0381 | -0.4517 |
| test | 7h | levels45_original | +4 | -0.0148 | -0.8605 |
| test | 7h | rain108_original | -9 | -0.0153 | -1.2479 |
| test | 7h | rain108_original | -3 | -0.0142 | +0.4263 |
| test | 7h | levels45_original | +0 | +0.0213 | -0.8740 |
| test | 8h | levels45_original | -2 | -0.0240 | -0.5008 |
| test | 8h | rain108_original | +6 | -0.0684 | -1.7072 |
| test | 8h | rain108_original | +4 | +0.0212 | +0.5572 |
| test | 8h | levels45_original | +3 | +0.0270 | -1.2744 |
| test | 9h | levels45_original | -9 | -0.0510 | -0.3049 |
| test | 9h | rain108_original | +10 | -0.0935 | -1.3774 |
| test | 9h | rain108_original | +6 | -0.0169 | +0.0133 |
| test | 9h | levels45_original | -6 | +0.0135 | -2.3315 |
| test | 10h | levels45_original | -12 | -0.1348 | -0.3363 |
| test | 10h | rain108_original | +6 | -0.1174 | -1.4202 |
| test | 10h | rain108_original | -2 | -0.0186 | +0.0205 |
| test | 10h | levels45_original | -9 | -0.0930 | -2.5164 |
| test | 11h | levels45_original | -6 | -0.0471 | -0.5783 |
| test | 11h | rain108_original | +6 | -0.0917 | -0.6914 |
| test | 11h | rain108_original | +5 | -0.0069 | -0.0615 |
| test | 11h | levels45_original | -6 | -0.0857 | -3.2008 |
| test | 12h | levels45_original | +3 | -0.0576 | -0.8640 |
| test | 12h | rain108_original | +3 | -0.1195 | -0.0514 |
| test | 12h | rain108_original | +5 | +0.0040 | +0.0766 |
| test | 12h | levels45_original | +8 | -0.0658 | -2.6212 |

Todos os horizontes, populações, recortes e os 12 contrastes das arestas do experimento estão em effects.csv/evaluation.csv. Não combinar horizontes com base nos resultados já vistos. A retirada de chuva não a torna fisicamente irrelevante; diferenças de modelos não identificam sozinhas uma causa hidrológica. Metadados, datum, regime das usinas e publicação histórica permanecem sem certificação. As faltas remanescentes foram preservadas.

Verificação: 96 modelos reproduzidos exatamente, 1152 métricas recalculadas e 576 métricas congeladas idênticas. Contagens, pesos, parâmetros, cortes e hashes conferidos. Meta de 98% não atingida.
