# Radar comparado à persistência do nível usado na emissão

Diagnóstico congelado às 06:43:02 UTC de 22/09/2026. A referência mantém constante o campo `last_observed.value` de cada emissão. Os 12 níveis foram conferidos com observação aprovada e recibo coletado antes da emissão. Este é o último nível **usado pelo cálculo**, sem afirmar que era a observação mais recente existente na fonte. A persistência foi reconstruída agora; nunca foi emitida como previsão prospectiva.

Foram preservados 144 pontos em bandas reais de antecedência 1–12h, incluindo 54 pares com observação e 90 alvos não vencidos. Importações históricas, revisões manuais, modelos retirados e bandas fora de 1–12 não entram. `scorecard.json` separa quatro versões e cada antecedência; não há seleção de horizontes favoráveis.

Na versão atual `fd40fd74e87486e7`, há dez pares em apenas quatro horários-alvo, todos durante a mesma subida observada. Radar acerta oito dentro de 0,50 m; a referência constante, nenhum. MAE agregado descritivo: Radar 0,230 m, persistência 1,623 m. Esse agregado mistura antecedências e não é o placar exigido pela meta.

| Antecedência real mínima | Pares | Acertos Radar | Acertos persistência | MAE Radar (m) | MAE persistência (m) |
|---|---:|---:|---:|---:|---:|
| 1h | 4 | 4 | 0 | 0,179 | 1,152 |
| 2h | 3 | 2 | 0 | 0,266 | 1,627 |
| 3h | 2 | 2 | 0 | 0,091 | 2,115 |
| 4h | 1 | 0 | 0 | 0,603 | 2,510 |
| 5–12h | 0 | — | — | — | — |

Amostras pequenas, horários compartilhados e um episódio não certificam generalização ou independência. Nenhum par é elegível para a meta enquanto fuso e referência da régua estiverem pendentes. Não houve treino, inferência adicional, promoção, preenchimento de alvo nem alteração de recibos. O comparador acrescenta contexto à avaliação desta subida; não justifica trocar o modelo por persistência nem alterar parâmetros.

`manifest.json` sela as saídas originais. `supplement-manifest.json` sela este texto e a conferência independente de erros, antecedências e agregações. As previsões e fontes originais são identificadas em `sources.json`.
