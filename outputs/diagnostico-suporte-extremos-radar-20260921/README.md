# Suporte dos novos exemplos extremos nas árvores RADAR

Diagnóstico dos modelos congelados de12h. Os12 casos foram selecionados depois dos resultados por resposta observada acima do máximo original de treino(8,09m). Não é novo teste, ajuste, ablação ou prova causal.

Os sete exemplos novos de2024 acima desse máximo partem de níveis entre13.70 e15.11m. Os12 casos posteriores partem de3.21 a10.42m. As faixas não se sobrepõem: ampliar a resposta máxima de treino não garante cobrir a combinação de nível inicial e subida rápida.

| Origem | Base(m) | Resposta real(m) | Resposta prevista(m) | Árvores que compartilham folha com algum extremo2024 | Fração média do peso desses exemplos na folha |
|---|---:|---:|---:|---:|---:|
| 2026-07-21T13:00:00-03:00 | 3.59 | 8.40 | 1.6778 | 43/180 | 0.5132% |
| 2026-07-21T14:00:00-03:00 | 3.54 | 9.43 | 2.2965 | 35/180 | 0.6031% |
| 2026-07-21T15:00:00-03:00 | 3.41 | 10.36 | 3.8483 | 52/180 | 1.6310% |
| 2026-07-21T16:00:00-03:00 | 3.27 | 11.22 | 3.1319 | 46/180 | 1.0645% |
| 2026-07-21T17:00:00-03:00 | 3.21 | 11.95 | 4.4540 | 72/180 | 2.3094% |
| 2026-07-21T18:00:00-03:00 | 3.25 | 12.56 | 5.1106 | 88/180 | 3.0015% |
| 2026-07-21T19:00:00-03:00 | 3.42 | 13.08 | 5.6674 | 94/180 | 3.4256% |
| 2026-07-21T20:00:00-03:00 | 3.89 | 13.27 | 7.1269 | 104/180 | 4.0133% |
| 2026-07-21T21:00:00-03:00 | 5.02 | 12.76 | 7.1917 | 99/180 | 3.9349% |
| 2026-07-21T22:00:00-03:00 | 6.95 | 11.42 | 6.0100 | 84/180 | 3.2173% |
| 2026-07-21T23:00:00-03:00 | 8.77 | 10.02 | 5.5169 | 79/180 | 2.9484% |
| 2026-07-22T00:00:00-03:00 | 10.42 | 8.60 | 5.1794 | 81/180 | 2.8577% |

Restringindo descritivamente a base ao intervalo posterior de3.21–10.42m, há2285 pares originais e152 novos. A resposta máxima original é8.09m e a nova é8.01m: a máxima combinada permanece8.09m. Esse intervalo foi escolhido depois de examinar os casos; não é um filtro de treino ou avaliação.

## O que a inspeção comprova

A soma da resposta inicial com os180 valores de folhas reproduz a inferência de cada modelo. O roteamento manual de todas as amostras de treino reproduz exatamente as contagens de todas as folhas nas360 árvores. Nenhum modelo foi retreinado.

first-divergences.csv conta o primeiro corte que separa cada caso posterior de cada um dos sete exemplos2024, em cada árvore do candidato. Não é importância causal de variável, SHAP ou demonstração de que mudar esse campo reduziria o erro. Folhas do boosting aprendem correções residuais; a fração de exemplos extremos em uma folha não é o peso final da previsão.

Os erros continuam no conjunto. Nenhum valor de2024 foi deslocado, nenhuma variável foi modificada para forçar similaridade, e nenhum período virou holdout. A hipótese de falta de exemplos em regimes comparáveis orienta pesquisa adicional, sem resolver datum, geometria, sensores ou disponibilidade histórica.
