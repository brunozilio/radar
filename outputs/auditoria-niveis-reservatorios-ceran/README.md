# Auditoria de níveis de reservatórios ONS/CERAN

Leitura em 21/09/2026, sem downloads, máscaras, correções, interpolação ou alteração de scripts compartilhados. Escopo: 18 CSVs ONS existentes, abril/2025 a 21/09/2026 11h; 38.764 linhas. Montante/jusante são analisados separadamente em metros. Volume útil não foi utilizado.

## Achado prioritário

**14 de Julho, jusante, 03/05/2025 14h: 168,74 m**, entre **68,74 m às 13h e 68,75 m às 15h**. São saltos +100,00 e −99,99 m em uma hora, com I/Q=29/29 m³/s na linha central. Origem exata: `DADOS_HIDROLOGICOS_HO_2025_05-ceran.csv`, linha 63 (linhas 62/64 vizinhas). O mesmo registro tem montante 102,88 m. Forte suspeita de erro isolado no campo jusante, mas a causa e valor correto não estão documentados. Não foi substituído por 68,74, eliminado ou mascarado. Contexto integral 11–17h em `julho-spike-context-original.csv`.

Este ponto pode afetar ajustes com jusante mesmo sendo positivo/finito e, portanto, aceito por um filtro que só rejeite negativos/NaN. Deve permanecer visível na avaliação do experimento original. Qualquer análise de sensibilidade futura requer regra declarada e separação dos resultados; não apagar erros retrospectivamente.

## Integridade e lacunas

| Usina | Linhas | Duplicatas por timestamp | Horas sem linha¹ | Montante ausente | Jusante ausente | Zeros/negativos nos níveis |
|---|---:|---:|---:|---:|---:|---:|
| Castro Alves | 12.921 | 0 | 2 | 0 | 0 | 0 |
| Monte Claro | 12.921 | 0 | 2 | 0 | 0 | 0 |
| 14 de Julho | 12.922 | 0 | 1 | 1 | 0 | 0 |

Não há timestamps inválidos nem valores infinitos/strings não numéricas além do único campo vazio. O campo vazio de montante de Julho é **30/05/2025 01h**, CSV maio/2025 linha 698; jusante=71,68 m, I=438, Q=470 m³/s. Ausência não foi convertida em zero.

Horas sem registro: Castro **30/05/2025 02h**, **03/08/2026 14h**; Monte **30/05/2025 01–02h**; Julho **22/12/2025 10h**. Isso exclui períodos externos à cobertura e não garante ausência de falhas de medição entre registros existentes.

¹Para inventariar a grade, as 538 etiquetas `23:59` de cada usina foram interpretadas como fim do dia (`24:00`), **hipótese ainda não confirmada do exportador**. Strings originais não foram modificadas. Depois dessa hipótese não há instantes fora da grade. `missing-hours.csv` explicita o critério.

## Saltos horários: sinalização de amplitude, não rejeição

Comparadas somente linhas adjacentes com intervalo original entre 59 e 61 minutos e ambos os valores finitos; nenhuma diferença atravessa buracos de várias horas. Limiares absolutos de 1 m e 5 m foram usados apenas para inventário, sem ajustar pelo erro dos modelos nem afirmar tolerância física. Taxa por hora e intervalo real também estão salvos. Máximo absoluto inclui valores suspeitos.

| Usina / campo | Faixa finita observada (m) | Saltos ≥1 m | Maior salto absoluto |
|---|---:|---:|---:|
| Castro / montante | 236,92–245,92 | 1 | +1,10 m, 21/09/2026 11h |
| Castro / jusante | 145,36–157,56 | 37 | +2,70 m, 02/08/2025 21h |
| Monte / montante | 146,80–153,39 | 1 | +1,06 m, 07/08/2025 10h |
| Monte / jusante | 103,00–119,41 | 122 | +4,64 m, 22/03/2026 18h |
| Julho / montante | 97,21–108,15 | 0 | +0,52 m, 21/09/2026 11h |
| Julho / jusante | 66,75–168,74 | 274 | +100,00 m, 03/05/2025 14h |

Há **435 diferenças ≥1 m**; apenas duas ≥5 m, ambas entrada/saída do pico isolado de Julho. Os demais saltos podem refletir cheias, operação, medição ou erro; não foram invalidados. Datas/valores/linhas anteriores e posteriores estão em `hourly-jumps-ge1m.csv`; `top20-hourly-jumps-per-series.csv` preserva os vinte maiores de cada série, inclusive abaixo de 1 m. Quantis e contagens em `summary.json`.

Os máximos atuais de montante Castro e Julho, às 11h, pertencem à subida observada de 21/09; a amplitude elevada sozinha não os torna erro. Mínimos abaixo de cotas normais de cadastro também não foram classificados automaticamente como inválidos, dadas obras/regimes documentados anteriormente.

## Contrato dos campos CERAN ao vivo

Foram lidas somente as três páginas já preservadas na emissão `mucum-hourly-20260921T180020-0300`. Cada uma contém 48 linhas, de **19/09/2026 18h a 21/09/2026 17h**, com cabeçalhos literais:

- `Data / Hora`
- `Nível Montante (m)`
- `Nível Justante (m)` — grafia da própria fonte, aparentemente correspondente a jusante; preservada no inventário.

Os níveis ocupam as colunas 2/3 do HTML. É compatibilidade nominal de grandeza/unidade com `val_nivelmontante`/`val_niveljusante` ONS, não prova de mesmo datum, sensor, ponto físico, janela de agregação ou convenção de revisão. Nenhuma das três páginas declara UTC/GMT/Brasília/fuso, nem foi localizada referência vertical nelas.

**240 pares numéricos de níveis nos mesmos relógios originais** (40 horários × 2 campos × 3 usinas) coincidem exatamente com o ONS: maior diferença 0 m. As 48 linhas por página não geram 48 pareamentos porque a cobertura ONS termina antes e os rótulos da meia-noite diferem. Esse confronto corrobora compatibilidade atual de valores, mas não substitui o contrato de fuso/datum. `ceran-ons-same-clock-levels.csv` permite auditar todos os pares. Valores CERAN sem par não foram considerados divergências.

A última linha CERAN de Castro mostra montante **246,22 m às 17h**, acima do máximo **245,92 m** do recorte histórico ONS: há extrapolação potencial desse preditor mesmo com dados positivos/finitos. Não é critério de invalidade.

Para o experimento, atraso presumido de 60 min e expiração de 90 min são políticas de disponibilidade simulada, não latências comprovadas pelas páginas. Conservar hora original, hora de coleta e hipótese temporal. Não usar nível futuro contemporâneo ao alvo como preditor de uma emissão anterior, nem interpretar ganho retrospectivo como validação prospectiva.

## Entrega e verificação

`source-manifest.json` contém caminhos e SHA-256 dos 18 CSVs e três páginas. `ceran-collection-provenance.json` preserva as três entradas do manifesto da coleta original, com URLs/horários/hashes. `ceran-field-contract.json` mantém cabeçalhos e valores originais das páginas. Nenhum arquivo de origem foi alterado.

`nonfinite-zero-negative.csv` contém o único campo vazio; `duplicate-source-rows.csv` tem apenas cabeçalho por ausência de duplicatas. Os CSVs de saltos são listas de revisão, não máscaras de treino. `validation.json` registra reconciliação das contagens e hashes; `artifact-hashes.json` cobre esta entrega. Nenhum dado foi buscado da internet nesta rodada, nenhum volume foi convertido em armazenamento e nenhum candidato foi promovido.
