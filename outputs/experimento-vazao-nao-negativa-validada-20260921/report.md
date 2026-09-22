# Regressão de vazões com coeficientes não negativos

Resultado: candidato não promovido. Este é o experimento numericamente validado. O primeiro resultado, em experimento-vazao-nao-negativa-20260921, foi invalidado por falha na construção da matriz e não deve ser usado para conclusões.

| Período | Família | MAE geral | MAE vazões altas | Viés vazões altas |
|---|---|---:|---:|---:|
| validation | reference_delta_full | 81.98 | 285.24 | 19.75 |
| validation | level_ridge_unconstrained | 177.48 | 395.22 | 272.98 |
| validation | level_ridge_nonnegative | 185.46 | 417.48 | 331.14 |
| test | reference_delta_full | 169.23 | 437.99 | -152.16 |
| test | level_ridge_unconstrained | 173.62 | 403.54 | -129.45 |
| test | level_ridge_nonnegative | 175.64 | 421.84 | -158.62 |

Unidades:m³/s. Agregados ponderados pelo número de pares em0–11h. Vazões altas usam o mesmo percentil95 histórico de14deJulho da referência, não a cota de cheia deMuçum. Todos os candidatos usam exatamente os mesmos alvos de avaliação.

A restrição reduz o diagnóstico atual de14deJulho em11h de19.341,99 para12.623,36m³/s. Isso não prova maior precisão. Na validação anterior, o erro de vazões altas piora de285,24 para417,48m³/s; no desenvolvimento seguinte, melhora437,99→421,84, acompanhada de piora geral169,23→175,64. O período seguinte já foi examinado, portanto não é evidência independente que possa substituir a validação anterior.

O modelo intermediário sem restrição também foi testado para separar a mudança de variáveis/objetivo da restrição de sinal. Os dois modelos de nível usam vazões defasadas em vez de diferenças, resposta absoluta e os mesmos25preditores de chuva. O intercepto permanece fixado à média ponderada do alvo, como no ajustador de referência; não foi otimizado separadamente neste protocolo.

## Verificação numérica

O primeiro otimizador declarou sucesso, mas uma conferência independente encontrou resíduo relativoKKT0,0375 em um ajuste. Valores da parte não utilizada do fator triangular entravam na matriz transposta. A implementação passou a extrair explicitamente o triângulo inferior, verificar a reconstrução da matriz original e exigir KKTrelativo<=1e-7. Um teste injeta valores espúrios no triângulo oposto para garantir que não afetem o problema.

Na repetição validada,36ajustes restritos convergiram, com resíduo relativo máximo2,94e-15. A referência reproduz a avaliação anterior; hashes e identidade dos alvos foram conferidos. Os36modelos finais e cópias de código foram preservados. A suíte local passou68testes.

As restrições tornam a resposta monotônica nas variáveis numéricas, mantendo os demais valores e indicadores de ausência fixos. Não impõem conservação de água, soma unitária dos coeficientes ou teto físico ao rio. Nenhuma previsão ativa foi modificada ou emitida por este experimento. A meta98% permanece não demonstrada.
