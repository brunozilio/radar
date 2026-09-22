# Auditoria independente — Radar observado de120campos

**122 verificações passaram.** Recalculei diretamente de predictions.csv as48linhas de métricas de cheia/full_schedule:24combinações fase×horizonte, duas famílias. Concordância com evaluation.csv até1e−12. Nenhum modelo foi lido, inferido ou treinado.

Cheia: alvo≥7m. Acerto: erro absoluto≤0,50m. Cada horizonte da validação tem28alvos/28pares; cada horizonte do teste tem237alvos/236pares/1falha, nas duas famílias. As máscaras dos pares também coincidem, não apenas suas contagens.

| Fase | h | Acertos180→120 | MAE180→120 (m) | Máximo180→120 (m) |
|---|---:|---:|---:|---:|
| validation | 1 | 28→28 | 0.066987→0.066681 | 0.243992→0.253657 |
| validation | 2 | 28→28 | 0.122403→0.118979 | 0.370170→0.361910 |
| validation | 3 | 26→26 | 0.173415→0.169607 | 0.638271→0.614080 |
| validation | 4 | 26→26 | 0.184390→0.166461 | 0.615579→0.560208 |
| validation | 5 | 25→25 | 0.202945→0.229123 | 0.600808→0.755306 |
| validation | 6 | 24→24 | 0.259427→0.258712 | 1.308811→1.096290 |
| validation | 7 | 17→18 | 0.422249→0.427502 | 2.523308→2.655657 |
| validation | 8 | 19→20 | 0.514018→0.488229 | 2.405568→2.505030 |
| validation | 9 | 17→17 | 0.565691→0.609563 | 1.911718→2.140509 |
| validation | 10 | 10→11 | 0.757323→0.763796 | 1.661940→1.664331 |
| validation | 11 | 8→9 | 0.916902→0.913231 | 2.353719→2.348861 |
| validation | 12 | 8→7 | 0.925149→0.908493 | 2.607250→2.619470 |
| test | 1 | 230→230 | 0.077488→0.077472 | 1.275991→1.284834 |
| test | 2 | 225→225 | 0.142998→0.145745 | 2.462106→2.485409 |
| test | 3 | 206→206 | 0.244249→0.239780 | 3.539570→3.526872 |
| test | 4 | 192→189 | 0.348850→0.347738 | 4.128445→4.159274 |
| test | 5 | 170→174 | 0.459019→0.449501 | 4.864268→4.732018 |
| test | 6 | 147→149 | 0.600976→0.599275 | 5.643662→5.717301 |
| test | 7 | 134→132 | 0.713245→0.735030 | 5.308074→5.611444 |
| test | 8 | 131→128 | 0.805518→0.843765 | 6.001469→6.185898 |
| test | 9 | 113→113 | 0.936280→0.969283 | 5.943609→6.000374 |
| test | 10 | 95→93 | 1.072684→1.067814 | 6.431357→6.464545 |
| test | 11 | 84→85 | 1.210566→1.178292 | 6.882901→6.566431 |
| test | 12 | 86→83 | 1.340765→1.361813 | 7.921526→7.589997 |

## Ganhos e perdas

- validation: ganha acertos em[7, 8, 10, 11], perde em[12], empata em[1, 2, 3, 4, 5, 6, 9]; MAE piora em[5, 7, 9, 10].
- test: ganha acertos em[5, 6, 11], perde em[4, 7, 8, 10, 12], empata em[1, 2, 3, 9]; MAE piora em[2, 7, 8, 9, 12].

O resultado é misto e não demonstra dominância da versão120. Acertos, erro médio e extremos precisam permanecer separados; não foi feita seleção de uma versão por horizonte depois de observar os resultados.

## Falha preservada

A origem22/07/2026 17h tem base ausente. As duas famílias não produzem previsões h1–12, embora todos esses alvos sejam cheias observadas. Os12casos permanecem no arquivo missing-forecasts.csv, com uma linha por família e horizonte. O cálculo observed_target_hit_fraction divide os acertos por237, não236; MAE/P98/máximo usam apenas os236pares finitos. Ausência não virou erro zero nem saiu do denominador de sucesso sobre alvos.

## Limites e integridade

Este é um ensaio de remoção dos60preditoresNWP mantendo120campos observados; não há acréscimo2023/2024 nem substituição por chuva futura zero. Parâmetros foram congelados para outro conjunto de entradas, portanto o resultado não estabelece ótimo de arquitetura. Os períodos já foram inspecionados; a comparação é desenvolvimento descritivo, não avaliação independente ou comprovação prospectiva.

O protocolo declara promoted=false e goal_achieved=false, conferidos nesta auditoria. Sem promoção, alteração operacional ou declaração de meta alcançada. O agente principal cuida da verificação dos modelos e membership; esta tarefa limitou-se às métricas e cobertura.

audit.py reproduz o cálculo local; verification.json/CSVs preservam todos os números; source-manifest.json registra os três arquivos lidos e seus hashes; artifact-hashes.json cobre os artefatos próprios.
