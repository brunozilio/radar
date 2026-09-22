# Correção pela mediana de erros já verificáveis

**A correção não será aplicada à rotina horária.** Ela ajuda em 1 h, mas piora os prazos longos e aumenta alguns erros extremos. A meta completa de 98% não foi atingida.

Para cada horizonte, o teste subtrai do nível original a mediana dos erros de previsões originais cujos alvos já ocorreram entre origem−24 h e origem−15 min, com pelo menos seis pares finitos. O histórico começa vazio em julho; não há preenchimento ou realimentação com erros de previsões corrigidas. Janela, atraso e mínimo foram fixados antes da execução.

## Comparação

| Prazo | Recorte | Modelo | Pares | Acertos ±0,50 m | MAE | Máximo |
|---|---|---|---:|---:|---:|---:|
| 1 h | all | julho_levels | 1938 | 97.57% | 0.138 m | 1.336 m |
| 1 h | all | past_error_median | 1938 | 98.40% | 0.130 m | 1.496 m |
| 1 h | level_ge_7m | julho_levels | 235 | 91.91% | 0.209 m | 1.336 m |
| 1 h | level_ge_7m | past_error_median | 235 | 95.32% | 0.183 m | 1.496 m |
| 6 h | all | julho_levels | 1926 | 75.70% | 0.364 m | 4.191 m |
| 6 h | all | past_error_median | 1926 | 74.87% | 0.364 m | 4.245 m |
| 6 h | level_ge_7m | julho_levels | 235 | 48.94% | 0.758 m | 4.191 m |
| 6 h | level_ge_7m | past_error_median | 235 | 46.38% | 0.812 m | 4.245 m |
| 12 h | all | julho_levels | 1914 | 60.55% | 0.558 m | 9.038 m |
| 12 h | all | past_error_median | 1914 | 57.52% | 0.627 m | 10.100 m |
| 12 h | level_ge_7m | julho_levels | 235 | 30.21% | 1.375 m | 9.038 m |
| 12 h | level_ge_7m | past_error_median | 235 | 22.55% | 1.841 m | 10.100 m |

Em 1 h, o resultado geral de 98,40% é apenas histórico e o recorte de cheias fica em 95,32%. Não atende à meta que exige todos os prazos, cheias e prova prospectiva. Em 12 h nas cheias, a taxa cai de 30,21% para 22,55%, e o MAE sobe de 1,375 para 1,841 m. Não será selecionado somente o prazo favorável após examinar o resultado.

## Integridade e causalidade

Foram mantidas todas as 23.538 linhas, os valores-base e a cobertura. Houve correção em 22.979 previsões; nenhuma ficou negativa. Uma verificação independente por seleção direta de janelas reproduziu todas as correções, com diferença máxima zero, e registrou o primeiro e o último alvo usado em `calibration-window-audit.csv`. Todos os alvos utilizados têm aprovação explícita no acervo auditado.

Os 105 testes passaram, incluindo impossibilidade de dados futuros afetarem previsões anteriores, atraso de observação, ausência de realimentação e conservação de previsões ausentes. `cluster-metrics.csv` preserva as métricas de cada agrupamento, sem certificar independência.

A disponibilidade histórica após 15 minutos permanece presumida; revisões posteriores das fontes não estão reconstituídas por emissão. É uma adaptação sequencial com observações anteriores do mesmo evento, não um modelo estático avaliado sem acesso posterior a esse período. Não há evidência prospectiva nem intervalo de confiança inferido de janelas sobrepostas.
