# Erros por tendência conhecida e episódio observado

As previsões permanecem as mesmas. A tendência usa somente níveis aprovados e exatos de origem−15min e três horas antes: subida acima de0,05m/h, descida abaixo de−0,05m/h e estabilidade entre esses limites. É variação líquida entre pontos, não monotonicidade contínua ou nova regra de alerta. Os valores futuros são usados apenas como verdade de avaliação.

## Cobertura por episódio

A política anterior de agrupamento encontrou quatro episódios com alvos horários≥7m no período de desenvolvimento. Nenhum é certificado como independente; dois têm lacunas de observação. A cheia de início de julho não tem pares calculáveis em nenhum horizonte do experimento, embora existam alvos de nível. Ela permanece visível como falha de cobertura.

| Início BRT | Pico observado(m) | Alvos12h com nível | Pares calculáveis12h | MAE12h referência→candidato(m) | Acertos±0,50m referência→candidato |
|---|---:|---:|---:|---:|---:|
| 02/07 20:30 | 8.85 | 35 | 0 | não calculável | não calculável |
| 21/07 22:00 | 19.86 | 135 | 121 | 2.253→2.163 | 7.4%→9.1% |
| 13/08 05:30 | 9.74 | 49 | 44 | 0.802→0.739 | 18.2%→27.3% |
| 31/08 05:15 | 7.54 | 18 | 18 | 0.643→0.562 | 55.6%→55.6% |

## Tendência disponível na origem, alvos≥7m

| Prazo | Tendência | Pares | MAE referência→candidato(m) | Acertos referência→candidato |
|---|---|---:|---:|---:|
| 6h | subida | 85 | 1.103→1.055 | 32.9%→28.2% |
| 6h | descida | 68 | 0.822→0.815 | 38.2%→33.8% |
| 6h | estável | 17 | 1.016→0.966 | 35.3%→35.3% |
| 6h | desconhecida | 1 | 0.770→0.899 | 0.0%→0.0% |
| 12h | subida | 95 | 1.812→1.738 | 16.8%→24.2% |
| 12h | descida | 63 | 1.403→1.343 | 15.9%→15.9% |
| 12h | estável | 24 | 2.411→2.217 | 4.2%→0.0% |
| 12h | desconhecida | 1 | 1.139→1.438 | 0.0%→0.0% |

O candidato reduzMAE12h nas três tendências conhecidas, mas não melhora a taxa de acerto em todas elas: na estabilidade fica0/24dentro de±0,50m. Em6h a redução deMAEvem acompanhada de pior taxa de acerto nas subidas e descidas. Não há fundamento para promover o candidato nem criar uma seleção oportunista de horizontes/episódios favoráveis.

## Verificação e limites

Todos os alvos finitos coincidem com a última fonte bruta consultada e têm QC explicitamente aprovado: divergências=0, sem aprovação=0. A soma das categorias reproduz contagens eMAE originais com diferença máxima6.66e-16m. Horários/unidades foram mantidos e todos os hashes conferidos.

Os agrupamentos foram definidos por observações e política preexistente, sem usar erro para escolher membros. Tendência desconhecida, lacunas, eventos sem previsões e censuras não foram excluídos. O período já foi examinado: é diagnóstico de desenvolvimento, com disponibilidade histórica presumida, não validação prospectiva. As previsões sobrepostas não representam eventos independentes nem autorizam intervalo IIDde confiança. Zero amostras foram adicionadas à meta98%. Nenhum modelo ou rotina horária foi alterado.
