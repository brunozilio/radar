# Modelo alternativo condicionado a conflito de componentes ONS

Diagnóstico histórico local. Nenhuma observação, emissão ou modelo operacional foi substituído.

A regra geral detectou três registros de Monte Claro: Q total zero com componentes completos somando 6 m³/s. Pela dependência dos preditores atuais e de 1/3/6 horas, eles afetam nove origens, 22/07 das 08h às 16h. Somente nessas origens usa-se a previsão congelada sem os 16 preditores Monte. Nenhuma data está codificada na seleção.

|Período|Recorte|Modelo|N|MAE (m³/s)|Máximo (m³/s)|
|---|---|---|---:|---:|---:|
|validation|all|reference|78558|70.50|2098.40|
|validation|all|conditional|78558|70.50|2098.40|
|validation|high_flow|reference|336|266.58|1100.07|
|validation|high_flow|conditional|336|266.58|1100.07|
|test|all|reference|23550|142.36|8160.61|
|test|all|conditional|23550|125.37|4286.18|
|test|high_flow|reference|3252|396.03|8160.61|
|test|high_flow|conditional|3252|272.99|4286.18|

Foram selecionadas 108 previsões dos 12 prazos; 108 melhoraram e 0 pioraram. As outras 102000 ficaram exatamente iguais. A população de alvos foi preservada.

O grupo selecionado está inteiro no teste já inspecionado. Não há caso de conflito exercitado na validação anterior, portanto a invariância dessa validação não prova que o ramo alternativo generaliza. Nove origens e 108 prazos sobrepostos não constituem nove eventos nem 108 amostras independentes.

O conflito não determina qual coluna está incorreta nem fornece uma vazão verdadeira de reposição. Campos ausentes permanecem desconhecidos. A fórmula ONS não foi transferida às páginas CERAN atuais, cujo contrato de componentes é diferente/não verificado.

Atraso de uma hora e expiração de 90 minutos reproduzem a hipótese dos preditores históricos. O arquivo revisado não informa quando cada revisão esteve disponível. A seleção usa tempos passados, mas disponibilidade histórica não está certificada.

A melhora de vazão deve ser investigada até o nível de Muçum; por si só não demonstra a meta de 98% e não autoriza promoção.

## Proveniência e limite de transferência

A verificação independente conferiu 85 condições no diagnóstico de montante,
sem alteração fora das origens selecionadas. No nível de Muçum, confirmou
23.538 linhas e 23.430 valores/status não selecionados exatamente iguais.
A suíte passou 116 testes.

O confronto irrestrito entre ONS e a série congelada encontrou 175 diferenças
de dependências em 45 timestamps de 19–21/09 UTC, máximo 77,95 m³/s;
nenhuma envolve os conflitos selecionados, zero bruto ou ausência congelada.
As 12 dependências que realmente acionam a regra foram conferidas. Não se
afirma equivalência global das séries nem se atribui uma causa sem pesquisa.
A regra não está autorizada para transferência automática a outro snapshot
ou às fontes CERAN ao vivo sem nova conferência de semântica/proveniência.
