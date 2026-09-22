# RADAR: ensaio com120campos observados

Comparação histórica de desenvolvimento, com as mesmas102.084 linhas e os mesmos parâmetros. Somente os60campos de previsão meteorológica foram retirados; chuva futura não foi imposta igual azero. Não entraram dados novos de2023/2024. Não houve promoção.

| Fase | Horizonte | Versão | Acertos/pares cheia | Acertos/alvos com falhas | MAE(m) | Máximo(m) |
|---|---:|---|---:|---:|---:|---:|
| validation | 1h | native_control | 28/28 | 28/28 | 0.0670 | 0.2440 |
| validation | 1h | observed_only | 28/28 | 28/28 | 0.0667 | 0.2537 |
| validation | 2h | native_control | 28/28 | 28/28 | 0.1224 | 0.3702 |
| validation | 2h | observed_only | 28/28 | 28/28 | 0.1190 | 0.3619 |
| validation | 3h | native_control | 26/28 | 26/28 | 0.1734 | 0.6383 |
| validation | 3h | observed_only | 26/28 | 26/28 | 0.1696 | 0.6141 |
| validation | 4h | native_control | 26/28 | 26/28 | 0.1844 | 0.6156 |
| validation | 4h | observed_only | 26/28 | 26/28 | 0.1665 | 0.5602 |
| validation | 5h | native_control | 25/28 | 25/28 | 0.2029 | 0.6008 |
| validation | 5h | observed_only | 25/28 | 25/28 | 0.2291 | 0.7553 |
| validation | 6h | native_control | 24/28 | 24/28 | 0.2594 | 1.3088 |
| validation | 6h | observed_only | 24/28 | 24/28 | 0.2587 | 1.0963 |
| validation | 7h | native_control | 17/28 | 17/28 | 0.4222 | 2.5233 |
| validation | 7h | observed_only | 18/28 | 18/28 | 0.4275 | 2.6557 |
| validation | 8h | native_control | 19/28 | 19/28 | 0.5140 | 2.4056 |
| validation | 8h | observed_only | 20/28 | 20/28 | 0.4882 | 2.5050 |
| validation | 9h | native_control | 17/28 | 17/28 | 0.5657 | 1.9117 |
| validation | 9h | observed_only | 17/28 | 17/28 | 0.6096 | 2.1405 |
| validation | 10h | native_control | 10/28 | 10/28 | 0.7573 | 1.6619 |
| validation | 10h | observed_only | 11/28 | 11/28 | 0.7638 | 1.6643 |
| validation | 11h | native_control | 8/28 | 8/28 | 0.9169 | 2.3537 |
| validation | 11h | observed_only | 9/28 | 9/28 | 0.9132 | 2.3489 |
| validation | 12h | native_control | 8/28 | 8/28 | 0.9251 | 2.6072 |
| validation | 12h | observed_only | 7/28 | 7/28 | 0.9085 | 2.6195 |
| test | 1h | native_control | 230/236 | 230/237 | 0.0775 | 1.2760 |
| test | 1h | observed_only | 230/236 | 230/237 | 0.0775 | 1.2848 |
| test | 2h | native_control | 225/236 | 225/237 | 0.1430 | 2.4621 |
| test | 2h | observed_only | 225/236 | 225/237 | 0.1457 | 2.4854 |
| test | 3h | native_control | 206/236 | 206/237 | 0.2442 | 3.5396 |
| test | 3h | observed_only | 206/236 | 206/237 | 0.2398 | 3.5269 |
| test | 4h | native_control | 192/236 | 192/237 | 0.3488 | 4.1284 |
| test | 4h | observed_only | 189/236 | 189/237 | 0.3477 | 4.1593 |
| test | 5h | native_control | 170/236 | 170/237 | 0.4590 | 4.8643 |
| test | 5h | observed_only | 174/236 | 174/237 | 0.4495 | 4.7320 |
| test | 6h | native_control | 147/236 | 147/237 | 0.6010 | 5.6437 |
| test | 6h | observed_only | 149/236 | 149/237 | 0.5993 | 5.7173 |
| test | 7h | native_control | 134/236 | 134/237 | 0.7132 | 5.3081 |
| test | 7h | observed_only | 132/236 | 132/237 | 0.7350 | 5.6114 |
| test | 8h | native_control | 131/236 | 131/237 | 0.8055 | 6.0015 |
| test | 8h | observed_only | 128/236 | 128/237 | 0.8438 | 6.1859 |
| test | 9h | native_control | 113/236 | 113/237 | 0.9363 | 5.9436 |
| test | 9h | observed_only | 113/236 | 113/237 | 0.9693 | 6.0004 |
| test | 10h | native_control | 95/236 | 95/237 | 1.0727 | 6.4314 |
| test | 10h | observed_only | 93/236 | 93/237 | 1.0678 | 6.4645 |
| test | 11h | native_control | 84/236 | 84/237 | 1.2106 | 6.8829 |
| test | 11h | observed_only | 85/236 | 85/237 | 1.1783 | 6.5664 |
| test | 12h | native_control | 86/236 | 86/237 | 1.3408 | 7.9215 |
| test | 12h | observed_only | 83/236 | 83/237 | 1.3618 | 7.5900 |

Acerto significa erro≤0,50m; cheia é recorte analítico observado≥7m. evaluation.csv inclui todos os horizontes e recortes, indisponibilidade e falhas. changes.csv preserva ganhos e regressões.

Os24modelos foram recarregados e suas previsões reproduzidas exatamente. Máscaras, cortes, parâmetros, contagens por árvore,288linhas de métricas e144linhas do controle foram conferidos.

Este ensaio estabelece um controle de120campos para eventual acréscimo de histórico sem NWP. Os parâmetros foram escolhidos anteriormente para180campos e não foram otimizados de novo. Todas as fases jáforam examinadas; não constituem validação independente nem prova de98% prospectivos. Permanecem pendências de metadados, publicação e comparabilidade física.
