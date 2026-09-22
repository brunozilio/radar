# Auditoria independente: acréscimo de 2023 ao Radar observado

125 verificações passaram. As 48 métricas de cheia/full_schedule foram recalculadas diretamente das previsões e coincidem até 1e-12. Controle de 120 campos, alvos, bases e chaves reproduzem exatamente o experimento anterior.

Cada horizonte tem 28 alvos/28 pares na validação e 237 alvos/236 pares/1 falha no teste. A falha da origem 22/07 17h permanece no denominador de sucesso sobre alvos observados. Erros finitos não recebem zero para ausências.

| Fase | h | Acertos controle→2023 | MAE (m) | Máximo (m) |
|---|---:|---:|---:|---:|
| validation | 1 | 28→28 | 0.066681→0.075868 | 0.253657→0.284468 |
| validation | 2 | 28→28 | 0.118979→0.129519 | 0.361910→0.447688 |
| validation | 3 | 26→25 | 0.169607→0.204033 | 0.614080→0.593229 |
| validation | 4 | 26→26 | 0.166461→0.240353 | 0.560208→0.848732 |
| validation | 5 | 25→25 | 0.229123→0.325427 | 0.755306→1.235331 |
| validation | 6 | 24→18 | 0.258712→0.531288 | 1.096290→2.106793 |
| validation | 7 | 18→13 | 0.427502→0.602535 | 2.655657→3.523294 |
| validation | 8 | 20→11 | 0.488229→0.829559 | 2.505030→3.250993 |
| validation | 9 | 17→8 | 0.609563→1.043689 | 2.140509→3.009558 |
| validation | 10 | 11→6 | 0.763796→1.184996 | 1.664331→3.263361 |
| validation | 11 | 9→5 | 0.913231→1.237115 | 2.348861→3.328471 |
| validation | 12 | 7→3 | 0.908493→1.210744 | 2.619470→2.906819 |
| test | 1 | 230→229 | 0.077472→0.100567 | 1.284834→0.776705 |
| test | 2 | 225→209 | 0.145745→0.194267 | 2.485409→1.095394 |
| test | 3 | 206→211 | 0.239780→0.237143 | 3.526872→3.087788 |
| test | 4 | 189→194 | 0.347738→0.313092 | 4.159274→3.527514 |
| test | 5 | 174→169 | 0.449501→0.462485 | 4.732018→4.334248 |
| test | 6 | 149→154 | 0.599275→0.545722 | 5.717301→4.513468 |
| test | 7 | 132→126 | 0.735030→0.719145 | 5.611444→3.687599 |
| test | 8 | 128→135 | 0.843765→0.732589 | 6.185898→3.913273 |
| test | 9 | 113→121 | 0.969283→0.857575 | 6.000374→4.531147 |
| test | 10 | 93→97 | 1.067814→0.935727 | 6.464545→4.770160 |
| test | 11 | 85→89 | 1.178292→1.129228 | 6.566431→5.820891 |
| test | 12 | 83→89 | 1.361813→1.256706 | 7.589997→7.362831 |

Nos 12 pares de teste/12h com resposta acima de 8,09 m, 11 melhoram e 1 pioram. MAE 6.770415→5.777524 m; máximo 7.589997→7.362831 m. As 12 origens e erros estão preservados no CSV.

Resultado misto: não há dominância geral nem promoção. Os períodos já inspecionados constituem desenvolvimento; esta auditoria não estabelece causalidade física dos ganhos, disponibilidade histórica certificada, equivalência de datum/regime entre anos ou meta de 98%. Nenhum treino ou consulta nova foi executado.
