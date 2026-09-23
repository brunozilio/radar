# Experimento hidrométrico de Muçum — 23/09/2026

Modelo distinto sem chuva ou previsão meteorológica. Não implementa MGB-IPH, não é balanço de massa e não mede fisicamente o tempo de percurso. Vazões de usinas em cascata são covariáveis separadas; não são somadas.

Calibração offline única. Todas as famílias, cortes, normalização e parâmetros foram fixados conforme `execution-manifest.json`; o histórico já havia sido examinado em desenvolvimento. O desempenho é retrospectivo, com disponibilidade histórica de dados não reconstruída. Nenhuma promoção pública é autorizada por esses resultados.

## Resultado do episódio de 21–23/09

| Horizonte nominal | Casos | MAE com defasagens | MAE contemporâneo | MAE persistência | MAE tendência local | Acerto ±0,50m |
|---|---:|---:|---:|---:|---:|---:|
| +1h | 46 | 0.089m | 0.085m | 0.480m | 0.162m | 95.65% |
| +2h | 45 | 0.246m | 0.226m | 0.965m | 0.394m | 88.89% |
| +3h | 44 | 0.367m | 0.351m | 1.455m | 0.678m | 79.55% |
| +4h | 43 | 0.505m | 0.483m | 1.935m | 1.020m | 67.44% |
| +5h | 42 | 0.620m | 0.607m | 2.384m | 1.379m | 64.29% |
| +6h | 41 | 0.753m | 0.817m | 2.796m | 1.772m | 60.98% |

A validação escolheu o modelo com defasagens nos seis horizontes. No teste cronológico posterior, o controle contemporâneo teve menor MAE nos seis; no episódio recente, teve menor MAE em cinco. Não houve troca de modelo após observar esses resultados. Isso não demonstra que a inclusão de defasagens melhora a previsão fora da validação.

O resultado ficou abaixo de 98% de acertos dentro de ±0,50m em todos os horizontes no episódio recente. Os casos são horas correlacionadas de um mesmo episódio, não eventos independentes. Nenhum destes números comprova desempenho operacional com chuva ausente.

## Operação experimental

- Somente `predict` com parâmetros congelados; nunca ajustar no cron.
- Todas as leituras exigidas são exatas; faltas permanecem indisponíveis.
- Referência de no máximo três horas; pontos vencidos são retirados preservando o alvo e horizonte nominal originais.
- A interface de inferência retorna `mode: shadow`, `publishable: false`.
- Intervalos inferior/superior vêm dos quantis empíricos de resíduos da validação; não possuem cobertura probabilística garantida.
- `extrapolatedFeatures` identifica valores fora dos mínimos/máximos do ajuste.
- `evaluation.json` inclui disponibilidade natural das alternativas, índices exatos de partição, correlações de todos os lags e erros em nível ≥7m.

## Arquivos congelados

`predictions.csv` foi gravado em modo exclusivo e seu SHA-256 salvo antes de calcular as métricas de teste e stress. `model.json` e `evaluation.json` também recusam substituição pela CLI. `execution-manifest.json` registra hashes de código, protocolo e dataset antes do fit.
