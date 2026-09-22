# Suporte histórico das entradas — emissão Radar de 00h

Foram reproduzidas exatamente as 14 previsões emitidas às 00h08min55s BRT. As máscaras de treinamento foram reconstruídas pelo mesmo corte temporal e pela exigência original dos primeiros 24 campos completos. Alvos horários foram conferidos contra a série de 15 minutos. Nenhum ajuste novo foi feito.

O nível de entrada é 17,45 m; no treino varia de 0,81 a 15,30 m. Os alvos de treino chegam a 15,31 m. São 10.875 amostras no prazo nominal de 1h e 10.843 em 14h, com último alvo de treino em 20/09 às 23h, estritamente anterior ao corte de 21/09 às 00h.

Em todos os 14 modelos, 24 entradas estão acima do máximo visto no treino e uma abaixo do mínimo. Não faltam entradas nesta origem. Exemplos:

| Entrada | Atual | Maior valor no treino |
|---|---:|---:|
| Muçum: nível | 17,45 m | 15,30 m |
| Linha José Júlio: nível | 19,95 m | 15,94 m |
| Santa Tereza: nível | 16,52 m | 13,36 m |
| 14 de Julho: vazão | 11.893,47 m³/s | 6.148 m³/s |
| Tainhas: chuva em 24h | 151,2814 mm | 75,2967 mm |

Os níveis mantêm suas próprias referências de régua. A tabela compara cada variável consigo mesma, sem converter níveis entre estações. O CSV completo contém 2.520 comparações por coluna/horizonte.

Essas faixas não quantificam incerteza e estar dentro delas não comprova suporte multivariado. O modelo prevê variação sobre a âncora atual, portanto pode produzir níveis acima do maior alvo histórico; o diagnóstico não impõe corte artificial. As entradas meteorológicas atuais também diferem do produto de previsão do dia anterior usado no treino. Os horizontes nominais 13/14 não têm validação de precisão específica. Fuso e datum continuam sem certificação.

Este resultado reforça a busca de episódios com níveis, vazões e chuva mais diversos, preservando mudanças físicas e separação temporal. Não demonstra que adicionar qualquer cheia melhorará a precisão.

Esta versão corrige apenas o nome de uma coluna preliminar: cutoff_utc representa o corte exclusivo; actual_last_training_target representa o último alvo efetivamente admitido. A execução preliminar sem sufixo v2 não deve ser usada como referência final. Nenhuma previsão ou valor numérico mudou.
