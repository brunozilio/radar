# Radar: treino com faltas e níveis de reservatórios

Comparação histórica de desenvolvimento. Quatro versões nas mesmas102.084 origens/horizontes: referência, treino com faltas, níveis adicionais e combinação dos dois. Controles congelados;24 modelos combinados novos. Sem busca de parâmetros, seleção de horizontes, promoção ou emissão ao vivo.

Acerto: erro absoluto ≤0,50 m. Cheia: nível observado ≥7 m, recorte analítico. Os nomes validation/test são cortes históricos já inspecionados, não validação independente.

**Resultado misto, sem promoção.** Na cheia de test, a combinação reduz o MAE em 6h, mas perde acertos em alguns horizontes. Em 12h, seu maior erro supera a referência e a versão com níveis adicionais. Também há perdas na fase validation. Não escolher versões por horizonte usando estes resultados já vistos. changes.csv preserva as diferenças contra as três versões em todos os horizontes.

| Fase | Horizonte | Versão | Acertos na cheia | MAE cheia (m) | Maior erro cheia (m) |
|---|---:|---|---:|---:|---:|
| validation | 1h | Referência | 28/28 (100.00%) | 0.0670 | 0.2244 |
| validation | 1h | Treino com faltas | 28/28 (100.00%) | 0.0670 | 0.2440 |
| validation | 1h | Níveis adicionais | 28/28 (100.00%) | 0.0679 | 0.2080 |
| validation | 1h | Combinação | 28/28 (100.00%) | 0.0718 | 0.2424 |
| validation | 6h | Referência | 24/28 (85.71%) | 0.2646 | 1.2348 |
| validation | 6h | Treino com faltas | 24/28 (85.71%) | 0.2594 | 1.3088 |
| validation | 6h | Níveis adicionais | 24/28 (85.71%) | 0.2358 | 0.9339 |
| validation | 6h | Combinação | 23/28 (82.14%) | 0.2462 | 1.2327 |
| validation | 12h | Referência | 8/28 (28.57%) | 0.7742 | 1.6670 |
| validation | 12h | Treino com faltas | 8/28 (28.57%) | 0.9251 | 2.6072 |
| validation | 12h | Níveis adicionais | 11/28 (39.29%) | 0.7229 | 1.7199 |
| validation | 12h | Combinação | 8/28 (28.57%) | 0.9060 | 2.4449 |
| test | 1h | Referência | 230/236 (97.46%) | 0.0853 | 1.3044 |
| test | 1h | Treino com faltas | 230/236 (97.46%) | 0.0775 | 1.2760 |
| test | 1h | Níveis adicionais | 230/236 (97.46%) | 0.0852 | 1.3024 |
| test | 1h | Combinação | 230/236 (97.46%) | 0.0793 | 1.2998 |
| test | 6h | Referência | 154/236 (65.25%) | 0.6237 | 5.9593 |
| test | 6h | Treino com faltas | 147/236 (62.29%) | 0.6010 | 5.6437 |
| test | 6h | Níveis adicionais | 158/236 (66.95%) | 0.6076 | 6.1150 |
| test | 6h | Combinação | 156/236 (66.10%) | 0.5760 | 5.4559 |
| test | 12h | Referência | 75/236 (31.78%) | 1.3995 | 7.1202 |
| test | 12h | Treino com faltas | 86/236 (36.44%) | 1.3408 | 7.9215 |
| test | 12h | Níveis adicionais | 84/236 (35.59%) | 1.3275 | 6.8643 |
| test | 12h | Combinação | 80/236 (33.90%) | 1.3318 | 7.6867 |

## Cobertura e limitações

Na cheia da fase test, cada horizonte tem 237 alvos observados: 236 pares avaliáveis e **uma falha de emissão por ausência do nível-base**, igual nas quatro versões. Os percentuais da tabela usam os 236 pares, não os 237 alvos. Por exemplo, em 1h, os 230 acertos representam 97,46% dos pares e 97,05% dos alvos incluindo a falha.

A revisão independente do agente recalculou diretamente as previsões e confirmou os 24 resultados de cheia da combinação (duas fases × 12 horizontes). Ela perde acertos para a versão com níveis adicionais em 7 dos 12 horizontes de test; não há dominância consistente.

Todos os modelos mantêm a mesma disponibilidade de previsão. Linhas sem alvo continuam no arquivo; somente falta do nível-base impede previsão. evaluation.csv preserva todos os12 horizontes, os recortes geral/cheia e entradas completas/com faltas, com cobertura e falhas.

O treino ampliado tem7 linhas com ausência nos níveis novos em1h e6 em6h/12h, concentradas em30/05/2025 e com alvos abaixo7m. Isso não comprova robustez a falhas durante cheias.

Os campos do vetor das21h fora das faixas de treino caem de17 para11 na fase test (18 para12 na validation). Três campos agora parecem cobertos porque entra o pico suspeito de168,74m no jusante de Julho e suas inclinações. A contagem menor não comprova melhor cobertura física; o dado foi preservado sem correção nesta rodada.

Verificação: inferência dos24 modelos reproduzida exatamente;432 linhas de métricas dos controles coincidem integralmente com as rodadas anteriores. Memberships, cortes, contagens, parâmetros e hashes conferidos. Cinco testes focados de ausência/corte/seleção temporal passaram antes da avaliação.

Os resultados não demonstram98% prospectivos. Persistem hipóteses de disponibilidade, fonte revisada, fuso/datum não certificados e diferenças entre chuva histórica e previsão ao vivo. Nenhuma alteração da automação ou do modelo operacional.
