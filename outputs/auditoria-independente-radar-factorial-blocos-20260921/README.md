# Auditoria independente: oito famílias Radar

458 verificações passaram. As192 métricas de cheia/full_schedule foram recalculadas diretamente das previsões, com tolerância1e-12. As102.084 chaves/bases/alvos e quatro controles são exatos; disponibilidade idêntica nas oito famílias;36máscaras e96memberships/pesos conferem.

Cada horizonte/família preserva28alvos/28pares de validação e237alvos/236pares/1falha de teste. Sucesso sobre alvos usa237 e mantém a falha; MAE usa236 pares finitos.

Foram calculados12contrastes: adição2023 em cada um dos quatro conjuntos de entradas; adição da chuva com/sem auxiliares, em cada conjunto de anos; adição dos auxiliares com/sem chuva, em cada conjunto de anos. Valores positivos de Δacertos são ganhos; valores negativos de ΔMAE/máximo são reduções de erro.

## Efeitos por horizonte

| Fase/contraste | Ganho de acertos | Perda de acertos | MAE melhora | MAE piora |
|---|---|---|---|---|
| validation:year120 | [] | [3, 6, 7, 8, 9, 10, 11, 12] | [] | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] |
| validation:year33 | [2, 3, 4, 5, 6, 8, 11, 12] | [7] | [1, 2, 3, 4, 6, 7, 8, 9, 12] | [5, 10, 11] |
| validation:year45 | [6, 7, 8, 9, 10] | [4, 12] | [1, 2, 7, 8, 9, 10, 11] | [3, 4, 5, 6, 12] |
| validation:year108 | [3, 7] | [6, 8, 9, 10, 11, 12] | [2, 3] | [1, 4, 5, 6, 7, 8, 9, 10, 11, 12] |
| validation:rain_with_aux_original | [5, 8, 9, 10, 11, 12] | [3, 4, 6] | [2, 5, 6, 7, 8, 9, 10, 11, 12] | [1, 3, 4] |
| validation:rain_with_aux_augmented | [5, 12] | [3, 6, 7, 8, 9, 10] | [12] | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11] |
| validation:rain_without_aux_original | [2, 4, 6, 7, 8, 9, 10, 11] | [5] | [2, 4, 6, 7, 8, 9, 10, 11, 12] | [1, 3, 5] |
| validation:rain_without_aux_augmented | [3, 7, 8, 9, 10] | [5, 6, 11, 12] | [3, 7] | [1, 2, 4, 5, 6, 8, 9, 10, 11, 12] |
| validation:aux_with_rain_original | [3, 4, 5, 6, 8, 9] | [7, 10, 11, 12] | [1, 2, 3, 4, 5, 6, 8] | [7, 9, 10, 11, 12] |
| validation:aux_with_rain_augmented | [4, 5, 6] | [3, 7, 8, 9, 10, 12] | [2, 4, 5] | [1, 3, 6, 7, 8, 9, 10, 11, 12] |
| validation:aux_without_rain_original | [2, 3, 4, 6, 7, 8, 9] | [10, 12] | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] | [11, 12] |
| validation:aux_without_rain_augmented | [3, 4, 6, 7, 8, 9, 10] | [5, 11, 12] | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11] | [12] |
| test:year120 | [3, 4, 6, 8, 9, 10, 11, 12] | [1, 2, 5, 7] | [3, 4, 6, 7, 8, 9, 10, 11, 12] | [1, 2, 5] |
| test:year33 | [1, 3, 4, 5, 10] | [6, 7, 8, 9, 11, 12] | [1, 2, 3, 4, 5, 6, 9, 10, 11, 12] | [7, 8] |
| test:year45 | [1, 7, 12] | [2, 3, 4, 5, 8, 9, 10, 11] | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] | [] |
| test:year108 | [1, 3, 4, 6, 8, 9, 10, 11, 12] | [2, 7] | [3, 4, 5, 6, 7, 8, 9, 10, 11, 12] | [1, 2] |
| test:rain_with_aux_original | [5, 8, 12] | [2, 3, 4, 6, 9, 10, 11] | [1, 2, 4, 5, 6, 10, 11, 12] | [3, 7, 8, 9] |
| test:rain_with_aux_augmented | [6, 8, 9, 10, 11, 12] | [1, 2, 7] | [4, 5, 6, 8, 9, 10, 11, 12] | [1, 2, 3, 7] |
| test:rain_without_aux_original | [] | [2, 3, 5, 6, 7, 8, 9, 10, 11, 12] | [1, 5, 11, 12] | [2, 3, 4, 6, 7, 8, 9, 10] |
| test:rain_without_aux_augmented | [4, 8, 12] | [1, 2, 3, 5, 6, 7, 9, 10, 11] | [5, 6, 8, 10, 11, 12] | [1, 2, 3, 4, 7, 9] |
| test:aux_with_rain_original | [2, 3, 4, 5, 6, 8, 9, 11, 12] | [7, 10] | [1, 2, 3, 4, 5, 6, 7, 9, 10, 11] | [8, 12] |
| test:aux_with_rain_augmented | [2, 3, 4, 5, 6, 8, 9, 11, 12] | [1, 10] | [2, 3, 4, 5, 6, 7, 8, 9, 10] | [1, 11, 12] |
| test:aux_without_rain_original | [3, 4, 5, 6, 10] | [7, 8, 9, 11, 12] | [1, 2, 3, 4, 5] | [6, 7, 8, 9, 10, 11, 12] |
| test:aux_without_rain_augmented | [1, 4, 5, 6, 7] | [2, 3, 8, 9, 10, 11, 12] | [1, 3, 4, 5, 6] | [2, 7, 8, 9, 10, 11, 12] |

## Resultados h1/h6/h12

| Fase | h | Família | Acertos/alvos | MAE | Máximo |
|---|---:|---|---:|---:|---:|
| validation | 1 | observed_control | 28/28 | 0.066681 | 0.253657 |
| validation | 1 | augmented | 28/28 | 0.075868 | 0.284468 |
| validation | 1 | core_original | 28/28 | 0.070535 | 0.184259 |
| validation | 1 | core_augmented | 28/28 | 0.060200 | 0.162466 |
| validation | 1 | levels45_original | 28/28 | 0.064297 | 0.214926 |
| validation | 1 | levels45_augmented | 28/28 | 0.057738 | 0.206170 |
| validation | 1 | rain108_original | 28/28 | 0.071123 | 0.186985 |
| validation | 1 | rain108_augmented | 28/28 | 0.071329 | 0.233299 |
| validation | 6 | observed_control | 24/28 | 0.258712 | 1.096290 |
| validation | 6 | augmented | 18/28 | 0.531288 | 2.106793 |
| validation | 6 | core_original | 18/28 | 0.366026 | 0.806297 |
| validation | 6 | core_augmented | 20/28 | 0.328739 | 1.018641 |
| validation | 6 | levels45_original | 25/28 | 0.261199 | 1.061608 |
| validation | 6 | levels45_augmented | 27/28 | 0.273751 | 1.418339 |
| validation | 6 | rain108_original | 20/28 | 0.345540 | 1.231229 |
| validation | 6 | rain108_augmented | 17/28 | 0.519448 | 1.689502 |
| validation | 12 | observed_control | 7/28 | 0.908493 | 2.619470 |
| validation | 12 | augmented | 3/28 | 1.210744 | 2.906819 |
| validation | 12 | core_original | 8/28 | 1.097877 | 3.061248 |
| validation | 12 | core_augmented | 9/28 | 1.093578 | 2.681916 |
| validation | 12 | levels45_original | 3/28 | 1.174292 | 2.257666 |
| validation | 12 | levels45_augmented | 2/28 | 1.243306 | 2.013848 |
| validation | 12 | rain108_original | 8/28 | 0.810315 | 2.372222 |
| validation | 12 | rain108_augmented | 4/28 | 1.107090 | 2.736001 |
| test | 1 | observed_control | 230/237 | 0.077472 | 1.284834 |
| test | 1 | augmented | 229/237 | 0.100567 | 0.776705 |
| test | 1 | core_original | 230/237 | 0.086345 | 1.312938 |
| test | 1 | core_augmented | 232/237 | 0.081383 | 0.772480 |
| test | 1 | levels45_original | 230/237 | 0.078144 | 1.352100 |
| test | 1 | levels45_augmented | 233/237 | 0.076854 | 0.695920 |
| test | 1 | rain108_original | 230/237 | 0.084493 | 1.270991 |
| test | 1 | rain108_augmented | 231/237 | 0.092516 | 0.838805 |
| test | 6 | observed_control | 149/237 | 0.599275 | 5.717301 |
| test | 6 | augmented | 154/237 | 0.545722 | 4.513468 |
| test | 6 | core_original | 144/237 | 0.634925 | 5.675656 |
| test | 6 | core_augmented | 143/237 | 0.616770 | 5.608718 |
| test | 6 | levels45_original | 151/237 | 0.637405 | 6.168964 |
| test | 6 | levels45_augmented | 151/237 | 0.605166 | 5.501555 |
| test | 6 | rain108_original | 134/237 | 0.644839 | 5.544744 |
| test | 6 | rain108_augmented | 142/237 | 0.602831 | 4.984940 |
| test | 12 | observed_control | 83/237 | 1.361813 | 7.589997 |
| test | 12 | augmented | 89/237 | 1.256706 | 7.362831 |
| test | 12 | core_original | 83/237 | 1.370278 | 10.028690 |
| test | 12 | core_augmented | 79/237 | 1.293003 | 9.421135 |
| test | 12 | levels45_original | 75/237 | 1.427580 | 10.211224 |
| test | 12 | levels45_augmented | 78/237 | 1.370022 | 9.347238 |
| test | 12 | rain108_original | 78/237 | 1.357774 | 7.513398 |
| test | 12 | rain108_augmented | 81/237 | 1.238302 | 7.462013 |

## Dominância e limites

Dominância descritiva conjunta definida como acertos não menores, MAE e máximo não maiores em todos os12horizontes, com alguma melhora estrita. Relações encontradas: []. Nenhuma seleção de família por horizonte foi realizada.

As diferenças dos efeitos por ano/bloco estão em interactions.csv; são contrastes aritméticos, não atribuição física nem estimativa de significância. Chuva inclui indicadores de cobertura, e os hiperparâmetros não foram reajustados por representação. Permanecem os limites de disponibilidade/datum/regime entre anos e a ausência do pico2023. Esta auditoria não interpreta ausência como zero nem comprova98% prospectivos.

Os modelos e inferência são verificados separadamente pelo agente principal. Esta tarefa leu apenas matrizes, máscaras, previsões, métricas, código/protocolo e hashes; nenhum modelo foi carregado ou executado. Sem promoção.

## Interpretação dos efeitos condicionais

O acréscimo2023 piora MAE na validação em12/12horizontes com120campos e10/12com108; em45piora5/12 e em33piora3/12. **Retirar somente os níveis auxiliares não elimina a regressão ampla da validação.** Em h12,108original→108+2023 passa de0,810315→1,107090m e8→4acertos;45original→45+2023 passa de1,174292→1,243306m e3→2acertos.

O efeito das entradas de chuva muda conforme os anos usados no treino. Mantendo os auxiliares, adicionar chuva melhora MAE da validação em9/12horizontes no treino original, mas só1/12 após acrescentar2023. Sem auxiliares, melhora9/12original e2/12 aumentado. Essa interação depende do procedimento de ajuste congelado, inclui indicadores de cobertura e não prova efeito físico da precipitação.

No teste, acrescentar2023 ao conjunto45 melhora MAE em12/12horizontes, mas perde acertos em8/12; ao conjunto108 melhora MAE10/12 e acertos9/12, mas perde acertos em2/12. Nenhuma família apresenta dominância conjunta nos critérios declarados, mesmo considerando cada fase separadamente.

Em teste/h12,108+2023 tem MAE1,238302m contra1,256706m de120+2023, mas81contra89acertos e máximo7,462013contra7,362831m. Ganho de erro médio não equivale a ganho de precisão no limiar de0,50m. Não escolheremos uma família diferente por horizonte depois desses resultados.
