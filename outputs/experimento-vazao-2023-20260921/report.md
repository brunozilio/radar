# Treinamento experimental com a cheia de2023

Decisão: candidato não promovido. Parâmetros e avaliação seguiram o protocolo definido antes do ajuste. Os dados de2023 permanecem preservados; nenhum resultado alterou os modelos em acompanhamento.

| Período | Família | MAE geral | MAE vazões altas | Viés nas vazões altas |
|---|---|---:|---:|---:|
| validation | reference_full | 81.98 | 285.24 | 19.75 |
| validation | reference_ceran_only | 74.86 | 324.89 | -101.55 |
| validation | augmented_ceran_2023 | 84.49 | 406.71 | -116.14 |
| test | reference_full | 169.23 | 437.99 | -152.16 |
| test | reference_ceran_only | 173.81 | 491.88 | -83.59 |
| test | augmented_ceran_2023 | 175.25 | 454.72 | -131.30 |

Vazões e erros em m³/s. Média ponderada pela quantidade de pares, nos prazos0–11h. O recorte de vazões altas usa o percentil95 de14deJulho anterior a01/10/2025, preservado da referência; não é a definição de cheia de Muçum. Os336pares de validação e3.252de desenvolvimento são correlacionados e não equivalem a eventos independentes.

A referência completa teve MAE285,24m³/s nas vazões altas da validação; retirar chuva/tributário elevou para324,89. Adicionar2023 ao modelo reduzido elevou novamente para406,71. No desenvolvimento posterior, acrescentar2023 melhorou o modelo reduzido, mas o resultado454,72 continuou pior que437,99 da referência completa. Não há ganho sustentado que justifique substituição.

## Diagnóstico atual, origem18h de21/09

| Família | Vazão estimada0h | +5h | +11h |
|---|---:|---:|---:|
| reference_full | 7654.78 | 17072.03 | 19341.99 |
| reference_ceran_only | 7787.73 | 19137.37 | 24872.12 |
| augmented_ceran_2023 | 8090.76 | 21949.19 | 28775.39 |

Os modelos desta comparação usam o histórico de latência congelado das15h e a entrada atual do snapshot18h; não são reprodução do ajuste horário ativo. A leitura mais recente de14deJulho era17h, portanto o valor0h é estimativa, não observação. Nenhum destes diagnósticos foi emitido como previsão adicional.

## Auditoria e limitações

Foram acrescentadas669–681origens de2023 por antecedência; o máximo alvo adicional é15.114m³/s. Os alvos são exclusivamente vazões publicadas em horas exatas. Registros23:59 podem ser entradas após o atraso presumido, mas não foram deslocados para criar alvos à meia-noite. Não se usou pico de nível Muçum, precipitação inventada ou vazão futura como entrada.

A referência reproduziu os resultados históricos anteriores até tolerância1e-8m³/s. Os três candidatos têm exatamente os mesmos alvos/recortes de avaliação, confirmados por hash. Os dados brutos, política, código,36modelos finais, entradas e escolhas foram preservados. A suíte local passou64testes, incluindo vazamento temporal, expiração de leitura carregada, sinais por campo e não conversão23:59→00h.

Disponibilidade original, fuso histórico e regime operacional pré-avarias2024 seguem limitações. O evento2023 e o período de desenvolvimento posterior já foram examinados; nenhum deles representa teste independente novo. Os resultados não provam98% de acerto de nível. A simples adição de uma cheia maior, nesta representação linear, foi insuficiente. O próximo candidato deve tratar a dinâmica e a extrapolação mantendo essas avaliações como desenvolvimento.
