# Radar com níveis de reservatórios

24 candidatos foram treinados com 204 preditores: os 180 originais mais os 24 níveis e variações de montante/jusante de 14 de Julho, Monte Claro e Castro Alves. A referência permaneceu congelada; o candidato manteve seus índices de treino, pesos e parâmetros. Não houve componente HGE.

|Fase|Prazo|Recorte|Modelo|N|Acertos ≤0,50 m|MAE (m)|Máximo (m)|
|---|---|---|---|---|---|---|---|
|validation|1|all|baseline|6479|6478 (99.98%)|0.0194|0.6443|
|validation|1|all|candidate|6479|6478 (99.98%)|0.0194|0.6669|
|validation|1|level_ge_7m|baseline|28|28 (100.00%)|0.0670|0.2244|
|validation|1|level_ge_7m|candidate|28|28 (100.00%)|0.0679|0.2080|
|validation|6|all|baseline|6472|6362 (98.30%)|0.0918|1.3726|
|validation|6|all|candidate|6472|6372 (98.45%)|0.0933|1.2511|
|validation|6|level_ge_7m|baseline|28|24 (85.71%)|0.2646|1.2348|
|validation|6|level_ge_7m|candidate|28|24 (85.71%)|0.2358|0.9339|
|validation|12|all|baseline|6466|5182 (80.14%)|0.3257|2.3333|
|validation|12|all|candidate|6466|5376 (83.14%)|0.2992|2.3204|
|validation|12|level_ge_7m|baseline|28|8 (28.57%)|0.7742|1.6670|
|validation|12|level_ge_7m|candidate|28|11 (39.29%)|0.7229|1.7199|
|test|1|all|baseline|1939|1933 (99.69%)|0.0371|1.3044|
|test|1|all|candidate|1939|1933 (99.69%)|0.0372|1.3024|
|test|1|level_ge_7m|baseline|236|230 (97.46%)|0.0853|1.3044|
|test|1|level_ge_7m|candidate|236|230 (97.46%)|0.0852|1.3024|
|test|6|all|baseline|1927|1759 (91.28%)|0.2096|5.9593|
|test|6|all|candidate|1927|1765 (91.59%)|0.2045|6.1150|
|test|6|level_ge_7m|baseline|236|154 (65.25%)|0.6237|5.9593|
|test|6|level_ge_7m|candidate|236|158 (66.95%)|0.6076|6.1150|
|test|12|all|baseline|1915|1296 (67.68%)|0.5144|7.1202|
|test|12|all|candidate|1915|1370 (71.54%)|0.4713|6.8643|
|test|12|level_ge_7m|baseline|236|75 (31.78%)|1.3995|7.1202|
|test|12|level_ge_7m|candidate|236|84 (35.59%)|1.3275|6.8643|

Todos os 102.084 agendamentos anteriores estão preservados. evaluation.csv contém cada prazo, as falhas de cobertura e os subconjuntos com/sem os primeiros 24 campos preenchidos; changes.csv contém todas as diferenças por horizonte.

Houve ganhos nos prazos longos nas duas fases, mas não em todos os recortes. No teste de cheia, 6 horas teve 154→158 acertos e 12 horas 75→84, em 236 pares por prazo; 2 horas perdeu três acertos. Na fase validation, a cheia de 12 horas passou 8→11/28 acertos, enquanto 4 horas perdeu um. Não houve seleção posterior de prazos para substituir partes da previsão operacional.

O treino continua com o filtro original dos primeiros 24 campos completos; a mudança de política de treino testada anteriormente não foi incorporada a este candidato. A inferência e a avaliação incluem as origens com campos ausentes, desde que haja nível-base de Muçum.

Os níveis dos reservatórios mantêm seus próprios referenciais. Não foram convertidos em volume, subtraídos entre estações ou tratados como estimativas de vazão física. Os registros anômalos documentados permanecem no acervo.

A disponibilidade é uma hipótese histórica: atraso de 60 minutos mais vencimento de 90 minutos após a consulta atrasada, sem reposicionar o registro de 23h59. Isso admite idade total de até 150 minutos na origem, não apenas 90; a maior idade efetivamente aceita foi 121 minutos. Ausência no registro mais novo permanece ausência. Não há comprovação de publicação do dado naquele instante.

São períodos de desenvolvimento já inspecionados; a fase validation também participou da escolha anterior dos parâmetros da referência. Não houve promoção, atualização do runner, emissão operacional, deploy ou alegação de 98% prospectivos.
