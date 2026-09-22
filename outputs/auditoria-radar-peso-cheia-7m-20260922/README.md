# Auditoria dos pesos de treino ≥7m

Etapa anterior à inspeção do candidato: **284 verificações passaram**. As 24 máscaras do experimento misto foram reconstruídas com os cortes, admissibilidade, bases e atribuição PCG64(57) preservados. Não houve ajuste, inferência ou rede.

Trocar `target>=9` por `target>=7` aumenta o peso **exatamente em 2** nas amostras de alvo em `[7,9)`. Abaixo de7 e a partir de9, os pesos são idênticos. Nos casos intermediários com `abs(delta)>=1`, o peso passa de3 para5; nos demais, de1 para3. Nenhum alvo/base/resposta ou linha foi alterado. Os casos exatamente7 entram no incremento; os exatamente9 já recebiam o peso alto original.

| Fase de treino | h | Linhas | alvo <7 | alvo [7,9) | alvo ≥9 | Soma dos pesos original → esperada |
|---|---:|---:|---:|---:|---:|---:|
| validation | 1 | 3530 | 3373 | 59 | 98 | 3742 → 3860 (+118) |
| validation | 6 | 3520 | 3361 | 61 | 98 | 4332 → 4454 (+122) |
| validation | 12 | 3513 | 3347 | 64 | 102 | 4909 → 5037 (+128) |
| test | 1 | 9298 | 9113 | 84 | 101 | 9524 → 9692 (+168) |
| test | 6 | 9279 | 9092 | 86 | 101 | 10701 → 10873 (+172) |
| test | 12 | 9269 | 9075 | 89 | 105 | 11749 → 11927 (+178) |

As fases acima identificam os cortes dos modelos, não o uso de seus alvos de avaliação no treino. `expected-training-weights.csv` traz os 24 grupos, contagens das fronteiras exatas e hashes. `expected-training-vectors.npz` guarda índices, respostas e os dois vetores de peso para a auditoria posterior. Os hashes do pai foram verificados sem mutação.

As mesmas origens reaparecem entre horizontes/fases; não somar as contagens como observações independentes. **7m é definição analítica, não declaração de limiar oficial de alerta.** Alterar pesos relativos pode mudar toda a função ajustada, não apenas previsões em cheia; o incremento não demonstra melhora.

## Auditoria do candidato concluído

**2.917 verificações adicionais passaram**, sem divergência concreta. Os 48 vetores pareados salvos (antigo/novo em 24 máscaras) coincidem exatamente com os vetores esperados preservados na etapa preliminar. Índices, ordem, respostas, contagens por faixa, somas e hashes dos pesos conferem. Nas 24 máscaras, as configurações completas HGB, 180 campos e 180 iterações foram preservados. As únicas alterações declaradas do ajuste são os pesos adicionais nas amostras em `[7,9)`; nenhuma característica, base, alvo ou linha foi acrescentada.

O protocolo preservado tem SHA-256 `1f8ccf42085b3c3430aa9c7efe03b49eb4ddf7dcf90cb688ce156ebb7355c35c`. Os horários registrados de protocolo/pré-fit/conclusão estão ordenados. O manifesto pré-fit inclui os hashes do plano e dos vetores pareados. Manifestos, código executado, runtime e fontes foram conferidos, inclusive integridade ao final. Os horários são metadados locais, não atestação independente do início do otimizador.

Reaplicados 24 candidatos nos dois perfis: **48 aplicações exatas**. Reaplicados os 72 modelos parent nos dois perfis: **144 aplicações exatas**. As entradas de avaliação são as matrizes originais intactas; as 204.168 linhas preservam todos os campos anteriores. São duas vistas das mesmas 102.084 origens/horizontes, não observações independentes.

Recalculadas as **1.152 métricas** das quatro famílias, duas fases, dois perfis, 12 horizontes, três populações e dois recortes. As 864 métricas dos controles são idênticas ao pai. Valores numéricos conferiram com tolerância absoluta de 10⁻¹², contagens exatamente. Alvos desconhecidos permanecem separados; previsões ausentes para alvos conhecidos contam como falhas no denominador observado. Cada grupo alto de test tem 237 alvos conhecidos, 236 pares e uma falha; validation tem28 pares/alvos.

## Ganhos e regressões

Contra o modelo misto anterior, os acertos de cheia/test ganham/empatam/perdem em 6/2/4 horizontes A e 6/4/2 B. Em validation, são 2/5/5 A e 1/5/6 B. Isso não demonstra domínio nem sustenta promoção.

| Cheia/test | Acertos misto → candidato | MAE misto → candidato |
|---|---:|---:|
| A, 6h | 170 → 166 / 237 | 0,602111 → 0,606535 m |
| B, 6h | 166 → 169 / 237 | 0,635535 → 0,640608 m |
| A, 12h | 75 → 67 / 237 | 1,328673 → 1,341347 m |
| B, 12h | 75 → 68 / 237 | 1,384912 → 1,392254 m |

Na verificação suplementar solicitada, os quatro grupos de teste12h `[7,9)` foram reconstruídos diretamente das previsões. Os acertos caem de **44 para39 /120** em A e de **49 para40 /120** em B. As contagens e erros coincidem com `level-band-metrics.csv`. Aumentar os pesos dessas amostras no treino não garantiu melhora nessa faixa de avaliação. A associação observada não identifica um mecanismo causal único. Não foi ampliada a auditoria para todas as métricas/transições secundárias por faixa.

## Limites e reprodução

O arquivo HGB salvo não contém prova interna de todos os pesos/amostras efetivamente consumidos pelo ajuste. A evidência delimitada é a reconstrução independente, vetores pareados salvos antes do fit, código executado, hashes/metadados e reaplicação exata. Não foi feito refit nem escolhido outro peso/limiar/seed. Todas as janelas já foram inspecionadas como desenvolvimento, e os perfis são vistas pareadas. Fuso, datum, publicação histórica e independência dos episódios não são certificados por este teste.

`audit.py` verifica o candidato e controles sem importar o runner operacional; `check_band.py` verifica os quatro grupos suplementares sem inferência. `finalize.py` confere os hashes e grava o manifesto próprio, excluindo-o de si mesmo. Os artefatos preliminares de expectativa foram preservados. Não houve rede, promoção, emissão ou mudança operacional; a meta não foi atingida. Esta entrega está finalizada e estável; não reexecutar após congelamento externo sem autorização.
