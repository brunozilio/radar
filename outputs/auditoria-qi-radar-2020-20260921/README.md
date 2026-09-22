# Vazões ONS2020: valores literais e efeito nos atrasos RADAR

Uma consulta pública trouxe junho de2020 para aquecimento; julho foi reutilizado com hashes verificados. Somente14 deJulho, MonteClaro eCastroAlves foram extraídas. Não houve treino, correção de valores ou troca de componentes.

| Mês | Usina | Linhas | Q/I finitos | Qzero | Izero | Qzero com componentes>1 | Resíduo>1 |
|---|---|---:|---:|---:|---:|---:|---:|
| 2020-06 | JIUHQJ | 720 | 720/720 | 0 | 0 | 0 | 0 |
| 2020-06 | JIUHMC | 720 | 720/720 | 0 | 0 | 0 | 0 |
| 2020-06 | JIUHCA | 720 | 720/720 | 0 | 0 | 0 | 0 |
| 2020-07 | JIUHQJ | 744 | 744/744 | 8 | 6 | 8 | 8 |
| 2020-07 | JIUHMC | 744 | 744/744 | 14 | 15 | 0 | 0 |
| 2020-07 | JIUHCA | 744 | 744/744 | 0 | 0 | 0 | 0 |

Foram rastreadas8640 consultas (18 por origem: Qcorrente e recuos1/2/4/8h, Icorrente, três usinas) nas480 origens de01–20/07. 480 têm todos os valores disponíveis sob atraso60min e idade90min após consulta. 23 usam algum zero;16 usam Qzero com soma positiva de componentes;16 usam Qcom resíduo absoluto>1m³/s. As categorias se sobrepõem e não são rótulos oficiais de erro.

Nas nove origens extremas previamente identificadas, 9/9 têm todas as consultas e 0/9 usam algum zero. São origens de desenvolvimento previamente examinadas, não nove cheias independentes.

Os zeros não foram trocados por valores estimados, componentes ouNaN. MonteClaro pode apresentar componentes tambémzero: consistência aritmética não comprova correção física. Afluência é outra grandeza; nenhuma checagem de soma de defluência a valida. O limiar1m³/s é diagnóstico congelado, não tolerância oficial.

Junho foi extraído diretamente do CSVsemicolon com preservação dos campos textuais, linha e arquivo de origem. Julho preserva o CSVliteral da auditoria anterior e o hash doParquet; não foi redecodificado neste passo. Timestamps23:59 permanecem23:59; a auditoria não usa a coluna interpretada24h. Publicação histórica, revisão, fuso/exportador, datum e equivalência de regime continuam pendentes.

ons-references.json serve para uma futura matriz, cujo protocolo deve declarar explicitamente como trata esses diagnósticos. A presente auditoria não aprovou todas as linhas para treino, não alterou máscaras e não acessou2021/2022reservados.
