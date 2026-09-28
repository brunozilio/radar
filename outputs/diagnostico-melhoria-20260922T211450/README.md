# Diagnóstico de melhorias: tendência de curto prazo

Comparação exploratória sobre os mesmos casos da auditoria de produção. Nenhum modelo foi treinado ou publicado. A âncora vem da própria emissão R2; a tendência usa o nível ANA exatamente uma hora antes da âncora, exigindo registro no D1 anterior à emissão. Não há ajuste de parâmetros, limites artificiais ou escolha pelo resultado.

| Antecedência mínima real | Pares | MAE atual (m) | MAE tendência linear (m) | Até ±0,50 m: atual → tendência |
|---|---:|---:|---:|---:|
| 1h | 22 | 0.322 | 0.244 | 18/22 → 21/22 |
| 2h | 21 | 0.599 | 0.486 | 9/21 → 11/21 |
| 3h | 20 | 0.803 | 0.828 | 6/20 → 5/20 |
| 4h | 19 | 1.149 | 1.245 | 2/19 → 2/19 |
| 5h | 18 | 1.486 | 1.697 | 1/18 → 1/18 |

A tendência simples melhorou as duas antecedências curtas, mas piorou de 3 a 5h. Justifica testar uma correção curta e amortecida, separada do componente hidrológico de maior prazo. Não justifica substituir automaticamente o modelo atual.

Limites: um episódio já examinado; created_at não prova inexistência de revisões posteriores; os resultados não certificam desempenho futuro ou 98%. Uma conferência independente reconstruiu os 100 casos e 15 grupos de métricas a partir do R2/D1 e reproduziu os resultados com diferença inferior a 1e-12.

Prioridades: colocar a trava de dados completos já preparada em operação; preservar observações e versões das fontes além da retenção de 48h; alinhar entradas de treino e inferência; testar correção de tendência somente no curto prazo; calibrar propagação de vazões e chuva para prazos maiores; avaliar novas versões em eventos inteiros reservados e depois em paralelo com o modelo operacional.
