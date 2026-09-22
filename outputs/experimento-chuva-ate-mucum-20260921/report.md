# Efeito da chuva prevista no nível de Muçum

**O ganho de vazão não melhorou a métrica principal do nível. O candidato não foi promovido.**

A comparação troca apenas a vazão futura prevista de Julho, mantendo Carreiro e suas entradas estimadas, chuva/escoamento local HGE, pesos de propagação, curva vazão–nível, correção residual e âncora. Foram mantidas as 23.538 linhas originais e todos os valores anteriores. Os 23.103 pares válidos e as exclusões são os mesmos.

## Comparação dos níveis

Acerto = erro absoluto de no máximo 0,50 m. Todos os prazos estão em `evaluation.csv`; os exemplos abaixo não substituem a avaliação completa.

| Prazo | Recorte | Modelo | Pares | Acertos | MAE |
|---|---|---|---:|---:|---:|
| 1 h | all | julho_levels | 1938 | 1891 (97.57%) | 0.138 m |
| 1 h | all | julho_levels_rain | 1938 | 1892 (97.63%) | 0.138 m |
| 1 h | level_ge_7m | julho_levels | 235 | 216 (91.91%) | 0.209 m |
| 1 h | level_ge_7m | julho_levels_rain | 235 | 217 (92.34%) | 0.209 m |
| 6 h | all | julho_levels | 1926 | 1458 (75.70%) | 0.364 m |
| 6 h | all | julho_levels_rain | 1926 | 1458 (75.70%) | 0.363 m |
| 6 h | level_ge_7m | julho_levels | 235 | 115 (48.94%) | 0.758 m |
| 6 h | level_ge_7m | julho_levels_rain | 235 | 116 (49.36%) | 0.757 m |
| 12 h | all | julho_levels | 1914 | 1159 (60.55%) | 0.558 m |
| 12 h | all | julho_levels_rain | 1914 | 1151 (60.14%) | 0.557 m |
| 12 h | level_ge_7m | julho_levels | 235 | 71 (30.21%) | 1.375 m |
| 12 h | level_ge_7m | julho_levels_rain | 235 | 67 (28.51%) | 1.359 m |

Em 12 h nas cheias, o erro médio cai de 1,375 para 1,359 m e o máximo de 9,038 para 8,323 m. Contudo, os acertos caem de 71 para 67 entre 235 pares (30,21%→28,51%). No conjunto geral de 12 h, a taxa cai de 60,55% para 60,14%. A cobertura não mudou.

## Transições de acerto nas cheias

| Prazo | Acertos perdidos | Acertos novos | Falhas de previsão com alvo |
|---|---:|---:|---:|
| 1 h | 0 | 1 | 2 |
| 2 h | 0 | 0 | 2 |
| 3 h | 3 | 0 | 2 |
| 4 h | 0 | 0 | 2 |
| 5 h | 3 | 0 | 2 |
| 6 h | 0 | 1 | 2 |
| 7 h | 4 | 1 | 2 |
| 8 h | 2 | 1 | 2 |
| 9 h | 1 | 1 | 2 |
| 10 h | 4 | 2 | 2 |
| 11 h | 6 | 0 | 2 |
| 12 h | 6 | 2 | 2 |

## Verificação e limites

A atualização inverte a curva monotônica no nível anterior, acrescenta somente a diferença de vazão futura propagada e reaplica a mesma curva/offset. Pesos com lag mínimo de 1 h garantem que as âncoras de origem e origem−1 h não dependem dessa troca. Entram corretamente leads de Julho 0…11; não foram usadas vazões futuras observadas.

Os modelos de vazão congelados foram reproduzidos; a inversão/reconversão tem erro máximo de 7,11e-15 m. As 147 previsões com alvo ausente também foram atualizadas, sem inventar alvos. As 288 falhas de âncora permanecem. Vazão total negativa produziria falha explícita; nenhuma foi encontrada. A referência preservada reproduz suas métricas sem diferença.

A suíte passou 101 testes, incluindo equivalência com cálculo direto da curva, índices de propagação, preservação de ausências e falhas no denominador. A disponibilidade histórica das previsões meteorológicas continua presumida, e a distribuição do arquivo não equivale à previsão operacional mais recente. Não há prova prospectiva, independente ou de 98% de acertos.

## Repetição integral independente

Uma implementação separada recalculou o estado HGE, chuva futura, todas as vazões propagadas, âncora, residual e curva em seis origens, sem usar a inversão dos níveis. Foram comparados 72 níveis por família (144 comparações), todos dentro da tolerância de 1e-8 m; diferença máxima 7,11e-15 m. As origens incluem cheias e entradas estimadas do Carreiro. Os demais pontos têm a verificação algébrica e os hashes, mas não esta repetição integral. Evidências em `../verificacao-integral-chuva-mucum-20260921/verification.json`. Isso confirma a implementação, não a precisão hidrológica.
