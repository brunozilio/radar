# Muçum — atualização com uma curva central

Emitido em 2026-09-21T15:16:58.244423-03:00. Referência 2026-09-21T15:00:00-03:00; último nível observado 9.23 m em 2026-09-21T14:45:00-03:00. Os dados brutos novos e horários de coleta estão em `raw/manifest.json`.

| Horário BRT | Estimativa central |
|---|---:|
| 21/09 16h | 10,4 m |
| 21/09 17h | 11,2 m |
| 21/09 18h | 11,5 m |
| 21/09 19h | 11,7 m |
| 21/09 20h | 12,4 m |
| 21/09 21h | 12,1 m |
| 21/09 22h | 13,4 m |
| 21/09 23h | 13,6 m |
| 22/09 00h | 14,2 m |
| 22/09 01h | 14,0 m |
| 22/09 02h | 13,8 m |
| 22/09 03h | 13,7 m |

A família **arvores_previsao_chuva** foi escolhida pelo menor escore médio na validação histórica dos 12 prazos: {"arvores": 0.41380857429265044, "arvores_previsao_chuva": 0.40244488171854725, "linear_log": 0.43001754519176577}. Não houve escolha pela preferência por um nível menor/maior, nem suavização manual para parecer mais confiável. Os coeficientes foram ajustados com alvos anteriores a hoje. A seleção e o desenvolvimento anteriores já observaram erros deste evento; retrospectivas de hoje não são validação prospectiva independente.

Foram atualizadas 27 séries ANA, três usinas CERAN e 100 séries individuais SIGMA. A SIGMA confirmou a última leitura de Muçum; as séries SIGMA não foram inseridas apenas no caso atual em um modelo calibrado com outra base. Suas diferenças e atrasos estão em `auditoria-sigma.csv`. O cálculo de chuva continua usando as 27 séries ANA e pesos de área; vazões/afluências das três usinas entram como preditores. Não se afirma que todas as estações SIGMA estejam assimiladas.

Para 12h, esta família apresentou MAE de 0,45 m no teste histórico e 3,82 m nas 3 retrospectivas disponíveis de hoje. O primeiro valor mistura condições de rio baixo e cheias; nenhum deles é uma margem garantida para a previsão atual. A onda atual ultrapassa condições do histórico. A representação com uma linha atende ao formato solicitado e não resolve a incerteza.

Os quatro métodos ainda resultam em 13,3 a 18,8 m no último horário, inclusive 17,0 m na propagação por vazão. Essa amplitude não é um intervalo de confiança nem um limite de cheia. As alternativas foram preservadas em `candidatos-latencia.csv` e `roteamento-previsao.csv`, embora o gráfico mostre só a curva selecionada. Os resultados não confirmam pico ou queda.

Conferência: 12 horários consecutivos e valores finitos, uma família em toda a curva, seleção pelo escore histórico. O último observado é um ponto separado, sem inventar uma medição às 15h. Nenhuma mudança em produção ou mensagem externa.

Fontes: [ANA](https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx), [SIGMA — Muçum](https://sigmameteorologia.com/produtos/stations/2026-09-21/86510000.txt), [CERAN — 14 de Julho](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHQJ.php), [Monte Claro](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHMC.php), [Castro Alves](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHCA.php). Arquivo histórico de reservatórios ONS e previsões meteorológicas GFS/ECMWF/ICON complementam o ajuste e as alternativas.
