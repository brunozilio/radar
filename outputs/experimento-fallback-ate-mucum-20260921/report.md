# Efeito do modelo condicional sobre o nível de Muçum

Resultado histórico misto, sem promoção. A regra usa conflitos de componentes ONS para selecionar previsões de vazão de 14 de Julho sem Monte Claro em nove origens já investigadas. Chuva, Carreiro, estados HGE, âncora, curva e observações permanecem iguais.

|Prazo|Modelo|Cheias: N|Acertos ≤0,50 m|MAE (m)|Máximo (m)|
|---|---|---:|---:|---:|---:|
|1 h|reference|235|216 (91.91%)|0.2094|1.3363|
|1 h|candidate|235|214 (91.06%)|0.2085|1.3363|
|6 h|reference|235|115 (48.94%)|0.7579|4.1908|
|6 h|candidate|235|117 (49.79%)|0.6809|3.1660|
|12 h|reference|235|71 (30.21%)|1.3752|9.0383|
|12 h|candidate|235|71 (30.21%)|1.1761|5.7441|

Foram mantidas as 23.538 linhas: 23.103 pares confrontáveis, 147 alvos ausentes e 288 âncoras ausentes. A seleção afeta 108 previsões; as demais conservam o valor anterior sem reconversão numérica. Não houve ajuste adicional de modelo.

A vazão melhorou em todas as 108 previsões selecionadas, mas esse ganho não se converteu em aumento de acertos em todos os prazos de nível. Na cheia em 1 h houve perda líquida de dois acertos; em 12 h a redução do erro médio e máximo não mudou os 71 acertos de 235. Portanto, esta mudança não atende à meta.

A reconstrução por componentes em seis origens, incluindo três afetadas, conferiu 144 valores com diferença máxima 7,11e-15 m. O cálculo independente refez o roteamento de Julho e usou componentes Carreiro/HGE/residual de replay anterior, sem inverter o nível. Não representa nova simulação integral dos 23.538 casos nem certificação de disponibilidade.

Os três conflitos são conhecidos retrospectivamente e não há casos exercitados na validação anterior. A regra diagnóstica ONS não foi aplicada às parcelas CERAN do monitoramento atual. Antes de qualquer uso operacional, são necessárias evidências independentes de qualidade, disponibilidade e ganho.

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
