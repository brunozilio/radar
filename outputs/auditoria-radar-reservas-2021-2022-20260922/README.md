# Auditoria independente — primeira avaliação reservada de 2021/2022

Passaram 871 verificações: 24 modelos fixos, 48 aplicações, 26.340 linhas agendadas, 156 exclusões de fronteira e 432 métricas recalculadas. Os 153 hashes de entradas e as referências dos modelos, treino e helpers conferem. Nenhum treino ou ajuste foi executado.

Ordem registrada: protocolo 2026-09-22T03:13:34.125356+00:00; entradas congeladas 2026-09-22T03:29:03.358072+00:00; inferência 2026-09-22T03:29:09.860149+00:00 até 2026-09-22T03:29:11.322655+00:00. Os arquivos e a ligação entre manifestos conferem. Esta evidência local não é prova de toda computação anterior fora do escopo.

A matriz reconstruída independentemente reproduziu exatamente 34 aplicações. Em 14 aplicações, diferenças de chuva da ordem de 1e-13 atravessaram limiares das árvores e alteraram 203 previsões. A matriz ORIGINAL congelada reproduziu exatamente todas as previsões dessas 14 aplicações; nenhum valor foi alterado ou arredondado.

O rastreamento identificou 253 divergências de caminho, todas em preditores de chuva; a soma das diferenças das folhas reproduz cada diferença de previsão até 1e-12. Maior diferença: 0,029309652 m, candidato h4, origem 29/05/2022 23h (11,945531397 m congelado versus 11,916221746 m reconstruído). Casos e limiares estão em threshold-sensitivity.csv e tree-threshold-crossings.csv. Isto limita qualquer alegação de equivalência exata sob outra implementação numérica.

| Período | h | Acertos controle→candidato / alvos ≥7 m | MAE (m) | Máximo (m) |
|---|---:|---:|---:|---:|
| 2021 | 1 | 11→11/11 | 0.049012→0.060751 | 0.136993→0.143373 |
| 2021 | 6 | 8→9/11 | 0.347436→0.234912 | 0.755541→0.627428 |
| 2021 | 12 | 6→10/11 | 0.461953→0.264860 | 0.745555→0.615673 |
| 2022 | 1 | 307→310/312 | 0.073907→0.065192 | 1.108535→0.982939 |
| 2022 | 6 | 194→218/312 | 0.640565→0.471371 | 3.742340→2.972566 |
| 2022 | 12 | 147→120/312 | 1.027166→1.063000 | 5.816917→4.877715 |
| pooled | 1 | 318→321/323 | 0.073057→0.065041 | 1.108535→0.982939 |
| pooled | 6 | 202→227/323 | 0.630552→0.463294 | 3.742340→2.972566 |
| pooled | 12 | 153→130/323 | 1.007857→1.035734 | 5.816917→4.877715 |

No recorte de cheia, o candidato ganha acertos em 7 horizontes e perde em 2 em 2021 (3 empates); em 2022 ganha em 8 e perde em 4. O resultado agregado ganha em 9 e perde em 3. O conjunto geral agregado melhora acertos nos 12 horizontes, mas isso não elimina as regressões de cheia: em 2022/h12, 147→120 acertos e MAE 1,027166→1,063000 m. Não há domínio geral ou promoção.

Todos os 11 alvos de cheia de 2021 têm previsão; em 2022 são 312 alvos e 311 pares por horizonte, com uma falha mantida no denominador. Há 323 alvos de cheia agregados, 322 pares e uma falha. Alvos desconhecidos não viram acertos. Todas as linhas têm falta em algum dos primeiros 24 campos: complete24 é vazio e missing24 coincide com full_schedule. A ausência auxiliar não criou filtro adicional.

Limites: os modelos foram ajustados com dados de 2025/26, portanto este teste mede transferência retrospectiva a janelas reservadas, não previsões que poderiam ser emitidas com somente o treino disponível em 2021/22. Amostras horárias são correlacionadas; 11/312 alvos não representam esse número de eventos independentes. Fuso, datum e disponibilidade histórica permanecem pressupostos. O teste não cumpre a meta prospectiva de 98%. Se estes resultados orientarem ajustes futuros, as janelas passam a desenvolvimento e não podem ser reapresentadas como teste novo independente.

Diagnóstico de classificação: as 203 células de previsão alteradas correspondem a 191 origens distintas e 190 timestamps-alvo distintos; não são uma contagem de eventos. Todas têm truth finita. Nenhuma muda a classificação |erro|≤0,50 m (zero acerto→erro e zero erro→acerto), no geral ou no recorte ≥7 m, em cada família/ano/horizonte. Os 96 grupos estão em hit-sensitivity-groups.csv; os 203 casos em hit-sensitivity-cases.csv. Isto não torna a diferença automaticamente tolerável nem apaga a sensibilidade de reprodução. As métricas primárias permanecem intocadas.
