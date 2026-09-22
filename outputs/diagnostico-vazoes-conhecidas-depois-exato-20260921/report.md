# Diagnóstico com vazões conhecidas depois — não é previsão

**Estes resultados usam informações indisponíveis na emissão e não contam para a meta de 98%.** Servem somente para investigar a sensibilidade das previsões às estimativas de vazão de montante.

Mantivemos o nível de referência, alvos, âncoras, chuva, Carreiro histórico/proxies, estados HGE, roteamento e curva. Substituímos apenas os termos de vazão estimada com tempo relativo não negativo: Julho, Carreiro ou ambos. Inclusive o termo relativo zero pode estar indisponível na emissão por atraso de publicação.

## Contrato de observação e cobertura

Nos 1968 horários de julho–setembro, a conferência de Julho encontrou 82 sem timestamp ONS exato e 32 com valor diferente da grade de referência. Esses pontos ficaram indisponíveis para o diagnóstico; não receberam valores anteriores nem aproximação temporal.

A primeira execução usava a grade com retenção de leitura anterior e foi preservada como preliminar/superada em ../diagnostico-vazoes-conhecidas-depois-20260921/invalidation.json. Não sustenta uma conclusão sobre observações exatas.

A exigência de dados disponíveis em todos os quatro cenários reduz a amostra. Comparamos cada cenário com a referência na mesma interseção, sem apresentar a redução como ganho de cobertura. Métricas individuais e exclusões permanecem no CSV.

## Níveis de cheia — interseção dos quatro cenários

|Prazo|Cenário|N comum|Acertos ≤0,50 m|MAE (m)|Máximo (m)|
|---|---|---:|---:|---:|---:|
|1 h|Referência causal|225|207 (92.00%)|0.2078|1.3363|
|1 h|Julho conhecido depois|225|208 (92.44%)|0.2048|1.3303|
|1 h|Carreiro conhecido depois|225|207 (92.00%)|0.2078|1.3363|
|1 h|Ambos conhecidos depois|225|208 (92.44%)|0.2048|1.3303|
|6 h|Referência causal|133|50 (37.59%)|0.8959|4.1908|
|6 h|Julho conhecido depois|133|63 (47.37%)|0.6720|1.7625|
|6 h|Carreiro conhecido depois|133|48 (36.09%)|0.9159|4.1674|
|6 h|Ambos conhecidos depois|133|58 (43.61%)|0.6896|1.8454|
|12 h|Referência causal|81|22 (27.16%)|1.7218|9.0383|
|12 h|Julho conhecido depois|81|26 (32.10%)|1.0265|2.1455|
|12 h|Carreiro conhecido depois|81|24 (29.63%)|1.6508|8.9899|
|12 h|Ambos conhecidos depois|81|29 (35.80%)|0.9919|2.2129|

## O que o diagnóstico muda

Na interseção de 12 h/cheia (81 pares), trocar só a vazão de Julho reduz MAE de 1,722 para 1,027 m; trocar só Carreiro reduz para 1,651 m; ambos chegam a 0,992 m. Ainda sobram erros relevantes, apesar da informação extra. Portanto, aperfeiçoar apenas a estimativa de montante não basta neste recorte: também é necessário investigar a resposta que converte as vazões em nível, incluindo correção da âncora, curva, runoff local e entradas históricas.

A contribuição de cada fonte não é aditiva, e erros podem se compensar. No prazo de 6 h, usar o Carreiro conhecido depois piora o MAE de 0,896 para 0,916 m. Isso não prova defeito na medição nem que uma previsão pior de Carreiro é desejável.

Não é um limite superior teórico de precisão, modelo candidato, treino, teste independente ou previsão prospectiva. A interseção tem forte seleção por lacunas; 81 pares de prazos sobrepostos não representam 81 cheias independentes. Fuso, revisões e validade física das medições continuam sujeitos às ressalvas do acervo.

O próximo diagnóstico deve separar os termos de resposta do modelo sobre os casos em que há entradas completas, mantendo a comparação também nos dados operacionais. A meta e a tolerância de 0,50 m permanecem iguais.

## Verificação matemática

Foram recompostos roteamentos completos de Julho/Carreiro em seis origens e quatro cenários usando componentes HGE/residual de replay independente anterior: 288 comparações, 228 valores finitos e 60 ausências concordantes; diferença máxima 1,07e-14 m. A checagem não inverteu os níveis de referência. Não houve nova simulação HGE dos 23.538 casos. A suíte passou 119 testes.

A verificação adicional reconstituiu o vínculo ONS e todos os deltas da
série, com diferença máxima 9,09e-13 m³/s; valores e estados conferidos
em todas as 23.538 linhas. Carreiro foi confrontado com a grade ANA exata
preservada, sem nova leitura integral dos XMLs. O vínculo temporal e a
concordância de fonte restringem a amostra e não eliminam seleção por lacunas.
