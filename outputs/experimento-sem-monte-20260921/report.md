# Retirada de Monte Claro dos preditores de vazão de 14 de Julho

A mudança não passou pelo critério pré-especificado para avançar à avaliação do nível de Muçum. Nenhuma previsão operacional foi alterada.

Foram retiradas 16 entradas de vazão, afluência e níveis/variações de Monte Claro. Os 61 preditores restantes, os alvos, cortes temporais, pesos e regularização mantiveram as regras anteriores. Os valores originais continuam preservados.

|Período|Recorte|Pares somados nos 12 prazos|MAE anterior (m³/s)|Sem Monte (m³/s)|Mudança|
|---|---|---:|---:|---:|---:|
|validation|all|78558|70.50|75.38|+6.92%|
|validation|high_flow|336|266.58|277.15|+3.97%|
|test|all|23550|142.36|130.89|-8.05%|
|test|high_flow|3252|396.03|301.96|-23.75%|

A soma dos pares pondera os erros pelos respectivos tamanhos; não representa observações independentes. O recorte de vazão alta usa o percentil 95 anterior a outubro de 2025, sem mudança de limiar.

O ganho em julho–setembro não se repetiu na validação anterior. Retirar a fonte inteira perde informação útil; este experimento não justifica descartar a fonte, declarar erro oficial ou trocar o modelo.

## Diagnóstico posterior da concentração do erro

As origens de 22/07 são separadas apenas para entender a sensibilidade já observada. Não são um recorte de seleção nem um evento independente certificado.

|Recorte|Grupo de origens|Família|N|MAE (m³/s)|Máximo (m³/s)|
|---|---|---|---:|---:|---:|
|all|july22_origins|level_and_slopes|288|1849.60|8160.61|
|all|other_origins|level_and_slopes|23262|121.22|4286.18|
|all|july22_origins|without_monte|288|484.63|2921.82|
|all|other_origins|without_monte|23262|126.51|4720.90|
|high_flow|july22_origins|level_and_slopes|288|1849.60|8160.61|
|high_flow|other_origins|level_and_slopes|2964|254.80|4286.18|
|high_flow|july22_origins|without_monte|288|484.63|2921.82|
|high_flow|other_origins|without_monte|2964|284.21|4720.90|

evaluation-extended.csv contém MAE, viés, RMSE, P90, P98 e máximo por prazo/período; daily-diagnostic.csv preserva o diagnóstico por data.

Referência reproduzida sem alteração nas previsões; 102108 pares idênticos por família, nenhuma previsão não finita nesse conjunto. Excluídos por alvo ou vazão conhecida ausentes continuam fora, como no controle; não equivalem a cobertura completa da série.

Arquivos históricos revistos e hipóteses de disponibilidade impedem tratar estes resultados como precisão prospectiva. Nenhuma conclusão de 98% decorre desta ablação.

O diagnóstico por data local concentra o ganho nas origens de 22/07:
MAE de 1.849,60 para 484,63 m³/s, sobre 288 pares sobrepostos de prazos.
Nas demais origens do teste, o MAE total piorou de 121,22 para 126,51 m³/s;
nas vazões altas, de 254,80 para 284,21 m³/s. Isso reforça a decisão de não
adotar a retirada integral: ela ajuda na oscilação já investigada, mas perde
precisão fora dela. Esta estratificação posterior é diagnóstico, sem excluir
o dia do placar nem transformar suas 288 linhas em eventos independentes.

## Verificação

305 verificações independentes passaram. Os 24 modelos anteriores e os 24
candidatos tiveram suas entradas e inferências conferidas: diferença máxima
de 0 m³/s. Os cortes e o pré-processamento de treino foram auditados; o
resíduo relativo máximo da equação normal foi 1,23e-15. Nenhum novo ajuste
foi feito pelo verificador. A suíte passou 112 testes.

coverage.csv confere a grade de avaliação: 78.558 pares na validação e
23.550 no teste por família. Não há exclusões por alvo ou vazão conhecida
ausentes nestes intervalos específicos, nem previsões não finitas. Isso
não certifica qualidade ou disponibilidade histórica das fontes.
