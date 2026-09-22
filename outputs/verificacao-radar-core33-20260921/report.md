# RADAR: compatibilidade das 33 entradas

Comparação fatorial local: 120/33 entradas, com/sem acréscimo de setembro de 2023. Mesmas máscaras, parâmetros, pesos e 102.084 previsões. 48 novos modelos e 48 controles congelados. Nenhuma promoção operacional.

Acerto: erro absoluto ≤0,50 m; cheia: observado ≥7 m, recorte analítico. As duas fases são desenvolvimento já inspecionado; não são prova prospectiva.

| Fase | Horizonte | Família | Acertos/pares cheia | Acertos/alvos com falhas | MAE (m) | Maior erro (m) |
|---|---:|---|---:|---:|---:|---:|
| validation | 1h | observed_control | 28/28 | 28/28 | 0.0667 | 0.2537 |
| validation | 1h | augmented | 28/28 | 28/28 | 0.0759 | 0.2845 |
| validation | 1h | core_original | 28/28 | 28/28 | 0.0705 | 0.1843 |
| validation | 1h | core_augmented | 28/28 | 28/28 | 0.0602 | 0.1625 |
| validation | 6h | observed_control | 24/28 | 24/28 | 0.2587 | 1.0963 |
| validation | 6h | augmented | 18/28 | 18/28 | 0.5313 | 2.1068 |
| validation | 6h | core_original | 18/28 | 18/28 | 0.3660 | 0.8063 |
| validation | 6h | core_augmented | 20/28 | 20/28 | 0.3287 | 1.0186 |
| validation | 12h | observed_control | 7/28 | 7/28 | 0.9085 | 2.6195 |
| validation | 12h | augmented | 3/28 | 3/28 | 1.2107 | 2.9068 |
| validation | 12h | core_original | 8/28 | 8/28 | 1.0979 | 3.0612 |
| validation | 12h | core_augmented | 9/28 | 9/28 | 1.0936 | 2.6819 |
| test | 1h | observed_control | 230/236 | 230/237 | 0.0775 | 1.2848 |
| test | 1h | augmented | 229/236 | 229/237 | 0.1006 | 0.7767 |
| test | 1h | core_original | 230/236 | 230/237 | 0.0863 | 1.3129 |
| test | 1h | core_augmented | 232/236 | 232/237 | 0.0814 | 0.7725 |
| test | 6h | observed_control | 149/236 | 149/237 | 0.5993 | 5.7173 |
| test | 6h | augmented | 154/236 | 154/237 | 0.5457 | 4.5135 |
| test | 6h | core_original | 144/236 | 144/237 | 0.6349 | 5.6757 |
| test | 6h | core_augmented | 143/236 | 143/237 | 0.6168 | 5.6087 |
| test | 12h | observed_control | 83/236 | 83/237 | 1.3618 | 7.5900 |
| test | 12h | augmented | 89/236 | 89/237 | 1.2567 | 7.3628 |
| test | 12h | core_original | 83/236 | 83/237 | 1.3703 | 10.0287 |
| test | 12h | core_augmented | 79/236 | 79/237 | 1.2930 | 9.4211 |

## Efeito de acrescentar 2023 às 33 entradas

| Fase | Horizonte | Diferença acertos cheia | Diferença MAE (m) | Diferença maior erro (m) |
|---|---:|---:|---:|---:|
| validation | 1h | +0 | -0.0103 | -0.0218 |
| validation | 2h | +1 | -0.0388 | -0.2239 |
| validation | 3h | +3 | -0.0224 | -0.1006 |
| validation | 4h | +3 | -0.0287 | -0.0510 |
| validation | 5h | +1 | +0.0278 | -0.1170 |
| validation | 6h | +2 | -0.0373 | +0.2123 |
| validation | 7h | -2 | -0.0648 | -0.5941 |
| validation | 8h | +1 | -0.0355 | +0.1533 |
| validation | 9h | +0 | -0.0027 | -0.2042 |
| validation | 10h | +0 | +0.0809 | +2.1626 |
| validation | 11h | +4 | +0.0205 | -0.3317 |
| validation | 12h | +1 | -0.0043 | -0.3793 |
| test | 1h | +2 | -0.0050 | -0.5405 |
| test | 2h | +0 | -0.0165 | -0.6488 |
| test | 3h | +10 | -0.0328 | -0.4727 |
| test | 4h | +5 | -0.0366 | -0.6211 |
| test | 5h | +2 | -0.0175 | -0.5293 |
| test | 6h | -1 | -0.0182 | -0.0669 |
| test | 7h | -3 | +0.0066 | -0.0610 |
| test | 8h | -8 | +0.0201 | +0.1724 |
| test | 9h | -5 | -0.0320 | +0.3569 |
| test | 10h | +6 | -0.0523 | +0.0402 |
| test | 11h | -4 | -0.0812 | -0.7158 |
| test | 12h | -4 | -0.0773 | -0.6076 |

Todos os horizontes, populações, recortes e quatro contrastes estão em effects.csv/evaluation.csv. Não combinar horizontes com base nos resultados já vistos. A retirada de chuva não a torna fisicamente irrelevante; diferenças de modelos não identificam sozinhas uma causa hidrológica. Metadados, datum, regime das usinas e publicação histórica permanecem sem certificação. As faltas remanescentes foram preservadas.

Verificação: 48 modelos reproduzidos exatamente, 576 métricas recalculadas e 288 métricas congeladas idênticas. Contagens, pesos, parâmetros, cortes e hashes conferidos. Meta de 98% não atingida.
