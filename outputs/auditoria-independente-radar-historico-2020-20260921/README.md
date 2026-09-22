# Auditoria independente: acréscimo de 2020 ao Radar observado

200 verificações passaram. As 48 métricas de cheia/full_schedule foram recalculadas diretamente das previsões e coincidem até 1e-12. Controle de 120 campos, alvos, bases e chaves reproduzem exatamente o experimento anterior.

Cada horizonte tem 28 alvos/28 pares na validação e 237 alvos/236 pares/1 falha no teste. A falha da origem 22/07 17h permanece no denominador de sucesso sobre alvos observados. Erros finitos não recebem zero para ausências.

| Fase | h | Acertos controle→2020 | MAE (m) | Máximo (m) |
|---|---:|---:|---:|---:|
| validation | 1 | 28→28 | 0.066681→0.063333 | 0.253657→0.249438 |
| validation | 2 | 28→28 | 0.118979→0.116966 | 0.361910→0.372859 |
| validation | 3 | 26→26 | 0.169607→0.150267 | 0.614080→0.550683 |
| validation | 4 | 26→23 | 0.166461→0.292123 | 0.560208→0.709390 |
| validation | 5 | 25→25 | 0.229123→0.235502 | 0.755306→0.895426 |
| validation | 6 | 24→21 | 0.258712→0.355074 | 1.096290→1.386024 |
| validation | 7 | 18→22 | 0.427502→0.365996 | 2.655657→1.610408 |
| validation | 8 | 20→21 | 0.488229→0.375791 | 2.505030→0.760126 |
| validation | 9 | 17→15 | 0.609563→0.504474 | 2.140509→0.983489 |
| validation | 10 | 11→10 | 0.763796→0.735694 | 1.664331→1.671329 |
| validation | 11 | 9→11 | 0.913231→0.770373 | 2.348861→1.913148 |
| validation | 12 | 7→7 | 0.908493→0.892804 | 2.619470→2.626978 |
| test | 1 | 230→231 | 0.077472→0.064764 | 1.284834→0.937513 |
| test | 2 | 225→225 | 0.145745→0.133403 | 2.485409→1.739874 |
| test | 3 | 206→218 | 0.239780→0.204529 | 3.526872→3.054983 |
| test | 4 | 189→195 | 0.347738→0.312034 | 4.159274→3.789298 |
| test | 5 | 174→180 | 0.449501→0.414250 | 4.732018→4.197175 |
| test | 6 | 149→163 | 0.599275→0.536116 | 5.717301→4.704522 |
| test | 7 | 132→164 | 0.735030→0.546890 | 5.611444→4.638033 |
| test | 8 | 128→143 | 0.843765→0.677792 | 6.185898→5.446067 |
| test | 9 | 113→124 | 0.969283→0.809448 | 6.000374→6.169177 |
| test | 10 | 93→109 | 1.067814→0.945992 | 6.464545→6.448104 |
| test | 11 | 85→101 | 1.178292→1.091871 | 6.566431→7.526431 |
| test | 12 | 83→87 | 1.361813→1.230338 | 7.589997→7.974639 |

Nos 12 pares de teste/12h com resposta acima de 8,09 m, 9 melhoram e 3 pioram. MAE 6.770415→6.502509 m; máximo 7.589997→7.974639 m. As 12 origens e erros estão preservados no CSV.

Resultado misto: não há dominância geral nem promoção. Os períodos já inspecionados constituem desenvolvimento; esta auditoria não estabelece causalidade física dos ganhos, disponibilidade histórica certificada, equivalência de datum/regime entre anos ou meta de 98%. Nenhum treino ou consulta nova foi executado.

As 92 verificações independentes de membership passaram; as 36 máscaras salvas e as 24 linhas de treinamento concordam com a reconstrução. Somente 2020 foi acrescentado aos dados originais de 2025/26: nenhum dado de 2021/22 reservado ou de 2023/24 foi incluído. Cutoffs estritos dos alvos: 01/10/2025 e 01/07/2026.

Pesos reconstruídos pela fórmula congelada 1 + 2·I(|alvo−base|≥1 m) + 2·I(alvo≥9 m). São somas derivadas das memberships e da fórmula, não um novo ajuste nem um log de pesos do estimador.

| Fase | h | Pares de 2020 | Alvos ≥7 m | Peso original | Peso 2020 | Fração do peso de 2020 |
|---|---:|---:|---:|---:|---:|---:|
| validation | 1 | 447 | 189 | 4646 | 661 | 12.4552% |
| test | 1 | 447 | 189 | 11137 | 661 | 5.6026% |
| validation | 6 | 437 | 179 | 5334 | 815 | 13.2542% |
| test | 6 | 437 | 179 | 12558 | 815 | 6.0944% |
| validation | 12 | 426 | 167 | 6004 | 992 | 14.1795% |
| test | 12 | 426 | 167 | 13812 | 992 | 6.7009% |

As 23 origens com algum Q/I zero não geram nenhum par elegível em h1..12: 22 têm base Muçum ausente; a única base finita é 08/07/2020 05h, 19,02 m, com todos os 12 alvos ausentes. Isto decorre das máscaras existentes, sem filtro novo sobre zeros; o apagão/QC do pico continua sendo uma limitação.

Pior erro do candidato no teste/12h: origem 2026-07-21T17:00:00-03:00, alvo 2026-07-22T05:00:00-03:00, base 3.21 m, observado 15.16 m, previsão 7.185360632 m, erro absoluto 7.974639368 m. Na mesma origem, controle 7.708730561 m e erro 7.451269439 m. O máximo do controle (7,589996584 m) ocorre em outra origem.

No teste, MAE melhora nos 12 horizontes e acertos melhoram em 11 (um empate). Na validação, acertos melhoram em três, empatam em cinco e pioram em quatro; h6 cai de 24 para 21/28. Não há dominância geral.
