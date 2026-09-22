# Verificação independente — resíduo autorregressivo

O verificador local `verify.py` não importa o pipeline, não refaz ajustes e não executa o HGE. Confere os artefatos de `outputs/experimento-residuo-autoregressivo-20260921` e as fontes preservadas. Resultado e tolerâncias individuais estão em `verification.json`.

Foram conferidos hashes de entradas/saídas, cópias do código e protocolo, identidade das 23.538 linhas/alvos/âncoras, grade horária, associação exata à vazão ANA bruta, soma independente do roteamento com lags positivos e exclusão apenas de pesos exatamente zero, substituição Carreiro somente quando ausente, identidade dos resíduos finalizados usando a descarga HGE preservada e alinhamento das quatro features.

Para cada horizonte 1–12, o verificador reconstrói a população de treino completa e finita, com alvo estritamente anterior a 01/07/2026 00:00 UTC−3. Confere contagens, último alvo/origem, médias, desvios, intercepto e equações normais ridge alpha1000 sem resolver novamente o ajuste. A inferência independente usa os coeficientes gravados. O corte é aplicado ao alvo, portanto também exclui origens pré-corte cujo alvo ultrapasse a fronteira.

As previsões baseline e seus componentes reproduzem o experimento tau6. A correção nova substitui a exponencial uma única vez, mantendo curva, offset e vazão sem correção. Cada família conserva **23.019 candidatos aplicados, 228 fallbacks exatamente iguais ao baseline, 288 baselines ausentes e 3 falhas por vazão corrigida negativa**. As 147 linhas sem alvo observado continuam contendo previsão; o alvo não decide a inferência. `negative-candidate-flows.json` conserva os seis registros no total, identificados por família, com valores e origens.

## Limites da verificação e do experimento

- O HGE não foi repetido aqui. A parcela `local_q` foi lida do NPZ preservado; o código foi revisado e a âncora comparada ao baseline. O responsável pela execução fez separadamente o teste de prefixo de estado, preservado em `state-prefix-verification.json`.
- Os resíduos pré-julho são in-sample aos componentes congelados e ajustados nesse período. Não são previsões fora de amostra emitidas historicamente.
- Os labels usam valores futuros em relação à origem, legitimamente como alvos de treino. Eles removem a parcela explicada por montante/chuva posteriormente conhecidos; não treinam diretamente o erro total da previsão emitida.
- A chuva finalizada inclui complemento de cobertura espacial por previsão arquivada. O roteamento usa a grade existente, que pode conter asof, e estimativas Carreiro onde faltam vazões. Evitar descrever o alvo como reconstrução exclusivamente observada ou composta apenas de registros exatos.
- Horários nominais e atrasos presumidos não certificam disponibilidade histórica, fuso do serviço legado ou continuidade do datum. Vazão ANA reportada não foi demonstrada independente do nível.
- `residual_model_applied=true` significa correção computável: as três falhas de vazão negativa também têm esse indicador. Para aplicação efetiva use o status de cada família. Não houve casos de indicador verdadeiro com baseline ausente nesta execução.
- Não há promoção, inferência operacional ou comprovação da meta de 98%. Não foram calculadas métricas principais nesta revisão; julho–setembro continua desenvolvimento já inspecionado.

Reprodução: `PYTHONDONTWRITEBYTECODE=1 /tmp/radar-hge-venv/bin/python outputs/verificacao-residuo-autoregressivo-20260921/verify.py`. Só os artefatos desta verificação são escritos. Nenhuma fonte, protocolo ou resultado original é modificado.
