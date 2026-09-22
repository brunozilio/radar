# Auditoria independente — ampliação Radar com histórico2024

**102 verificações passaram; métricas conferidas diretamente de predictions.csv.** Nenhum treino, inferência de modelo, consulta de rede ou alteração de fonte foi realizado.

As102.084chaves, bases, alvos, flags de completude e valores do controle nativo reproduzem exatamente o candidato native-missing congelado anterior. As48linhas de métricas abaixo (24fase×horizonte,2famílias) concordam com evaluation.csv até1e−12.

Cheia significa alvo observado≥7m; acerto significa erro absoluto≤0,50m. Validação tem28alvos/28pares em cada horizonte. Teste tem237alvos/236pares e1falha em cada horizonte, em ambas as famílias. A falha não é removida da fração sobre alvos observados; MAE/P98/máximo são calculados apenas nos pares finitos.

## Todas as combinações de cheia/full_schedule

| Fase | h | Acertos controle→ampliado | MAE controle→ampliado (m) | Máximo controle→ampliado (m) |
|---|---:|---:|---:|---:|
| validation | 1 | 28→28 | 0.066987→0.067699 | 0.243992→0.223137 |
| validation | 2 | 28→27 | 0.122403→0.127114 | 0.370170→0.512374 |
| validation | 3 | 26→25 | 0.173415→0.191240 | 0.638271→0.701419 |
| validation | 4 | 26→25 | 0.184390→0.244072 | 0.615579→0.776778 |
| validation | 5 | 25→23 | 0.202945→0.320278 | 0.600808→1.075664 |
| validation | 6 | 24→24 | 0.259427→0.293634 | 1.308811→1.363368 |
| validation | 7 | 17→21 | 0.422249→0.350655 | 2.523308→2.128943 |
| validation | 8 | 19→15 | 0.514018→0.646275 | 2.405568→2.714775 |
| validation | 9 | 17→16 | 0.565691→0.583911 | 1.911718→2.128683 |
| validation | 10 | 10→8 | 0.757323→0.816589 | 1.661940→1.664724 |
| validation | 11 | 8→12 | 0.916902→0.749286 | 2.353719→1.909249 |
| validation | 12 | 8→10 | 0.925149→0.893903 | 2.607250→2.186274 |
| test | 1 | 230→231 | 0.077488→0.068692 | 1.275991→1.001472 |
| test | 2 | 225→228 | 0.142998→0.122657 | 2.462106→1.879170 |
| test | 3 | 206→213 | 0.244249→0.229009 | 3.539570→3.337878 |
| test | 4 | 192→199 | 0.348850→0.312420 | 4.128445→3.748374 |
| test | 5 | 170→174 | 0.459019→0.436043 | 4.864268→4.449296 |
| test | 6 | 147→155 | 0.600976→0.543438 | 5.643662→5.270447 |
| test | 7 | 134→153 | 0.713245→0.620658 | 5.308074→4.147899 |
| test | 8 | 131→117 | 0.805518→0.820354 | 6.001469→4.500143 |
| test | 9 | 113→105 | 0.936280→0.933740 | 5.943609→5.674987 |
| test | 10 | 95→105 | 1.072684→0.961160 | 6.431357→5.724225 |
| test | 11 | 84→102 | 1.210566→1.080443 | 6.882901→7.127691 |
| test | 12 | 86→88 | 1.340765→1.283900 | 7.921526→8.088067 |

O candidato **não domina a referência**: no teste ganha acertos em10horizontes, perde em8h(−14) e9h(−8). Na validação ganha em3, perde em7 e empata em2. O MAE teste piora em8h; em9h melhora ligeiramente apesar da redução de acertos. O máximo teste piora em11h e12h. Estes critérios não são intercambiáveis.

## Falha explícita

Origem22/07/2026 17h UTC−3: base ausente e ambas as previsões ausentes para h1–12. Os alvos existem e são cheias: de18,68m em22/07 18h a14,07m em23/07 05h. Esses12casos (um por horizonte) permanecem no arquivo missing-forecasts.csv. Em12h, a fração de sucesso sobre todos os237alvos é86/237→88/237; a fração condicional sobre236pares é distinta.

## Maior erro de12h

O máximo do controle ocorre na origem21/07 19h, alvo22/07 07h: observado16,50m, controle8,578474m, ampliado9,087447m. Nesse mesmo par, erro absoluto melhora7,921526→7,412553m.

O maior erro do ampliado muda para origem21/07 16h, alvo22/07 04h: observado14,49m, controle7,365617m, ampliado6,401933m. Nesse par piora7,124383→8,088067m. Logo, melhorar o antigo pior caso não implica reduzir o novo máximo.

## Doze respostas acima da amplitude original de treino

A regra é alvo−base>8,09m, limite de resposta12h copiado do diagnóstico anterior preservado; não é um limite físico. Não foi reajustado ao novo resultado. São12origens21/07 12h–23h, já inspecionadas anteriormente, com alvos22/07 00h–11h.

| Origem21/07 | Alvo22/07 | ΔH observado (m) | Erro absoluto controle (m) | Ampliado (m) |
|---|---|---:|---:|---:|
| 13:00 | 01:00 | 8.40 | 7.148307 | 6.722196 |
| 14:00 | 02:00 | 9.43 | 7.180207 | 7.133505 |
| 15:00 | 03:00 | 10.36 | 6.272309 | 6.511707 |
| 16:00 | 04:00 | 11.22 | 7.124383 | 8.088067 |
| 17:00 | 05:00 | 11.95 | 7.575349 | 7.496036 |
| 18:00 | 06:00 | 12.56 | 7.502187 | 7.449380 |
| 19:00 | 07:00 | 13.08 | 7.921526 | 7.412553 |
| 20:00 | 08:00 | 13.27 | 7.755932 | 6.143131 |
| 21:00 | 09:00 | 12.76 | 7.337688 | 5.568257 |
| 22:00 | 10:00 | 11.42 | 6.199664 | 5.410038 |
| 23:00 | 11:00 | 10.02 | 5.262405 | 4.503108 |
| 00:00 | 12:00 | 8.60 | 4.262346 | 3.420649 |

Melhora o erro absoluto em10pares e piora em2 (origens15h e16h). MAE6,795192→6,321552m; máximo7,921526→8,088067m; **zero acertos nos12pares em ambas as versões**. Todas as previsões desses pares ficam abaixo do nível observado. Esse grupo é um diagnóstico pós-inspeção, não um teste independente.

## Artefatos e limites

audit.py reproduz a auditoria somente local; verification.json inclui métricas, falhas, pares extremos e verificações; osCSVs facilitam reuso sem recalcular. source-manifest.json registra hashes das fontes lidas e artifact-hashes.json registra os artefatos próprios.

Não foram auditados aqui ajuste dos modelos ou membership do treino novo; essa parte está com o agente principal. A referência de8,09m vem do inventário anterior, não de novo ajuste. Os períodos de avaliação já foram usados em desenvolvimento; as métricas são descritivas, não comprovação prospectiva ou evidência independente de generalização. Nenhuma promoção ou declaração de meta alcançada.
