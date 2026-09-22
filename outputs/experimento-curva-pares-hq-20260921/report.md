# Curva de vazão–nível ajustada somente com pares H/Q válidos

A nova curva não trouxe ganho consistente na previsão e não foi promovida. Foram preservados os modelos operacionais, a tolerância de 0,50 m e a população de alvos.

## Mudança isolada

A curva anterior havia sido ajustada somente nas linhas com toda a matriz de roteamento completa. Chuva ou vazão de outra estação ausente excluía um par H/Q válido de Muçum. O candidato usa os pares finitos H/Q, mantendo a mesma forma de potência, inicialização, limites, objetivo soft_l1 e cortes de treino. Nenhum hiperparâmetro foi procurado.

|Fase|Amostra|Pares de treino|Treino com nível ≥7 m|
|---|---|---:|---:|
|validation|original_membership|3025|100|
|validation|all_paired_hq|4373|228|
|test|original_membership|8880|128|
|test|all_paired_hq|10890|256|

## Conversão usando vazão reportada conhecida

Este quadro mede somente a aproximação H(Q), usando Q reportada no mesmo horário. Não mede capacidade de prever vazão, nível futuro ou independência física entre as medições.

|Período|Amostra|Recorte|N|MAE da conversão (m)|
|---|---|---|---:|---:|
|validation|original_membership|all|6517|0.0358|
|validation|original_membership|high|28|0.2057|
|validation|all_paired_hq|all|6517|0.0390|
|validation|all_paired_hq|high|28|0.1391|
|test|original_membership|all|1944|0.0895|
|test|original_membership|high|236|0.2518|
|test|all_paired_hq|all|1944|0.0858|
|test|all_paired_hq|high|236|0.2590|

A curva ampliada reduziu o MAE de conversão na cheia da validação (0,206→0,139 m), mas piorou na cheia do teste (0,252→0,259 m). Os pares H/Q do teste não entraram no ajuste. Os períodos, porém, já foram examinados durante o desenvolvimento, portanto não são novos testes independentes.

## Aplicação às previsões com os demais componentes fixos

A vazão calculada pelo HGE foi preservada; mudou apenas a curva e o offset calculado com a mesma âncora. Chuva, roteamento, estados, parâmetros, estimativas de montante e correção residual de vazão permaneceram iguais. Parâmetros HGE antes ajustados com a curva antiga podem incorporar compensações; isto é um teste isolado de conversão, não recalibração hidráulica completa.

|Prazo|N na cheia|Acertos anteriores|Acertos novos|MAE anterior (m)|MAE novo (m)|
|---|---:|---:|---:|---:|---:|
|1 h|235|216|217|0.2094|0.2091|
|2 h|235|174|174|0.3389|0.3392|
|3 h|235|155|153|0.4570|0.4579|
|4 h|235|138|138|0.5636|0.5650|
|5 h|235|131|128|0.6634|0.6658|
|6 h|235|115|114|0.7579|0.7606|
|7 h|235|108|105|0.8392|0.8431|
|8 h|235|95|95|0.9218|0.9263|
|9 h|235|92|90|1.0328|1.0383|
|10 h|235|88|88|1.1328|1.1386|
|11 h|235|85|85|1.2452|1.2510|
|12 h|235|71|71|1.3752|1.3815|

## Decomposição algébrica da referência

Com Q do alvo disponível, o erro de nível é a soma exata de: diferença de nível associada às vazões pela curva adotada; e diferença entre o resíduo H–Q da âncora e o do alvo. Os termos podem se compensar; seus erros absolutos médios não são parcelas aditivas do erro total.

|Prazo|Pares de cheia com Q do alvo|MAE total (m)|MAE associado às vazões (m)|MAE da diferença de resíduos H–Q (m)|
|---|---:|---:|---:|---:|
|1 h|234|0.2062|0.1929|0.0261|
|6 h|234|0.7455|0.6716|0.1126|
|12 h|234|1.3697|1.2575|0.1967|

A decomposição tem 23.091 pares: perdeu 12 linhas relativas ao alvo de 22/07 às 17h, nível 18,95 m, por falta de Q do alvo na grade. Essas linhas permanecem na comparação das previsões; apenas o diagnóstico algébrico fica indisponível. O alvo de cheia ausente deve impedir interpretar a decomposição como amostra completa.

VazaoFinal é a vazão reportada pela ANA. O acervo não prova que seja medição independente de nível nem documenta sua derivação operacional em 2025–2026. Logo os termos não são erros físicos puros. O primeiro reúne efeitos de vazão prevista, propagação e escoamento local; o segundo pode refletir curva, referência, revisão ou dependência H/Q.

Este diagnóstico não elimina incerteza de referência vertical, fuso e revisões. O próximo trabalho deve priorizar os termos que geram a vazão de Muçum e sua correção temporal, preservando o controle atual. Não cabe trocar a curva só pelo ganho pontual de um prazo.

## Verificações

A suíte passou 121 testes. A auditoria independente passou 51 verificações,
sem refazer o ajuste: fronteiras e custos conferidos; parâmetros do controle
a até 6,10e-11 dos preservados; Q prevista e aplicação da nova curva com
diferença máxima 0; identidade da decomposição até 7,11e-15 m. Nenhuma
verificação numérica transforma este desenvolvimento em prova prospectiva.
