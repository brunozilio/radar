# Adição de junho de 2024 — comparação de desenvolvimento

24 modelos candidatos foram ajustados com junho acrescido ao histórico recente; os24 controles congelados de120variáveis foram reproduzidos exatamente. Mesmos alvos, disponibilidade, cortes e parâmetros. O controle nesta tabela é experimental observado120, não a operação com180entradas. Todos os resultados são desenvolvimento conhecido; não comprovam98% nem validam eventos independentes.

## validation — nível observado ≥7m

| Horizonte nominal | Alvos / pares / falhas | Acertos controle → junho | MAE controle → junho (m) | Maior erro controle → junho (m) |
|---|---|---|---|---|
| 1h | 28 / 28 / 0 | 28 → 28 | 0.067 → 0.066 | 0.254 → 0.266 |
| 2h | 28 / 28 / 0 | 28 → 27 | 0.119 → 0.150 | 0.362 → 0.506 |
| 3h | 28 / 28 / 0 | 26 → 26 | 0.170 → 0.186 | 0.614 → 0.569 |
| 4h | 28 / 28 / 0 | 26 → 25 | 0.166 → 0.180 | 0.560 → 0.625 |
| 5h | 28 / 28 / 0 | 25 → 25 | 0.229 → 0.243 | 0.755 → 0.904 |
| 6h | 28 / 28 / 0 | 24 → 25 | 0.259 → 0.319 | 1.096 → 1.888 |
| 7h | 28 / 28 / 0 | 18 → 14 | 0.428 → 0.629 | 2.656 → 3.144 |
| 8h | 28 / 28 / 0 | 20 → 13 | 0.488 → 0.843 | 2.505 → 3.007 |
| 9h | 28 / 28 / 0 | 17 → 9 | 0.610 → 0.936 | 2.141 → 2.793 |
| 10h | 28 / 28 / 0 | 11 → 9 | 0.764 → 0.921 | 1.664 → 2.377 |
| 11h | 28 / 28 / 0 | 9 → 8 | 0.913 → 0.908 | 2.349 → 2.219 |
| 12h | 28 / 28 / 0 | 7 → 11 | 0.908 → 0.842 | 2.619 → 2.693 |

## test — nível observado ≥7m

| Horizonte nominal | Alvos / pares / falhas | Acertos controle → junho | MAE controle → junho (m) | Maior erro controle → junho (m) |
|---|---|---|---|---|
| 1h | 237 / 236 / 1 | 230 → 231 | 0.077 → 0.067 | 1.285 → 1.061 |
| 2h | 237 / 236 / 1 | 225 → 229 | 0.146 → 0.124 | 2.485 → 2.085 |
| 3h | 237 / 236 / 1 | 206 → 215 | 0.240 → 0.213 | 3.527 → 3.127 |
| 4h | 237 / 236 / 1 | 189 → 198 | 0.348 → 0.315 | 4.159 → 3.985 |
| 5h | 237 / 236 / 1 | 174 → 177 | 0.450 → 0.441 | 4.732 → 4.764 |
| 6h | 237 / 236 / 1 | 149 → 157 | 0.599 → 0.564 | 5.717 → 5.165 |
| 7h | 237 / 236 / 1 | 132 → 137 | 0.735 → 0.661 | 5.611 → 5.238 |
| 8h | 237 / 236 / 1 | 128 → 134 | 0.844 → 0.734 | 6.186 → 5.522 |
| 9h | 237 / 236 / 1 | 113 → 127 | 0.969 → 0.888 | 6.000 → 6.777 |
| 10h | 237 / 236 / 1 | 93 → 106 | 1.068 → 0.965 | 6.465 → 6.315 |
| 11h | 237 / 236 / 1 | 85 → 94 | 1.178 → 1.066 | 6.566 → 7.027 |
| 12h | 237 / 236 / 1 | 83 → 89 | 1.362 → 1.226 | 7.590 → 7.503 |

`contrasts.csv` inclui também todos os níveis e os recortes de disponibilidade. Nenhum horizonte foi escolhido para montar um modelo misto. As tolerâncias não foram ampliadas. Regime pós-avaria, referência da régua e publicação histórica de junho permanecem limitações. Falhas são mantidas no denominador observado. Nenhuma promoção operacional.
