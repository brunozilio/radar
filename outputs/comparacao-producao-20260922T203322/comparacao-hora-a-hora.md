# Previsão × nível observado — produção

Extração: 2026-09-22T20:35:18.088000-03:00. D1 `sofik-monitoramento-push` e R2 `sofik-monitoramento-media`. Consultas somente leitura; zero linhas escritas no D1.

Cada coluna usa a última emissão da rodada de origem correspondente (H−1, H−2, … H−6), escolhida sem consultar o resultado observado. Os valores nas colunas são **previsto / erro** em metros. Erro positivo = previsão acima do real. Horários de Brasília (UTC−03). Sem interpolação ou aproximação do horário.

O observado segue a prioridade do site: SACE/SGB; ANA/SNIRH quando não há SACE no instante. Ambas as fontes permanecem no JSON. Emissão/antecedência real/objeto R2 estão registrados para cada par.

## Muçum

| Horizonte nominal | Pares | MAE (m) | Viés (m) | Maior erro absoluto (m) | Dentro de ±0,50 m |
|---|---:|---:|---:|---:|---:|
| +1h | 23 | 0.134 | +0.121 | 0.404 | 23/23 (100.0%) |
| +2h | 22 | 0.322 | +0.318 | 0.785 | 18/22 (81.8%) |
| +3h | 21 | 0.599 | +0.599 | 1.313 | 9/21 (42.9%) |
| +4h | 20 | 0.803 | +0.787 | 1.668 | 6/20 (30.0%) |
| +5h | 19 | 1.149 | +1.049 | 2.087 | 2/19 (10.5%) |
| +6h | 18 | 1.486 | +1.309 | 2.490 | 1/18 (5.6%) |

| Hora alvo | Observado | Fonte | +1h previsto / erro | +2h | +3h | +4h | +5h | +6h |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| 21/09 22:00 | 16.45 | SACE/SGB | 16.46 / +0.01 | — | — | — | — | — |
| 21/09 23:00 | 17.07 | SACE/SGB | 17.06 / -0.01 | 17.29 / +0.22 | — | — | — | — |
| 22/09 00:00 | 17.59 | SACE/SGB | 17.76 / +0.17 | 17.89 / +0.30 | 17.67 / +0.08 | — | — | — |
| 22/09 01:00 | 18.10 | SACE/SGB | 18.18 / +0.08 | 18.46 / +0.36 | 18.25 / +0.15 | 17.97 / -0.13 | — | — |
| 22/09 02:00 | 18.47 | SACE/SGB | 18.65 / +0.18 | 18.87 / +0.40 | 18.84 / +0.37 | 18.44 / -0.03 | 17.86 / -0.61 | — |
| 22/09 03:00 | 18.68 | SACE/SGB | 18.86 / +0.18 | 18.84 / +0.16 | 19.21 / +0.53 | 18.97 / +0.29 | 18.33 / -0.35 | 17.67 / -1.01 |
| 22/09 04:00 | 18.71 | SACE/SGB | 18.84 / +0.13 | 18.98 / +0.27 | 19.26 / +0.55 | 19.30 / +0.59 | 18.83 / +0.12 | 18.12 / -0.59 |
| 22/09 05:00 | 18.59 | SACE/SGB | 18.56 / -0.03 | 18.83 / +0.24 | 19.28 / +0.69 | 19.41 / +0.82 | 19.21 / +0.62 | 18.60 / +0.01 |
| 22/09 06:00 | 18.36 | SACE/SGB | 18.28 / -0.08 | 18.49 / +0.13 | 19.00 / +0.64 | 19.26 / +0.90 | 19.19 / +0.83 | 18.91 / +0.55 |
| 22/09 07:00 | 18.02 | SACE/SGB | 18.01 / -0.01 | 17.98 / -0.04 | 18.24 / +0.22 | 18.57 / +0.55 | 19.17 / +1.15 | 19.17 / +1.15 |
| 22/09 08:00 | 17.57 | SACE/SGB | 17.76 / +0.19 | 17.69 / +0.12 | 17.89 / +0.32 | 18.01 / +0.44 | 18.57 / +1.00 | 18.98 / +1.41 |
| 22/09 09:00 | 17.07 | SACE/SGB | 17.21 / +0.14 | 17.44 / +0.37 | 17.57 / +0.50 | 17.63 / +0.56 | 18.06 / +0.99 | 18.33 / +1.26 |
| 22/09 10:00 | 16.53 | SACE/SGB | 16.71 / +0.18 | 16.88 / +0.35 | 17.29 / +0.76 | 17.31 / +0.78 | 17.72 / +1.19 | 18.06 / +1.53 |
| 22/09 11:00 | 15.93 | SACE/SGB | 16.16 / +0.23 | 16.37 / +0.44 | 16.71 / +0.78 | 17.00 / +1.07 | 17.20 / +1.27 | 17.57 / +1.64 |
| 22/09 12:00 | 15.23 | SACE/SGB | 15.56 / +0.33 | 15.83 / +0.60 | 16.21 / +0.98 | 16.46 / +1.23 | 16.88 / +1.65 | 16.94 / +1.71 |
| 22/09 13:00 | 14.46 | SACE/SGB | 14.86 / +0.40 | 15.23 / +0.77 | 15.67 / +1.21 | 15.98 / +1.52 | 16.32 / +1.86 | 16.74 / +2.28 |
| 22/09 14:00 | 13.75 | SACE/SGB | 14.09 / +0.34 | 14.53 / +0.78 | 15.06 / +1.31 | 15.42 / +1.67 | 15.82 / +2.07 | 16.13 / +2.38 |
| 22/09 15:00 | 13.16 | SACE/SGB | 13.38 / +0.22 | 13.84 / +0.68 | 14.37 / +1.21 | 14.81 / +1.65 | 15.25 / +2.09 | 15.65 / +2.49 |
| 22/09 16:00 | 12.72 | SACE/SGB | 12.81 / +0.09 | 13.12 / +0.40 | 13.60 / +0.88 | 14.10 / +1.38 | 14.64 / +1.92 | 15.11 / +2.39 |
| 22/09 17:00 | 12.34 | SACE/SGB | 12.37 / +0.03 | 12.56 / +0.22 | 12.95 / +0.61 | 13.33 / +0.99 | 13.92 / +1.58 | 14.51 / +2.17 |
| 22/09 18:00 | 11.97 | SACE/SGB | 11.99 / +0.02 | 12.08 / +0.11 | 12.33 / +0.36 | 12.64 / +0.67 | 13.16 / +1.19 | 13.76 / +1.79 |
| 22/09 19:00 | 11.61 | SACE/SGB | 11.61 / -0.00 | 11.68 / +0.07 | 11.85 / +0.24 | 12.06 / +0.45 | 12.43 / +0.82 | 12.99 / +1.38 |
| 22/09 20:00 | 11.28 | ANA/SNIRH | 11.26 / -0.02 | 11.32 / +0.04 | 11.47 / +0.19 | 11.61 / +0.33 | 11.82 / +0.54 | 12.30 / +1.02 |
| 22/09 21:00 | futuro | — | 10.93 / pendente | 10.97 / pendente | 11.15 / pendente | 11.22 / pendente | 11.39 / pendente | 11.65 / pendente |
| 22/09 22:00 | futuro | — | — | 10.66 / pendente | 10.79 / pendente | 10.85 / pendente | 11.02 / pendente | 11.19 / pendente |
| 22/09 23:00 | futuro | — | — | — | 10.44 / pendente | 10.51 / pendente | 10.67 / pendente | 10.82 / pendente |
| 23/09 00:00 | futuro | — | — | — | — | 10.17 / pendente | 10.34 / pendente | 10.49 / pendente |
| 23/09 01:00 | futuro | — | — | — | — | — | 10.06 / pendente | 10.12 / pendente |
| 23/09 02:00 | futuro | — | — | — | — | — | — | 9.85 / pendente |

## Encantado

| Horizonte nominal | Pares | MAE (m) | Viés (m) | Maior erro absoluto (m) | Dentro de ±0,50 m |
|---|---:|---:|---:|---:|---:|
| +1h | 12 | 0.163 | +0.157 | 0.376 | 12/12 (100.0%) |
| +2h | 11 | 0.311 | +0.311 | 0.651 | 9/11 (81.8%) |
| +3h | 10 | 0.506 | +0.506 | 0.913 | 5/10 (50.0%) |
| +4h | 9 | 0.673 | +0.673 | 1.083 | 3/9 (33.3%) |
| +5h | 8 | 0.929 | +0.929 | 1.284 | 0/8 (0.0%) |
| +6h | 7 | 0.995 | +0.995 | 1.239 | 1/7 (14.3%) |

| Hora alvo | Observado | Fonte | +1h previsto / erro | +2h | +3h | +4h | +5h | +6h |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| 22/09 09:00 | 15.80 | SACE/SGB | 15.76 / -0.04 | — | — | — | — | — |
| 22/09 10:00 | 15.45 | SACE/SGB | 15.47 / +0.02 | 15.46 / +0.01 | — | — | — | — |
| 22/09 11:00 | 14.93 | SACE/SGB | 15.09 / +0.16 | 15.19 / +0.26 | 15.13 / +0.20 | — | — | — |
| 22/09 12:00 | 14.42 | SACE/SGB | 14.57 / +0.15 | 14.71 / +0.29 | 14.85 / +0.43 | 14.99 / +0.57 | — | — |
| 22/09 13:00 | 13.78 | SACE/SGB | 14.06 / +0.28 | 14.18 / +0.40 | 14.39 / +0.61 | 14.39 / +0.61 | 14.71 / +0.93 | — |
| 22/09 14:00 | 13.02 | SACE/SGB | 13.40 / +0.38 | 13.67 / +0.65 | 13.80 / +0.78 | 13.98 / +0.96 | 13.96 / +0.94 | 14.26 / +1.24 |
| 22/09 15:00 | 12.38 | SACE/SGB | 12.64 / +0.26 | 12.95 / +0.57 | 13.29 / +0.91 | 13.32 / +0.94 | 13.52 / +1.14 | 13.39 / +1.01 |
| 22/09 16:00 | 11.73 | SACE/SGB | 12.00 / +0.27 | 12.19 / +0.46 | 12.52 / +0.79 | 12.81 / +1.08 | 12.99 / +1.26 | 12.90 / +1.17 |
| 22/09 17:00 | 11.20 | SACE/SGB | 11.35 / +0.15 | 11.55 / +0.35 | 11.76 / +0.56 | 11.95 / +0.75 | 12.48 / +1.28 | 12.37 / +1.17 |
| 22/09 18:00 | 10.77 | SACE/SGB | 10.82 / +0.05 | 10.90 / +0.13 | 11.17 / +0.40 | 11.19 / +0.42 | 11.59 / +0.82 | 11.86 / +1.09 |
| 22/09 19:00 | 10.30 | SACE/SGB | 10.41 / +0.11 | 10.37 / +0.07 | 10.52 / +0.22 | 10.75 / +0.45 | 10.83 / +0.53 | 11.08 / +0.78 |
| 22/09 20:00 | 9.83 | SACE/SGB | 9.94 / +0.11 | 10.06 / +0.23 | 9.99 / +0.16 | 10.10 / +0.27 | 10.36 / +0.53 | 10.32 / +0.49 |
| 22/09 21:00 | futuro | — | 9.46 / pendente | 9.59 / pendente | 9.70 / pendente | 9.57 / pendente | 9.71 / pendente | 10.14 / pendente |
| 22/09 22:00 | futuro | — | — | 9.19 / pendente | 9.23 / pendente | 9.35 / pendente | 9.22 / pendente | 9.49 / pendente |
| 22/09 23:00 | futuro | — | — | — | 8.81 / pendente | 8.88 / pendente | 9.09 / pendente | 8.96 / pendente |
| 23/09 00:00 | futuro | — | — | — | — | 8.49 / pendente | 8.62 / pendente | 8.80 / pendente |
| 23/09 01:00 | futuro | — | — | — | — | — | 8.21 / pendente | 8.33 / pendente |
| 23/09 02:00 | futuro | — | — | — | — | — | — | 7.96 / pendente |

## Santa Tereza

| Horizonte nominal | Pares | MAE (m) | Viés (m) | Maior erro absoluto (m) | Dentro de ±0,50 m |
|---|---:|---:|---:|---:|---:|
| +1h | 11 | 0.216 | +0.171 | 0.558 | 10/11 (90.9%) |
| +2h | 10 | 0.399 | +0.387 | 0.972 | 6/10 (60.0%) |
| +3h | 9 | 0.615 | +0.615 | 1.399 | 4/9 (44.4%) |
| +4h | 8 | 0.720 | +0.696 | 1.565 | 4/8 (50.0%) |
| +5h | 7 | 0.784 | +0.771 | 1.622 | 3/7 (42.9%) |
| +6h | 6 | 0.797 | +0.737 | 1.506 | 2/6 (33.3%) |

| Hora alvo | Observado | Fonte | +1h previsto / erro | +2h | +3h | +4h | +5h | +6h |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| 22/09 09:00 | 14.22 | SACE/SGB | 14.42 / +0.20 | — | — | — | — | — |
| 22/09 10:00 | 13.68 | SACE/SGB | 13.94 / +0.26 | 14.16 / +0.48 | — | — | — | — |
| 22/09 11:00 | 12.94 | SACE/SGB | 13.39 / +0.45 | 13.68 / +0.74 | 13.94 / +1.00 | — | — | — |
| 22/09 12:00 | 12.18 | SACE/SGB | 12.74 / +0.56 | 13.13 / +0.95 | 13.46 / +1.28 | 13.55 / +1.37 | — | — |
| 22/09 13:00 | 11.51 | SACE/SGB | 12.00 / +0.49 | 12.48 / +0.97 | 12.91 / +1.40 | 13.08 / +1.57 | 13.13 / +1.62 | — |
| 22/09 14:00 | 11.18 | SACE/SGB | 11.28 / +0.10 | 11.76 / +0.58 | 12.26 / +1.08 | 12.52 / +1.34 | 12.65 / +1.47 | 12.69 / +1.51 |
| 22/09 15:00 | 10.99 | SACE/SGB | 10.88 / -0.11 | 11.03 / +0.04 | 11.54 / +0.55 | 11.87 / +0.88 | 12.10 / +1.11 | 12.22 / +1.23 |
| 22/09 16:00 | 10.78 | SACE/SGB | 10.75 / -0.03 | 10.72 / -0.06 | 10.82 / +0.04 | 11.19 / +0.41 | 11.46 / +0.68 | 11.66 / +0.88 |
| 22/09 17:00 | 10.49 | SACE/SGB | 10.53 / +0.04 | 10.54 / +0.05 | 10.53 / +0.04 | 10.47 / -0.02 | 10.95 / +0.46 | 11.10 / +0.61 |
| 22/09 18:00 | 10.21 | SACE/SGB | 10.25 / +0.04 | 10.29 / +0.08 | 10.30 / +0.09 | 10.30 / +0.09 | 10.17 / -0.04 | 10.58 / +0.37 |
| 22/09 19:00 | 10.02 | SACE/SGB | 9.91 / -0.11 | 10.06 / +0.04 | 10.07 / +0.05 | 9.95 / -0.07 | 10.11 / +0.09 | 9.84 / -0.18 |
| 22/09 20:00 | sem leitura exata | — | 9.74 / sem par | 9.77 / sem par | 9.86 / sem par | 9.78 / sem par | 9.66 / sem par | 9.94 / sem par |
| 22/09 21:00 | futuro | — | 9.50 / pendente | 9.52 / pendente | 9.59 / pendente | 9.61 / pendente | 9.50 / pendente | 9.32 / pendente |
| 22/09 22:00 | futuro | — | — | 9.29 / pendente | 9.29 / pendente | 9.41 / pendente | 9.42 / pendente | 9.22 / pendente |
| 22/09 23:00 | futuro | — | — | — | 9.07 / pendente | 9.01 / pendente | 9.32 / pendente | 9.27 / pendente |
| 23/09 00:00 | futuro | — | — | — | — | 8.79 / pendente | 8.86 / pendente | 9.21 / pendente |
| 23/09 01:00 | futuro | — | — | — | — | — | 8.63 / pendente | 8.76 / pendente |
| 23/09 02:00 | futuro | — | — | — | — | — | — | 8.48 / pendente |

## Rastreabilidade e limites

112 objetos R2, 1055 medições D1, 177 emissões distintas por cidade, 50 rodadas por cidade. 65 cópias repetidas removidas. 7 divergências entre ANA e SACE no mesmo instante.

- No level QC stored in D1, no independent datum certification; these are retrospective errors, not proof of the 98% goal.
- D1 retention is approximately 48 hours.
- Issues persisted in R2 prove storage, not exact browser visibility time.
- Station round samples and horizons overlap; not independent flood events.
- Nominal 1h forecasts can have under 1h actual lead because issues are recalculated within the hour.

Arquivos: `comparacao-hora-a-hora.json` contém a seleção principal; `todas-emissoes.json` preserva todas as revisões; `r2-receipts.json` identifica origem e hashes; `d1-observacoes.json` preserva o resultado e metadados remotos; `divergencias-fontes.json` compara as duas fontes observadas.
