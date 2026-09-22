# Correção autorregressiva do resíduo de vazão

12 modelos ridge com alpha 1000 fixo, quatro resíduos anteriores à origem e alvos de treino estritamente anteriores a julho/2026. Avaliação histórica de desenvolvimento já inspecionada. Nenhuma promoção.

|Prazo|Recorte|Modelo|N|Acertos ≤0,50 m|MAE (m)|Falhas com alvo|
|---|---|---|---|---|---|---|
|1|all|baseline|1938|1891 (97.57%)|0.1383|6|
|1|all|candidate|1938|1893 (97.68%)|0.1285|6|
|1|level_ge_7m|baseline|235|216 (91.91%)|0.2094|2|
|1|level_ge_7m|candidate|235|223 (94.89%)|0.1757|2|
|6|all|baseline|1926|1458 (75.70%)|0.3641|13|
|6|all|candidate|1926|1425 (73.99%)|0.3573|13|
|6|level_ge_7m|baseline|235|115 (48.94%)|0.7579|2|
|6|level_ge_7m|candidate|235|129 (54.89%)|0.6597|2|
|12|all|baseline|1914|1159 (60.55%)|0.5579|19|
|12|all|candidate|1912|1227 (64.17%)|0.5271|21|
|12|level_ge_7m|baseline|235|71 (30.21%)|1.3752|2|
|12|level_ge_7m|candidate|235|89 (37.87%)|1.2436|2|

As métricas acima usam a amostra individual: no horizonte de 12 horas o candidato perde duas previsões por vazão negativa. evaluation.csv também preserva a comparação na amostra comum, sem eliminar as falhas da cobertura.

Contagens por família: {'reference': {'candidate_applied': 23019, 'baseline_missing': 288, 'fallback_original_tau6': 228, 'invalid_candidate_flow': 3}, 'julho_levels': {'candidate_applied': 23019, 'baseline_missing': 288, 'fallback_original_tau6': 228, 'invalid_candidate_flow': 3}}.

O alvo aprendido é Q reportada menos uma reconstrução com chuva e montante posteriormente conhecidos. Ele não é o erro completo da previsão emitida. Ao aplicar a correção a vazões previstas, os erros de montante e chuva permanecem.

Os componentes congelados foram ajustados no período anterior a julho e os resíduos de treino são internos a esse ajuste, não previsões fora de amostra. O teste posterior não entra no ajuste ridge, mas já havia sido examinado em outras experiências.

“Finalizado” indica uma reconstrução retrospectiva, não dados exclusivamente observados: a chuva inclui preenchimento da área sem cobertura com previous_day1, e o montante usa a grade histórica existente e proxy regional Carreiro para lacunas. Esses efeitos também entram nos estados anteriores. A ressalva pós-revisão está preservada em documentation-clarification.json; protocolo e código executados permanecem intactos.

Três vazões corrigidas negativas por família foram mantidas como falhas (11 horas: uma; 12 horas: duas). Não houve corte em zero nem fallback escolhido pelo sinal. Entradas residuais ausentes retornam exclusivamente à correção original; entradas-base ausentes permanecem ausentes.

A âncora foi reproduzida com diferença zero em todas as linhas comparáveis. 126 testes passaram, incluindo exclusão de labels no corte, invariância a resíduos futuros e preservação do fallback/falha. Esses testes não comprovam 98% prospectivos.
