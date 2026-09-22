# Radar: treino com entradas ausentes e avaliação completa

Referência e candidato foram ajustados no mesmo ambiente operacional atual, com os mesmos parâmetros, fontes e cortes. A única mudança no candidato foi permitir campos de níveis e variações ausentes no treino, usando o tratamento nativo das árvores. Isso inclui variações passadas de Muçum; o nível-base e o alvo de treino continuam obrigatórios.

A avaliação inclui todos os alvos agendados. A amostra antiga, que exigia os primeiros 24 campos preenchidos, e sua parte excluída são apresentadas separadamente.

## Todos os pares calculáveis, sem excluir ausência auxiliar

|Fase|Prazo|Recorte|Modelo|Pares|Acertos ≤0,50 m|MAE (m)|Falhas com alvo|
|---|---|---|---|---|---|---|---|
|validation|1|all|baseline|6479|6478 (99.98%)|0.0194|38|
|validation|1|all|candidate|6479|6478 (99.98%)|0.0218|38|
|validation|1|level_ge_7m|baseline|28|28 (100.00%)|0.0670|0|
|validation|1|level_ge_7m|candidate|28|28 (100.00%)|0.0670|0|
|validation|6|all|baseline|6472|6362 (98.30%)|0.0918|40|
|validation|6|all|candidate|6472|6316 (97.59%)|0.1008|40|
|validation|6|level_ge_7m|baseline|28|24 (85.71%)|0.2646|0|
|validation|6|level_ge_7m|candidate|28|24 (85.71%)|0.2594|0|
|validation|12|all|baseline|6466|5182 (80.14%)|0.3257|40|
|validation|12|all|candidate|6466|5223 (80.78%)|0.3290|40|
|validation|12|level_ge_7m|baseline|28|8 (28.57%)|0.7742|0|
|validation|12|level_ge_7m|candidate|28|8 (28.57%)|0.9251|0|
|test|1|all|baseline|1939|1933 (99.69%)|0.0371|5|
|test|1|all|candidate|1939|1932 (99.64%)|0.0341|5|
|test|1|level_ge_7m|baseline|236|230 (97.46%)|0.0853|1|
|test|1|level_ge_7m|candidate|236|230 (97.46%)|0.0775|1|
|test|6|all|baseline|1927|1759 (91.28%)|0.2096|12|
|test|6|all|candidate|1927|1745 (90.56%)|0.2083|12|
|test|6|level_ge_7m|baseline|236|154 (65.25%)|0.6237|1|
|test|6|level_ge_7m|candidate|236|147 (62.29%)|0.6010|1|
|test|12|all|baseline|1915|1296 (67.68%)|0.5144|18|
|test|12|all|candidate|1915|1338 (69.87%)|0.4873|18|
|test|12|level_ge_7m|baseline|236|75 (31.78%)|1.3995|1|
|test|12|level_ge_7m|candidate|236|86 (36.44%)|1.3408|1|

## Efeito da exclusão antiga no teste

|Prazo|Recorte|População|N|MAE referência|MAE candidato|Acertos referência|Acertos candidato|
|---|---|---|---|---|---|---|---|
|1|all|complete24|1350|0.0302|0.0286|1350|1350|
|1|all|missing24|589|0.0530|0.0467|583|582|
|1|level_ge_7m|complete24|144|0.0564|0.0498|144|144|
|1|level_ge_7m|missing24|92|0.1306|0.1209|86|86|
|6|all|complete24|1343|0.1794|0.1760|1239|1237|
|6|all|missing24|584|0.2792|0.2826|520|508|
|6|level_ge_7m|complete24|140|0.4111|0.3670|99|102|
|6|level_ge_7m|missing24|96|0.9338|0.9422|55|45|
|12|all|complete24|1337|0.4580|0.4228|935|969|
|12|all|missing24|578|0.6449|0.6364|361|369|
|12|level_ge_7m|complete24|140|1.0746|0.8916|53|62|
|12|level_ge_7m|missing24|96|1.8733|1.9957|22|24|

## Reprodução e limites

O primeiro ensaio foi interrompido ao detectar diferença com a previsão histórica arquivada. O ambiente antigo preservado (NumPy 2.0.2, scikit-learn 1.6.1) reproduziu exatamente as 1.350 previsões de uma hora; o atual (NumPy 2.5.3, scikit-learn 1.9.1) apresentou diferença máxima de 0,0908 m nesse horizonte. Variar 1/2/4 threads não alterou nenhum resultado dentro de cada ambiente. As acumulações meteorológicas construídas pelos dois procedimentos foram idênticas.

A nova comparação foi registrada após esse diagnóstico e antes de avaliar o candidato no teste. A referência atual é um novo ajuste, não a previsão arquivada. runtime-comparison.csv preserva todas as diferenças nos 16.113 pares antigos, por prazo; a diferença máxima ao longo dos 12 horizontes foi 1,1784 m. O ensaio interrompido e seus modelos parciais não foram substituídos.

As árvores mantêm os parâmetros por horizonte escolhidos anteriormente; portanto a fase chamada validation já participou da escolha e não é validação independente. O período test também foi previamente inspecionado. Nenhum resultado desta rodada certifica 98% prospectivos.

Os cortes originais foram preservados, inclusive a pequena exclusão de alvos que atravessam a fronteira de outubro no treino histórico. O runner operacional usa um corte único posterior. Não houve modificação do runner, emissão de nova previsão, mudança da automação, implantação ou promoção.

As faltas dos primeiros 24 campos incluem níveis e variações passadas de Muçum, Linha José Júlio, Linha Colombo e Passo Carreiro. Permitir NaNs não inventa observações e não recupera um nível-base ausente. Os atrasos e a disponibilidade das fontes históricas continuam hipóteses não certificadas.
