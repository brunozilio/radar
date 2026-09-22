# Sensibilidade à duração da correção residual

Constantes fixas de 2, 6 e 12 horas, âncora de 15 minutos. A referência operacional permanece em 6 horas.

Desenvolvimento histórico já inspecionado; nenhum candidato foi promovido.

|Prazo|Recorte|Tau (h)|N|Acertos ≤0,50 m|MAE (m)|Máximo (m)|
|---|---|---|---|---|---|---|
|1|all|6|1938|1891 (97.57%)|0.1383|1.3363|
|1|all|2|1938|1796 (92.67%)|0.2128|1.4437|
|1|all|12|1938|1899 (97.99%)|0.1248|1.3381|
|1|level_ge_7m|6|235|216 (91.91%)|0.2094|1.3363|
|1|level_ge_7m|2|235|163 (69.36%)|0.3985|1.4137|
|1|level_ge_7m|12|235|224 (95.32%)|0.1650|1.3381|
|6|all|6|1926|1458 (75.70%)|0.3641|4.1908|
|6|all|2|1926|1527 (79.28%)|0.3847|4.3569|
|6|all|12|1926|1387 (72.01%)|0.3662|4.0619|
|6|level_ge_7m|6|235|115 (48.94%)|0.7579|4.1908|
|6|level_ge_7m|2|235|98 (41.70%)|0.9519|4.3569|
|6|level_ge_7m|12|235|136 (57.87%)|0.6320|4.0619|
|12|all|6|1914|1159 (60.55%)|0.5579|9.0383|
|12|all|2|1914|1160 (60.61%)|0.5669|9.1388|
|12|all|12|1914|1143 (59.72%)|0.5513|8.8589|
|12|level_ge_7m|6|235|71 (30.21%)|1.3752|9.0383|
|12|level_ge_7m|2|235|65 (27.66%)|1.4397|9.1388|
|12|level_ge_7m|12|235|85 (36.17%)|1.2680|8.8589|

metrics.csv contém os dois modelos, todos os prazos e amostras individuais/comuns. Falhas e cobertura permanecem explícitas.

A verificação independente recompõe 216 níveis com componentes de seis origens previamente recalculados integralmente. Não reutiliza a inversão dos níveis previstos.

A correção estatística pode compensar erros de entrada, propagação e estado. Seu decaimento não identifica a causa física do erro. A conservação numérica do HGE não transforma essa correção em um fluxo físico.

Sem validação temporal independente para selecionar a duração, os resultados não justificam mudar a emissão operacional nem comprovar 98% prospectivos.
