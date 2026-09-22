# Sensibilidade à idade da leitura de Muçum

Comparação histórica de 15, 30 e 45 minutos. Não houve promoção ou ajuste de parâmetros.

Cada cenário preserva 23538 pares origem/alvo. Amostra comum aos três: 23079.

## Julho com níveis de reservatório — amostra comum

|Prazo|Recorte|Idade (min)|N|Acertos ≤0,50 m|MAE (m)|Máximo (m)|
|---|---|---|---|---|---|---|
|1 h|all|15|1936|1889 (97.57%)|0.1383|1.3363|
|1 h|all|30|1936|1848 (95.45%)|0.1621|1.6007|
|1 h|all|45|1936|1798 (92.87%)|0.1847|1.9330|
|1 h|level_ge_7m|15|235|216 (91.91%)|0.2094|1.3363|
|1 h|level_ge_7m|30|235|204 (86.81%)|0.2431|1.6007|
|1 h|level_ge_7m|45|235|189 (80.43%)|0.2756|1.9330|
|6 h|all|15|1924|1456 (75.68%)|0.3641|4.1908|
|6 h|all|30|1924|1453 (75.52%)|0.3659|4.2015|
|6 h|all|45|1924|1458 (75.78%)|0.3672|4.2194|
|6 h|level_ge_7m|15|235|115 (48.94%)|0.7579|4.1908|
|6 h|level_ge_7m|30|235|115 (48.94%)|0.7700|4.2015|
|6 h|level_ge_7m|45|235|114 (48.51%)|0.7793|4.2194|
|12 h|all|15|1912|1157 (60.51%)|0.5582|9.0383|
|12 h|all|30|1912|1156 (60.46%)|0.5585|9.0469|
|12 h|all|45|1912|1158 (60.56%)|0.5583|9.0599|
|12 h|level_ge_7m|15|235|71 (30.21%)|1.3752|9.0383|
|12 h|level_ge_7m|30|235|71 (30.21%)|1.3816|9.0469|
|12 h|level_ge_7m|45|235|72 (30.64%)|1.3832|9.0599|

As métricas completas dos dois modelos e de todos os prazos estão em metrics.csv; cobertura e transições são separadas.

Amostras individuais podem mudar por lacunas da âncora. A interseção reduz esse efeito na comparação de erros, mas não elimina o viés de seleção nem certifica disponibilidade histórica.

A idade efetivamente disponível deve determinar a leitura operacional. Escolher retroativamente o atraso de melhor resultado seria seleção de cenário, não ganho demonstrado.

Os demais atrasos e as previsões meteorológicas ficam fixos. Dados revistos não reproduzem o histórico de publicação. Estes resultados não comprovam a meta prospectiva de 98%.

## Verificação e conclusão

O cenário de 15 minutos reproduziu exatamente 46.500 valores finitos da
experiência anterior, além das mesmas lacunas e estados. Os três cenários
preservam proxies e insumos; 162 verificações independentes passaram.
Foram conferidas 1.152 métricas individuais contra as avaliações originais,
sem diferença. Em seis origens, os termos alterados da correção foram
recalculados sobre componentes de um replay independente: 216 comparações,
diferença máxima de 1,07e-14 m. A suíte passou 110 testes.

Na amostra comum de cheias de 1 h, a leitura mais antiga aumentou o MAE de
0,2094 para 0,2431 e 0,2756 m. O erro máximo aumentou de 1,3363 para
1,6007 e 1,9330 m. Em 12 h, o MAE foi 1,3752/1,3816/1,3832 m; o atraso
da âncora sozinho não explica a maior parte do erro longo neste experimento.
Nenhum cenário satisfaz os critérios completos da meta. O próximo trabalho
de melhoria deve considerar simultaneamente disponibilidade real das
medições e o erro das vazões previstas a montante, preservando este controle.
