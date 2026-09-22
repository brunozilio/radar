# Diagnóstico do candidato Carreiro por cheia

Foram mantidas as regras anteriores de tendência e agrupamento. Todos os 23.538 alvos/origens permanecem no diagnóstico; os alvos finitos conferem com as fontes aprovadas. As quatro cheias são agrupamentos observados, ainda sem certificação de independência; duas têm lacunas. Este relatório usa períodos históricos já examinados.

## Resultados de 12 h do candidato com níveis das usinas

| Início do agrupamento (UTC) | Pares/observações | Acertos ±0,50 m | MAE | Maior erro |
|---|---:|---:|---:|---:|
| 2026-07-02T23:30:00+00:00 | 35/35 | 26 (74.29%) | 0.351 m | 1.140 m |
| 2026-07-22T01:00:00+00:00 | 133/135 | 18 (13.53%) | 2.006 m | 9.038 m |
| 2026-08-13T08:30:00+00:00 | 49/49 | 17 (34.69%) | 0.694 m | 1.243 m |
| 2026-08-31T08:15:00+00:00 | 18/18 | 10 (55.56%) | 0.562 m | 1.565 m |

## O que a recuperação de entradas resolveu

A cheia que começa em 02/07 às 20h30 BRT tinha zero previsões calculáveis no experimento anterior. Agora há 35 pares por horizonte: 35/35 acertos em 6 h, mas somente 26/35 em 12 h. Isso evidencia utilidade de cobertura, sem demonstrar a meta em todos os prazos ou eventos.

Na maior cheia, iniciada em 21/07 às 22h BRT, a cobertura de 12 h sobe de 121/135 para 133/135 pares. A precisão continua baixa: 18/133 acertos, MAE de 2,006 m e erro máximo de 9,038 m. O pequeno viés médio (+0,161 m) mascara erros grandes de sinais opostos; subtrair esse viés não resolve o problema principal.

Os erros anteriormente calculáveis não mudaram. As métricas de pares anteriores, novos e ainda ausentes estão em `cluster-population-metrics.csv`. Não selecionar apenas a cheia ou prazo com 100% de acertos.

## Direção do próximo diagnóstico

O maior erro de 12 h está listado abaixo; a tabela completa permanece preservada para não esconder os demais. A próxima análise deve separar erro de previsão de vazão a montante, propagação e transformação vazão–nível, usando sensibilidades apenas como diagnóstico. Não trocar previsões históricas por vazões futuras observadas no placar.

- Origem 2026-07-22T09:00:00-03:00, alvo 2026-07-22T21:00:00-03:00: observado 17.790 m, previsto 8.752 m, erro -9.038 m; população previously_paired.
- Origem 2026-07-22T08:00:00-03:00, alvo 2026-07-22T20:00:00-03:00: observado 18.110 m, previsto 9.084 m, erro -9.026 m; população previously_paired.
- Origem 2026-07-22T11:00:00-03:00, alvo 2026-07-22T23:00:00-03:00: observado 17.040 m, previsto 25.494 m, erro +8.454 m; população previously_paired.

As contagens e erros médios recompõem as métricas gerais (diferença máxima 4.44e-16 m). A suíte passou 90 testes, incluindo rejeição de previsões cujo hash não confere. Nenhuma alteração de modelo em uso, promoção ou alcance da meta foi declarado.
