# Representação numérica fixa: comparação pareada

Regra registrada antes do ajuste: arredondar somente colunas de chuva/cobertura para oito casas. Cada família é comparada à mesma composição de treinamento. Todos os horizontes e populações estão no CSV. A tabela abaixo ilustra o recorte observado >=7 m; falhas permanecem no denominador. Os períodos já foram examinados: estes resultados não são um novo teste independente.

| Período | Família | h | Acertos antes → depois | MAE antes → depois | Máximo antes → depois |
|---|---|---:|---:|---:|---:|
| validation | original | 1 | 28 → 28 / 28 | 0.066681 → 0.066681 | 0.253657 → 0.253657 |
| validation | plus2020 | 1 | 28 → 28 / 28 | 0.063333 → 0.063333 | 0.249438 → 0.249438 |
| validation | original | 6 | 24 → 23 / 28 | 0.258712 → 0.254299 | 1.096290 → 1.086237 |
| validation | plus2020 | 6 | 21 → 21 / 28 | 0.355074 → 0.303787 | 1.386024 → 1.262299 |
| validation | original | 12 | 7 → 7 / 28 | 0.908493 → 0.913008 | 2.619470 → 2.627739 |
| validation | plus2020 | 12 | 7 → 8 / 28 | 0.892804 → 0.881569 | 2.626978 → 2.618127 |
| test | original | 1 | 230 → 230 / 237 | 0.077472 → 0.077472 | 1.284834 → 1.284834 |
| test | plus2020 | 1 | 231 → 231 / 237 | 0.064764 → 0.064764 | 0.937513 → 0.937513 |
| test | original | 6 | 149 → 148 / 237 | 0.599275 → 0.597610 | 5.717301 → 5.758939 |
| test | plus2020 | 6 | 163 → 162 / 237 | 0.536116 → 0.536904 | 4.704522 → 4.704893 |
| test | original | 12 | 83 → 82 / 237 | 1.361813 → 1.358788 | 7.589997 → 7.547984 |
| test | plus2020 | 12 | 87 → 89 / 237 | 1.230338 → 1.221200 | 7.974639 → 8.067397 |
| 2021 | original | 1 | 11 → 11 / 11 | 0.049012 → 0.049012 | 0.136993 → 0.136993 |
| 2021 | plus2020 | 1 | 11 → 11 / 11 | 0.060751 → 0.060751 | 0.143373 → 0.143373 |
| 2021 | original | 6 | 8 → 8 / 11 | 0.347436 → 0.310884 | 0.755541 → 0.714895 |
| 2021 | plus2020 | 6 | 9 → 9 / 11 | 0.234912 → 0.248002 | 0.627428 → 0.621092 |
| 2021 | original | 12 | 6 → 6 / 11 | 0.461953 → 0.441928 | 0.745555 → 0.741458 |
| 2021 | plus2020 | 12 | 10 → 11 / 11 | 0.264860 → 0.167414 | 0.615673 → 0.462490 |
| 2022 | original | 1 | 307 → 307 / 312 | 0.073907 → 0.073907 | 1.108535 → 1.108535 |
| 2022 | plus2020 | 1 | 310 → 310 / 312 | 0.065192 → 0.065192 | 0.982939 → 0.982939 |
| 2022 | original | 6 | 194 → 194 / 312 | 0.640565 → 0.643441 | 3.742340 → 3.719969 |
| 2022 | plus2020 | 6 | 218 → 217 / 312 | 0.471371 → 0.453714 | 2.972566 → 2.700152 |
| 2022 | original | 12 | 147 → 144 / 312 | 1.027166 → 1.031072 | 5.816917 → 5.790282 |
| 2022 | plus2020 | 12 | 120 → 113 / 312 | 1.063000 → 1.061850 | 4.877715 → 4.744236 |
| pooled | original | 1 | 318 → 318 / 323 | 0.073057 → 0.073057 | 1.108535 → 1.108535 |
| pooled | plus2020 | 1 | 321 → 321 / 323 | 0.065041 → 0.065041 | 0.982939 → 0.982939 |
| pooled | original | 6 | 202 → 202 / 323 | 0.630552 → 0.632080 | 3.742340 → 3.719969 |
| pooled | plus2020 | 6 | 227 → 226 / 323 | 0.463294 → 0.446687 | 2.972566 → 2.700152 |
| pooled | original | 12 | 153 → 150 / 323 | 1.007857 → 1.010946 | 5.816917 → 5.790282 |
| pooled | plus2020 | 12 | 130 → 124 / 323 | 1.035734 → 1.031294 | 4.877715 → 4.744236 |

Igualdade numérica entre reconstruções não prova precisão hidrológica. Nenhuma promoção operacional. Meta de 98% não demonstrada.
