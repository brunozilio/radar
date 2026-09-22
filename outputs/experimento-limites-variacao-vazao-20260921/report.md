# Limites estatísticos nas variações de vazão

Foram ajustados 48 modelos novos e reutilizados 48 modelos congelados. Os dois candidatos usam exatamente os mesmos 197.206 pares por família, sem eliminar os extremos. A referência foi reproduzida com diferença máxima de 0 m³/s.

O candidato limita somente 21 variáveis de mudança de vazão aos percentis 0,5 e 99,5 do treino de cada fonte/prazo. As vazões conhecidas, a chuva, os níveis e suas variações permanecem intactos. Esses limites controlam a influência estatística; não são limites físicos nem identificam automaticamente dados incorretos.

## Resultados

MAE agregado ponderado pelo número de pares, em m³/s. Contagens somadas entre prazos contêm alvos repetidos; não são eventos independentes.

| Fonte | Período | Modelo | MAE geral | MAE vazões altas |
|---|---|---|---:|---:|
| julho | validation | level_and_slopes | 70.50 | 266.58 |
| julho | validation | level_clipped_flow_changes | 72.07 | 277.63 |
| julho | test | level_and_slopes | 142.36 | 396.03 |
| julho | test | level_clipped_flow_changes | 131.69 | 315.62 |
| carreiro | validation | level_and_slopes | 12.88 | 79.18 |
| carreiro | validation | level_clipped_flow_changes | 13.22 | 73.66 |
| carreiro | test | level_and_slopes | 29.49 | 77.33 |
| carreiro | test | level_clipped_flow_changes | 28.40 | 81.84 |

Para Julho, o erro em vazões altas no período de teste caiu de 396,03 para 315,62 m³/s, mas na validação anterior piorou de 266,58 para 277,63 m³/s. Para Carreiro, a validação em vazões altas melhorou, mas o teste piorou de 77,33 para 81,84 m³/s. Todos os prazos e vieses permanecem em `evaluation.csv`.

## Decisão

**Não promover.** A melhoria localizada no período motivador do diagnóstico não se sustentou nos dois períodos. Não foi feito ajuste dos percentis após ver os resultados. O teste continua sendo desenvolvimento em períodos já examinados, sem prova independente ou prospectiva. Não foi declarado ganho no nível de Muçum: isso exigiria avaliação da cadeia completa.

Todos os parâmetros de transformação estão em `transforms.json`, com corte temporal e quantidade de entradas alteradas. Medições, previsões anteriores e rotina horária foram preservadas. A suíte passou 93 testes, incluindo isolamento dos limites em relação a valores futuros e preservação de variáveis não selecionadas/ausências.
