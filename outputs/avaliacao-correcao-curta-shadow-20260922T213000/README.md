# Candidato de correção curta: somente avaliação paralela

Receita fixa registrada antes desta execução: peso 50% até 1h real, reduzindo linearmente até zero em 3h; correção máxima ±0,50m. Não houve ajuste de coeficientes, treinamento, consulta remota ou publicação. O modelo publicado foi lido exatamente de cada emissão preservada, sem refazer sua inferência.

Foram examinadas 87 emissões e 522 pares emissão/alvo de Muçum. O horário disponível ao usuário é o maior entre emissão e primeiro armazenamento; a fórmula usa a antecedência real desde a emissão. As duas medidas estão preservadas por caso.

**Este episódio já foi examinado no desenvolvimento. Não é teste independente.** Os valores antigos de D1 possuem created_at, mas não comprovam versões históricas imutáveis nem QC. A exceção legacy_unverified foi habilitada apenas neste diagnóstico. Nenhum par é elegível para provar a meta de 98%.

## Mesmos casos selecionados pela auditoria anterior

| Antecedência mínima real | Total | Pares disponíveis | MAE original → shadow (m) | ±0,50m original → shadow | Melhorou / piorou / igual |
|---|---:|---:|---:|---:|---:|
| ≥1h | 28 | 21 | 0.320 → 0.233 | 17 → 20 | 15 / 6 / 0 |
| ≥2h | 27 | 20 | 0.591 → 0.526 | 9 → 9 | 13 / 7 / 0 |
| ≥3h | 26 | 19 | 0.789 → 0.789 | 6 → 6 | 0 / 0 / 19 |
| ≥4h | 25 | 18 | 1.121 → 1.121 | 2 → 2 | 0 / 0 / 18 |
| ≥5h | 24 | 17 | 1.440 → 1.440 | 1 → 1 | 0 / 0 / 17 |
| ≥6h | 0 | 0 | — | — | — |

## Todas as emissões, por antecedência real e direção conhecida

| Intervalo real (h) | Direção | Total | Pares disponíveis | MAE original → shadow (m) | ±0,50m original → shadow |
|---|---|---:|---:|---:|---:|
| [0,1) | all | 87 | 41 | 0.136 → 0.088 | 41 → 41 |
| [0,1) | rising | 12 | 12 | 0.116 → 0.103 | 12 → 12 |
| [0,1) | falling | 28 | 27 | 0.153 → 0.084 | 27 → 27 |
| [0,1) | stable | 2 | 2 | 0.028 → 0.061 | 2 → 2 |
| [0,1) | unavailable | 45 | 0 | — | — |
| [1,2) | all | 87 | 39 | 0.328 → 0.242 | 31 → 36 |
| [1,2) | rising | 12 | 12 | 0.279 → 0.282 | 12 → 12 |
| [1,2) | falling | 28 | 25 | 0.369 → 0.223 | 17 → 22 |
| [1,2) | stable | 2 | 2 | 0.124 → 0.242 | 2 → 2 |
| [1,2) | unavailable | 45 | 0 | — | — |
| [2,3) | all | 87 | 37 | 0.620 → 0.559 | 14 → 15 |
| [2,3) | rising | 12 | 12 | 0.461 → 0.485 | 4 → 4 |
| [2,3) | falling | 28 | 23 | 0.736 → 0.619 | 8 → 9 |
| [2,3) | stable | 2 | 2 | 0.234 → 0.322 | 2 → 2 |
| [2,3) | unavailable | 45 | 0 | — | — |
| [3,4) | all | 87 | 35 | 0.839 → 0.839 | 10 → 10 |
| [3,4) | rising | 12 | 12 | 0.538 → 0.538 | 4 → 4 |
| [3,4) | falling | 28 | 21 | 1.049 → 1.049 | 4 → 4 |
| [3,4) | stable | 2 | 2 | 0.442 → 0.442 | 2 → 2 |
| [3,4) | unavailable | 45 | 0 | — | — |
| [4,5) | all | 87 | 33 | 1.181 → 1.181 | 2 → 2 |
| [4,5) | rising | 12 | 12 | 0.756 → 0.756 | 2 → 2 |
| [4,5) | falling | 28 | 19 | 1.471 → 1.471 | 0 → 0 |
| [4,5) | stable | 2 | 2 | 0.977 → 0.977 | 0 → 0 |
| [4,5) | unavailable | 45 | 0 | — | — |
| [5,6) | all | 87 | 31 | 1.521 → 1.521 | 1 → 1 |
| [5,6) | rising | 12 | 12 | 0.966 → 0.966 | 1 → 1 |
| [5,6) | falling | 28 | 17 | 1.912 → 1.912 | 0 → 0 |
| [5,6) | stable | 2 | 2 | 1.526 → 1.526 | 0 → 0 |
| [5,6) | unavailable | 45 | 0 | — | — |

## Disponibilidade e decisão

Indisponibilidade do candidato: 270/522 pares; motivo(s): {"Exact required observation timestamp is missing": 270}.
Alvos ainda sem leitura exata e candidato indisponível permanecem no denominador total e nos arquivos por caso. As métricas pareadas usam exatamente os mesmos alvos nos dois braços.

**Não promover.** Melhora agregada neste episódio não estabelece segurança nas mudanças de direção/pico. Conferir MAE, viés, erro máximo, acertos e cobertura em cada grupo dos JSONs. A partir de 3h desde a emissão, a saída permanece exatamente igual ao modelo publicado. Validar a versão congelada em cheias independentes e prospectivamente, seguindo todos os critérios de protocol.json, antes de qualquer troca.
