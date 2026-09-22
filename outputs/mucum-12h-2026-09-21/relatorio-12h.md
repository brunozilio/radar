# Muçum — previsão de 12 horas

Calculado em 21/09/2026 14:25 BRT. Referência: **21/09/2026, 14h**. Horizonte de 12h após essa referência, até **22/09, 02h**; o prazo restante é menor que 12h no momento da entrega. Dados consultados às 14h20. Medição de Muçum usada: **7,88 m às 13h45**.

**Foi possível calcular o horizonte de 12 horas, mas não demonstrar alta precisão para esta cheia.** A divergência entre os métodos deve acompanhar qualquer divulgação. Nenhum dos valores constitui previsão oficial, limite máximo da inundação ou indicação de área segura.

| Horário BRT | Estatístico selecionado | Propagação de vazão | Menor–maior dos quatro modelos |
|---|---:|---:|---:|
| 21/09 15h | 8,9 m | 9,7 m | 8,9–9,7 m |
| 21/09 16h | 9,7 m | 11,1 m | 9,6–11,1 m |
| 21/09 17h | 10,4 m | 12,2 m | 10,4–12,4 m |
| 21/09 18h | 10,7 m | 13,3 m | 10,7–14,6 m |
| 21/09 19h | 11,3 m | 13,9 m | 11,3–16,8 m |
| 21/09 20h | 12,4 m | 14,8 m | 12,3–18,4 m |
| 21/09 21h | 12,8 m | 15,6 m | 12,5–19,4 m |
| 21/09 22h | 13,2 m | 16,3 m | 11,8–19,8 m |
| 21/09 23h | 13,1 m | 16,6 m | 12,7–20,2 m |
| 22/09 00h | 12,1 m | 16,9 m | 12,1–19,8 m |
| 22/09 01h | 13,1 m | 17,1 m | 13,0–19,7 m |
| 22/09 02h | 12,9 m | 17,1 m | 12,9–20,0 m |

A amplitude entre modelos **não é intervalo de confiança**. Não há fundamento para escolher a curva mais baixa ou mais alta como a verdadeira, nem para interpretar achatamento ou queda de uma curva como confirmação de pico. Os valores se referem à régua ANA 86510000, não à altitude absoluta nem à profundidade da água nas ruas.

## Atualizações incorporadas

| Fonte | Última observação em 21/09 | Valor |
|---|---|---:|
| Muçum | 13:45 | 7,9 m |
| Linha José Júlio | 13:30 | 11,3 m |
| Santa Tereza | 13:45 | 8,6 m |
| Passo Carreiro | 13:30 | 4,9 m |
| 14 de Julho — saída | 14:00 | 3962,2 m³/s |

A vazão de saída de 14 de Julho caiu de 4.212,67 m³/s às 13h para 3.962,18 m³/s às 14h. Esta informação substituiu a extrapolação que ainda não conhecia a leitura das 14h. Uma redução na usina não implica redução imediata em Muçum: a onda já propagada e as contribuições laterais continuam relevantes. As futuras operações da usina não são conhecidas.

## Como o prazo de 12h foi calculado

Foram ajustados modelos separados para cada antecedência de 1 a 12h. O estatístico seleciona entre regressão com transformação logarítmica e árvores, com/sem previsão meteorológica, usando somente a validação histórica. Para a curva de 12h, foi escolhida uma única família pelo escore médio de validação dos 12 prazos; escolher o vencedor independentemente em cada hora criava uma troca artificial de família entre 01h e 02h, com salto de quase 7 m. Essa troca foi eliminada sem suavizar ou alterar as previsões individuais. A alternativa por vazão usa propagação distribuída com pesos não negativos, conservação das entradas fluviais, chuva apenas na área incremental de 1.273 km² e assimilação da última observação de Muçum. O atraso real de 15 minutos dessa observação substituiu o valor fixo de 30 minutos da emissão anterior.

A vazão futura a montante também foi prevista separadamente para cada prazo; não foi mantida constante nem substituída por observações futuras. A chuva futura usa previsões de GFS, ECMWF e ICON arquivadas com antecedência de 24h do horário válido, permitindo comparação histórica causal até 12h. São previsões de pontos representativos, não medições futuras ou chuva areal exata. Novas emissões meteorológicas não foram inseridas apenas no caso atual em um modelo treinado com antecedências diferentes.

O catálogo da bacia contém 122 identificadores, mas **27 séries ANA** sustentam a calibração pluviométrica longa. Não se afirma que todos os 122 pluviômetros tenham sido calibrados individualmente. O trajeto até a régua usa a rede hidrográfica e exclui contribuição direta do Guaporé, cuja confluência fica abaixo da régua; possíveis efeitos de remanso não foram determinados. O atraso médio do roteamento é cerca de 5,4h desde 14 de Julho e 10,6h desde Passo Carreiro, respostas distribuídas que não equivalem a um tempo fixo para toda chuva atingir Muçum.

## Erro por antecedência

Treino inicial: abril–setembro/2025; escolha de parâmetros: outubro/2025–junho/2026; teste temporal: julho–20/09/2026. Os coeficientes finais usam apenas alvos anteriores a 21/09. A versão do método foi desenvolvida após observar erros desta manhã: o teste de hoje é diagnóstico retrospectivo, não validação prospectiva independente. Foram impostos os atrasos atuais de telemetria, sem reconstruir os horários históricos de publicação/revisão.

Cada célula abaixo informa **estatístico / propagação**, comparados nas mesmas origens disponíveis para os dois métodos. MAE é erro absoluto médio, não margem garantida.

| Prazo | MAE no teste histórico | MAE nas retrospectivas de hoje | N de origens de hoje |
|---|---:|---:|---:|
| 1h | 0,03 / 0,22 m | 0,14 / 0,48 m | 13 / 13 |
| 3h | 0,07 / 0,35 m | 0,64 / 1,00 m | 11 / 11 |
| 6h | 0,15 / 0,34 m | 1,63 / 1,47 m | 8 / 8 |
| 9h | 0,32 / 0,49 m | 2,83 / 2,45 m | 5 / 5 |
| 12h | 0,45 / 0,62 m | 3,68 / 3,11 m | 2 / 2 |

Os testes de 9–12h de hoje usam poucas origens da madrugada, anteriores à aceleração atual. Não validam uma previsão emitida agora durante a subida. O arquivo `validacao-12h.csv` inclui P90, viés, persistência como referência e subconjunto de níveis ≥9 m, para não confundir muitos períodos de rio baixo com precisão em cheia. As amostras horárias se sobrepõem e não equivalem a eventos independentes.

A subida de Linha José Júlio de 7,34 para 11,35 m entre 12h30 e 13h30 excedeu a maior subida horária do histórico usado. As árvores podem subestimar eventos fora do treino; regressões podem extrapolar em excesso. A propagação também depende de curvas-chave e previsões das vazões futuras. Nenhum desses limites foi eliminado pelo simples aumento do horizonte.

## Verificação e reprodução

Os seis testes causais da integração da chuva passaram. Foram conferidos os 12 horários consecutivos, a mudança de data à meia-noite e valores finitos dos quatro modelos. Dados brutos e horários de coleta estão em `raw/manifest.json`. As previsões anteriores foram preservadas. Não houve nova escrita em produção, publicação ou envio de mensagens.

Executar com `HYDRO_OUTPUT_DIR` apontando para esta pasta e `HYDRO_HORIZON=12`: `hydro_latency_forecast.py`, `hydro_mass_check.py`, `hydro_mass_forecast.py`, `hydro_12h_report.py`. Scripts em `../../scripts/`. Dependências locais usadas: `/tmp/radar-hydro-libs` e `/tmp/radar-plot-libs`.

Fontes: [ANA — telemetria](https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx), [CERAN — 14 de Julho](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHQJ.php), [ONS — reservatórios](https://dados.ons.org.br/dataset/dados_hidrologicos_ho), [Open-Meteo — arquivo de previsões](https://open-meteo.com/en/docs/previous-runs-api), [SGB — operação do Taquari](https://rigeo.sgb.gov.br/handle/doc/25841).
