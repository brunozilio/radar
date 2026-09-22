# Auditoria independente do experimento fatorial Radar core33

263 verificações passaram. Recalculei os96 grupos de cheia/full_schedule diretamente de predictions.csv; concordância até1e-12 com evaluation.csv. As102.084 chaves, bases, alvos, duas previsões controle e disponibilidade das quatro famílias coincidem exatamente com o experimento anterior. Todas as36 máscaras e os48 totais de treino/pesos conferem.

Cada horizonte/família mantém28alvos/28pares na validação e237alvos/236pares/1falha no teste. A falta da origem22/07 17h é preservada; MAE usa pares finitos e sucesso sobre alvos usa237 como denominador.

Comparação por horizonte, sem escolher versões após observar desempenho. Acerto é erro≤0,50m e cheia é alvo≥7m. A tabela mostra **original→com2023** dentro de cada conjunto de entradas.

| Fase | h | Acertos120 | MAE120 (m) | Acertos33 | MAE33 (m) |
|---|---:|---:|---:|---:|---:|
| validation | 1 | 28→28 | 0.066681→0.075868 | 28→28 | 0.070535→0.060200 |
| validation | 2 | 28→28 | 0.118979→0.129519 | 27→28 | 0.163169→0.124383 |
| validation | 3 | 26→25 | 0.169607→0.204033 | 24→27 | 0.213448→0.191048 |
| validation | 4 | 26→26 | 0.166461→0.240353 | 22→25 | 0.312572→0.283839 |
| validation | 5 | 25→25 | 0.229123→0.325427 | 24→25 | 0.311633→0.339397 |
| validation | 6 | 24→18 | 0.258712→0.531288 | 18→20 | 0.366026→0.328739 |
| validation | 7 | 18→13 | 0.427502→0.602535 | 14→12 | 0.607830→0.543026 |
| validation | 8 | 20→11 | 0.488229→0.829559 | 10→11 | 0.677232→0.641760 |
| validation | 9 | 17→8 | 0.609563→1.043689 | 7→7 | 0.771926→0.769249 |
| validation | 10 | 11→6 | 0.763796→1.184996 | 8→8 | 0.828350→0.909266 |
| validation | 11 | 9→5 | 0.913231→1.237115 | 5→9 | 0.965397→0.985872 |
| validation | 12 | 7→3 | 0.908493→1.210744 | 8→9 | 1.097877→1.093578 |
| test | 1 | 230→229 | 0.077472→0.100567 | 230→232 | 0.086345→0.081383 |
| test | 2 | 225→209 | 0.145745→0.194267 | 227→227 | 0.159466→0.142952 |
| test | 3 | 206→211 | 0.239780→0.237143 | 203→213 | 0.271074→0.238315 |
| test | 4 | 189→194 | 0.347738→0.313092 | 181→186 | 0.389679→0.353063 |
| test | 5 | 174→169 | 0.449501→0.462485 | 160→162 | 0.518808→0.501343 |
| test | 6 | 149→154 | 0.599275→0.545722 | 144→143 | 0.634925→0.616770 |
| test | 7 | 132→126 | 0.735030→0.719145 | 138→135 | 0.672084→0.678688 |
| test | 8 | 128→135 | 0.843765→0.732589 | 132→124 | 0.754689→0.774820 |
| test | 9 | 113→121 | 0.969283→0.857575 | 123→118 | 0.896037→0.864075 |
| test | 10 | 93→97 | 1.067814→0.935727 | 100→106 | 1.058953→1.006675 |
| test | 11 | 85→89 | 1.178292→1.129228 | 99→95 | 1.209384→1.128199 |
| test | 12 | 83→89 | 1.361813→1.256706 | 83→79 | 1.370278→1.293003 |

## Ganhos e regressões

- validation:add2023_with120: ganha acertos h[]; perde h[3, 6, 7, 8, 9, 10, 11, 12]; melhora MAE h[]; piora MAE h[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].
- validation:add2023_with33: ganha acertos h[2, 3, 4, 5, 6, 8, 11, 12]; perde h[7]; melhora MAE h[1, 2, 3, 4, 6, 7, 8, 9, 12]; piora MAE h[5, 10, 11].
- validation:reduce120to33_original: ganha acertos h[12]; perde h[2, 3, 4, 5, 6, 7, 8, 9, 10, 11]; melhora MAE h[]; piora MAE h[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].
- validation:reduce120to33_augmented: ganha acertos h[3, 6, 10, 11, 12]; perde h[4, 7, 9]; melhora MAE h[1, 2, 3, 6, 7, 8, 9, 10, 11, 12]; piora MAE h[4, 5].
- test:add2023_with120: ganha acertos h[3, 4, 6, 8, 9, 10, 11, 12]; perde h[1, 2, 5, 7]; melhora MAE h[3, 4, 6, 7, 8, 9, 10, 11, 12]; piora MAE h[1, 2, 5].
- test:add2023_with33: ganha acertos h[1, 3, 4, 5, 10]; perde h[6, 7, 8, 9, 11, 12]; melhora MAE h[1, 2, 3, 4, 5, 6, 9, 10, 11, 12]; piora MAE h[7, 8].
- test:reduce120to33_original: ganha acertos h[2, 7, 8, 9, 10, 11]; perde h[3, 4, 5, 6]; melhora MAE h[7, 8, 9, 10]; piora MAE h[1, 2, 3, 4, 5, 6, 11, 12].
- test:reduce120to33_augmented: ganha acertos h[1, 2, 3, 7, 10, 11]; perde h[4, 5, 6, 8, 9, 12]; melhora MAE h[1, 2, 7, 11]; piora MAE h[3, 4, 5, 6, 8, 9, 10, 12].

Os CSVs incluem todos os quatro contrastes principais e a diferença entre os efeitos de acréscimo (33 menos120). Essa interação é apenas descritiva: não é inferência estatística, não torna os28alvos independentes e não prova que ausências ou chuva foram a causa física da regressão. Os parâmetros permaneceram congelados, portanto também não há alegação de arquitetura ótima.

Sem novos ajustes, execução de modelos, coleta ou mudança operacional. Os controles e máscaras conferem; a inferência dos modelos é auditada pelo agente principal. Nenhuma promoção ou composição de famílias por horizonte.

## A redução resolveu a regressão da validação?

**Parcialmente no contraste de acréscimo, não como solução geral.** Adicionar2023 a120 piorou o MAE dos12horizontes da validação; dentro33 melhora9 e piora3 (h5/10/11). Entretanto, reduzir120→33 sem2023 já piora MAE nos12horizontes da validação. Assim, inverter o sinal do efeito de acréscimo sobre uma referência pior não equivale a recuperar o desempenho original.

Em h6 da validação,120original→120+2023→33original→33+2023 produz MAE0,258712→0,531288→0,366026→0,328739m e24→18→18→20acertos. Em h12: MAE0,908493→1,210744→1,097877→1,093578m e7→3→8→9acertos. O ganho em acertos pode coexistir com MAE maior.

No teste, acrescentar2023 dentro33 melhora MAE em10/12horizontes, mas perde acertos em6 (h6/7/8/9/11/12). Em h12,120+2023→33+2023 reduz89→79acertos, piora MAE1,256706→1,293003m e máximo7,362831→9,421135m. Não há dominância.

**Cuidado com98%:** core33+2023/teste/h1 tem232/236=98,305% apenas entre pares disponíveis, mas232/237=97,890% sobre os alvos observados, incluindo a falha. Isso não alcança98% no denominador completo e tampouco representa desempenho global ou prospectivo.

A remoção conjunta dos níveis SantaTereza/Carreiro e da chuva não separa o efeito de cada família; esta comparação não identifica a causa específica da regressão.
