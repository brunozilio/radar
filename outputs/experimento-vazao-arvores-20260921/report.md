# Experimento de árvores para vazão de montante

Decisão: manter a referência. O modelo ridge venceu a seleção pela validação anterior para as duas fontes. Nenhum candidato foi promovido ou emitido como previsão nova.

Comparação fixa das famílias ridge, árvores para variação e árvores para nível, com as mesmas entradas históricas e cortes cronológicos. A escolha usa a média nos12prazos de MAE geral +0,5×MAE nas vazões altas, apenas na validação.

| Fonte | Período | Família | MAE geral | MAE vazões altas |
|---|---|---|---:|---:|
| julho | validation | ridge_reference | 81.98 | 285.24 |
| julho | validation | tree_delta | 62.40 | 344.84 |
| julho | validation | tree_level | 69.31 | 1070.21 |
| julho | test | ridge_reference | 169.23 | 437.99 |
| julho | test | tree_delta | 146.24 | 413.18 |
| julho | test | tree_level | 209.18 | 832.33 |
| carreiro | validation | ridge_reference | 13.53 | 77.69 |
| carreiro | validation | tree_delta | 10.07 | 101.51 |
| carreiro | validation | tree_level | 11.76 | 178.47 |
| carreiro | test | ridge_reference | 29.68 | 78.21 |
| carreiro | test | tree_delta | 23.13 | 84.56 |
| carreiro | test | tree_level | 35.79 | 151.73 |

Vazões e erros em m³/s; agregados ponderados pela quantidade de pares, nos prazos0–11h. Vazão alta significa percentil95 histórico da própria fonte antes de01/10/2025, não o critério de cheia de Muçum. Pares correlacionados não são eventos independentes.

As árvores de variação melhoraram o MAE de vazões altas de14deJulho no período de desenvolvimento seguinte, mas pioraram a validação e não repetiram a melhora em Carreiro. Selecioná-las pelo teste depois de vê-lo seria usar esse período no desenvolvimento. Julho–setembro/2026 já foi examinado e não representa nova validação independente.

O ridge desta comparação usa as entradas históricas congeladas das15h; não é uma reprodução do ajuste horário ativo. Os diagnósticos atuais usam o snapshot17h recebido na coleta17:27. Valores futuros calculados pelas árvores não são prova de acerto.

Os arquivos guardam parâmetros, hashes e código do experimento. As árvores não foram serializadas; qualquer candidato futuro precisa ser treinado novamente e registrado antes da emissão. A única âncora aplicada em prazo0 foi14deJulho, cuja leitura das17h consta em idades-fontes.csv; Carreiro não tinha leitura na mesma hora. Nenhum resultado comprova a meta98%.
