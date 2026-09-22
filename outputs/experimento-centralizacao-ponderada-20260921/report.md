# Centralização ponderada no ajuste de vazões

Decisão: candidato não promovido. Ajustar corretamente o intercepto junto dos coeficientes eliminou o resíduo médio ponderado do treinamento, mas não trouxe ganho consistente que justifique mudar o modelo em acompanhamento.

| Fonte | Família | Validação geral | Validação vazões altas | Desenvolvimento geral | Desenvolvimento vazões altas | Diagnóstico atual11h |
|---|---|---:|---:|---:|---:|---:|
| julho | reference_delta | 81.982 | 285.241 | 169.235 | 437.989 | 19341.99 |
| julho | weighted_delta | 81.374 | 285.314 | 169.300 | 438.422 | 19349.35 |
| julho | reference_absolute | 176.233 | 388.020 | 173.900 | 432.126 | 19091.76 |
| julho | weighted_absolute | 75.143 | 329.172 | 161.293 | 433.562 | 19189.78 |
| carreiro | reference_delta | 13.526 | 77.686 | 29.679 | 78.206 | 1781.21 |
| carreiro | weighted_delta | 13.526 | 77.686 | 29.679 | 78.206 | 1781.21 |
| carreiro | reference_absolute | 14.930 | 79.367 | 59.450 | 137.636 | 1990.38 |
| carreiro | weighted_absolute | 14.930 | 79.367 | 59.450 | 137.636 | 1990.38 |

Erros e vazões em m³/s. MAE ponderado pelo número de pares, nos prazos0–11h. Mantidos limiares de vazão alta por fonte, todos os alvos e os mesmos53preditores. O diagnóstico atual usa o snapshot18h e histórico congelado das15h; não reproduz necessariamente o ajuste horário ativo.

## O que foi isolado

O ajuste anterior padronizava as entradas pela média não ponderada e fixava o intercepto na média ponderada do alvo. Quando pesos e entradas estão associados, isso não equivale ao ótimo conjunto de coeficientes e intercepto livre. O candidato usa a média ponderada das entradas, mantendo medianas, desvios-padrão, penalidade1000 e pesos originais. Essa mudança foi testada separadamente para resposta de variação e resposta de vazão absoluta.

O candidato foi conferido contra uma formulação independente de mínimos quadrados aumentados, com intercepto sem penalidade, além das equações normais e do resíduo médio ponderado. Pesos uniformes reproduzem a referência; Carreiro não teve diferença relevante pois os pesos desse treino são uniformes. A suíte local passou71testes.

Em14deJulho, o resíduo médio ponderado máximo no treinamento da referência de variação era17,70m³/s; o candidato o removeu numericamente. Na versão de resposta absoluta, o valor era148,83m³/s. Isso não garante menor erro fora do ajuste: a validação de vazões altas do modelo de variação praticamente não mudou e o desenvolvimento piorou ligeiramente. A variante absoluta ponderada melhorou sua própria referência, mas ficou pior que o modelo de variação nas vazões altas da validação.

A comparação conservou96modelos finais, código, hashes, resíduos de treino e previsões pareadas. Os períodos já foram examinados em desenvolvimento e não representam validação independente nova. Nenhuma emissão foi substituída. A discrepância de centralização não explica a extrapolação atual, e a meta98% permanece não demonstrada.
