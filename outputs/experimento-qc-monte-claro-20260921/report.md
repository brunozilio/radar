# Sensibilidade aos zeros suspeitos de Monte Claro

Apenas experimento retrospectivo: não houve promoção, nova emissão ou modificação do histórico original. A política foi registrada antes do cálculo em docs/monte-claro-input-qc-experiment.json.

Foram comparadas a entrada original, somente Q ausente e Q/I ausentes nas janelas auditadas de22/07/2026. São12slots deQ e8deI; suas diferenças temporais afetam nove origens horárias. Valores ausentes recebem o tratamento já existente do ridge: mediana e indicadores calculados somente no treinamento. Nenhum valor real de substituição foi inventado.

| Fonte | Variante | MAE geral | MAE vazões altas | MAE nas origens afetadas | Diagnóstico atual11h |
|---|---|---:|---:|---:|---:|
| julho | original | 169.23 | 437.99 | 3950.39 | 13418.35 |
| julho | Q_missing | 158.94 | 363.41 | 1704.63 | 13804.33 |
| julho | QI_missing | 153.32 | 322.73 | 479.78 | 13506.23 |
| carreiro | original | 29.68 | 78.21 | 265.65 | 1659.16 |
| carreiro | Q_missing | 29.34 | 78.53 | 202.96 | 1705.30 |
| carreiro | QI_missing | 29.11 | 78.91 | 158.71 | 1678.24 |

Valores em m³/s. MAE agregado nos prazos0–11h, ponderado pela quantidade de pares. Vazões altas usam o percentil95 da fonte anterior a01/10/2025; não são o critério de cheia de Muçum. Cada fonte tem108pares nas origens afetadas: nove origens ×12prazos, altamente correlacionados e pertencentes a um único episódio.

Em14deJulho, a retirada dos zeros das entradas reduz bastante os erros nesse episódio. EmCarreiro, melhora nas nove origens afetadas convive com pequena piora no subconjunto de vazões altas. A limpeza também não resolve a extrapolação do diagnóstico atual:14deJulho em11h permanece acima de13mil m³/s.

A validação anterior a01/07/2026 permanece idêntica, assim como todos os alvos e as previsões fora das origens afetadas no teste. O treinamento final, que inclui julho, muda seus coeficientes e por isso modifica também o diagnóstico atual. A referência original reproduz o experimento anterior com erro inferior a1e-8m³/s. Modelos finais, código, política e hashes foram preservados.

Limitações: as datas anômalas foram identificadas retrospectivamente. Julho–setembro/2026 é um período de desenvolvimento já examinado. Os resultados medem sensibilidade a uma entrada suspeita; não demonstram melhoria prospectiva nem98% de acerto do nível do rio. A máscara por data não deve entrar na operação. É necessário definir uma regra geral a partir da semântica da fonte e avaliá-la em outros eventos, sem selecionar exclusões pelos erros dos modelos. A série atual deCastroAlves não foi invalidada por exceder os máximos históricos.
