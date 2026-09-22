# Auditoria e correção da previsão de Muçum

Emitido em 21/09/2026 14:14 BRT. Referência da nova previsão: 14h. Medição de Muçum usada no cálculo: **7,69 m às 13h30**. Recebida depois do cálculo, às 14h12: **7,88 m às 13h45**; essa leitura não foi incorporada retroativamente à emissão congelada.

**Conclusão:** houve um defeito real de processamento da chuva e ele foi corrigido. A resposta não linear reduziu os erros retrospectivos de 1–3h, mas a precisão de 4–6h permanece insuficiente para divulgar um único nível como resultado confiável. A nova onda a montante está fora da amplitude de variação horária do histórico usado.

## 1. Erro de chuva localizado e corrigido

O código anterior calculava uma chuva horária terminando na última leitura e a mantinha por até 65 minutos. Ao somar essas entradas em várias horas, podia reutilizar o mesmo intervalo enquanto faltava a próxima leitura. Exemplo auditado: a estação ANA 86403000 tinha 25,8 mm no intervalo terminado às 12h; no retrato anterior, essa mesma leitura podia aparecer novamente no campo horário das 13h. Ausência de leitura das 13h não significa nem 25,8 mm novos nem zero chuva.

A função `observed_rain_windows` integra apenas os intervalos efetivamente medidos, divide intervalos de fronteira proporcionalmente e mantém explícita a fração sem observação. O acumulado de várias horas não soma cópias de uma chuva horária mantida por atraso. Essa função substituiu o trecho defeituoso em `hydro_routing_data.py` e alimenta as rotinas novas.

Seis testes passaram: ausência de repetição na hora seguinte; independência de observações futuras; conservação nos intervalos parciais; distinção entre dado ausente e chuva zero; rejeição de lacunas longas; e monotonicidade dos totais com a duração da janela. A conferência com os contadores das seis estações que os disponibilizam apresentou concordância ≥99,998%: ChuvaFinal é consistente com os incrementos nessas séries, sem evidência de um erro geral de unidade por fator quatro.

## 2. Extrapolação identificada; melhora parcial quantificada

As regressões anteriores combinavam chuva intensa, tendências e interação com chuva antecedente. Hoje, vários preditores ficaram além do intervalo histórico. Foram testadas janelas corrigidas, retirada da interação, transformação logarítmica e resposta não linear por árvores, com escolha de parâmetros pela validação histórica.

Comparação controlada: mesmas origens, mesmos horários-alvo e dados congelados em 13h. Nenhum alvo de hoje foi usado para ajustar os coeficientes. O desenvolvimento foi motivado pelos erros observados hoje, portanto estes números são diagnóstico retrospectivo, não validação independente da solução corrigida.

| Antecedência | MAE anterior | MAE corrigido | Mudança | N de origens |
|---|---:|---:|---:|---:|
| 1h | 0,16 m | 0,13 m | redução de 21,9% | 13 |
| 2h | 0,49 m | 0,31 m | redução de 37,5% | 12 |
| 3h | 0,74 m | 0,56 m | redução de 24,2% | 11 |
| 4h | 0,92 m | 0,97 m | aumento de 5,2% | 10 |
| 5h | 1,15 m | 1,34 m | aumento de 16,1% | 9 |
| 6h | 1,63 m | 1,60 m | redução de 2,3% | 8 |

**Não houve melhoria consistente de 4–6h.** Não foi escolhido um parâmetro por apresentar o menor erro nesta manhã. Uma árvore também pode limitar excessivamente a resposta fora do histórico; a regressão pode extrapolá-la demais. A divergência entre ambas é informação relevante, não ruído a esconder.

## 3. Defasagem da telemetria e nova onda

Uma base histórica completa contém leituras que ainda não haviam chegado no momento de uma previsão ao vivo. A nova avaliação impõe aos preditores as idades relativas observadas no corte das 14h. Os alvos de nível exigem medição exata; não são cópias mantidas de um nível antigo. O teste não reconstrói o horário de publicação de cada mensagem passada, que não está disponível. É um teste com atraso imposto, não prova de desempenho operacional.

| Fonte | Horário da observação | Idade às 14h | Valor |
|---|---|---:|---:|
| Linha José Júlio | 13:30 | 30 min | 11,35 m |
| Santa Tereza | 13:45 | 15 min | 8,63 m |
| Passo Carreiro | 13:30 | 30 min | 4,89 m |
| Muçum | 13:30 | 30 min | 7,69 m |
| 14 de Julho — saída | 13:00 | 60 min | 4212,67 m³/s |

A ANA informou Linha José Júlio em **11,35 m às 13h30**, com indicação de dado aprovado. Às 12h30 eram 7,34 m: **4,01 m de subida em uma hora**, contra máximo de **1,63 m/h** no histórico de abril/2025 a setembro/2026 usado aqui. O SGB consultado confirmou a subida até 8,32 m às 13h, mas ainda não havia publicado a leitura das 13h30. As fontes compartilham a rede de origem; isso não equivale a dois instrumentos independentes.

## 4. Checagem física independente

Foi delimitada a área incremental entre a 14 de Julho, o Passo Carreiro e Muçum: aproximadamente **1273 km²**. A chuva dessa área foi separada da chuva já representada pelos fluxos a montante, evitando dupla contagem de volume.

Foi ajustado um roteamento de vazão com pesos não negativos; os pesos de cada entrada fluvial somam 1 e a fração de escoamento direto da chuva fica entre 0 e 1. O ajuste convergiu. O atraso médio ponderado resultou em 5,42h para a 14 de Julho e 10,60h para o Passo Carreiro; são médias da resposta distribuída, distintas das medianas de alinhamento dos picos/ondas da análise anterior.

Mesmo usando as vazões e chuvas efetivamente observadas, a reconstrução no teste temporal apresentou MAE de **0,43 m**, P90 de **0,81 m** e erro máximo de **3,05 m**. Esse teste é de reconstrução da resposta, não de previsão: conhecer as vazões futuras seria informação adicional indisponível ao emitir a previsão. Por isso esse ajuste não foi apresentado como uma previsão mais precisa.

Também foi executada a versão prospectiva: vazões futuras a montante estimadas com modelos treinados em dados anteriores, chuva futura de previsões previamente emitidas e assimilação do desvio da última vazão de Muçum observada. Partes de intervalos de chuva sem medição foram estimadas pela previsão meteorológica, sem apagar as parcelas já medidas. Nenhuma vazão futura observada entrou como preditor.

Essa versão por vazão resultou em aproximadamente 10,3 / 12,1 / 13,4 / 14,6 / 15,5 / 16,7 m, de 15h a 20h. No teste temporal, seu MAE de 6h foi **0,40 m**, pior que os **0,18 m** do candidato estatístico; nas retrospectivas desta manhã, teve **1,47 m**, contra **1,61 m** do estatístico com atrasos impostos. Essa diferença no pequeno evento atual não demonstra superioridade prospectiva e não foi usada para escolher a curva de 16,7 m como previsão oficial ou precisa.

As vazões da ANA associadas às réguas dependem das curvas-chave. Não são medições independentes contínuas de vazão. Seções, rugosidade, remanso e operação futura dos reservatórios não foram determinados por este ajuste.

## 5. Previsão meteorológica faltante

Foram recuperadas também emissões individuais de GFS, ECMWF e ICON de 00 UTC e/ou 06 UTC, além do arquivo de previsões do ICON. A emissão de 00 UTC, disponível antes da subida da manhã, previa chuva muito menor em alguns pontos do que a observada nos pluviômetros da região. Como os pontos de grade e as áreas de influência dos pluviômetros diferem, essa comparação é diagnóstico de insuficiência da representação da chuva, não uma razão exata para multiplicar a previsão.

A versão com previsões históricas de chuva usa valores emitidos com 24h de antecedência para permitir teste sem usar chuva futura observada. A inclusão de GFS/ECMWF/ICON produziu mudanças pequenas e não eliminou os erros do início da subida. As emissões individuais mais recentes foram usadas para conferência; não foram introduzidas apenas hoje num modelo treinado com outro prazo meteorológico.

## 6. Revisão numérica — referência 14h

O candidato abaixo foi selecionado pela validação histórica. **A coluna não significa nível confirmado ou de alta precisão.** A amplitude das alternativas é especialmente relevante porque a nova aceleração está fora do histórico.

| Horário | Candidato estatístico selecionado no histórico | Resultados dos quatro candidatos |
|---|---:|---:|
| 15h | 8,9 m | 8,8–10,3 m |
| 16h | 9,5 m | 9,5–12,1 m |
| 17h | 10,4 m | 10,3–13,4 m |
| 18h | 11,0 m | 10,9–14,6 m |
| 19h | 10,9 m | 10,9–16,8 m |
| 20h | 12,0 m | 12,0–18,0 m |

**A faixa entre candidatos não é intervalo de confiança nem limite máximo.** Em 20h, o modelo linear resulta em cerca de 18 m, o roteamento de vazão em 16,7 m e os não lineares em cerca de 12 m. A avaliação disponível não permite resolver essa divergência com alta confiança. Tampouco confirma pico ou queda.

Esta edição substitui a versão anterior para consulta do método e dos resultados. As previsões antigas foram preservadas para auditoria. Nenhum alerta foi enviado e nenhuma alteração foi feita no banco de produção.

## Arquivos e reprodução

- `mucum-revisao-6h.png`: gráfico da divergência, com horários e limitações dentro da imagem.
- `comparacao-erros.png` e `antes-depois-mesmas-origens.csv`: ganho e piora na comparação controlada.
- `previsao-atualizada.csv`, `divergencia-modelos.csv`, `retrospectivas-latencia.csv`: valores e erros auditáveis.
- `auditoria-contadores.csv`, `janelas-chuva-corrigidas.csv`, `idades-fontes.csv`: diagnóstico dos dados.
- `conferencia-balanco.json`, `roteamento-vazao-pesos.csv`: restrições e resultado do ajuste por vazão.
- Scripts: `hydro_rain_windows.py`, `test_hydro_rain_windows.py`, `hydro_precision_audit.py`, `hydro_precision_fit.py`, `hydro_latency_forecast.py`, `hydro_mass_check.py`, `hydro_precision_report.py`.

## Fontes

- [ANA — telemetria](https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx).
- [SGB — dados da régua de Muçum](https://sace.sgb.gov.br/api/dados/taquari_3_cota.csv).
- [ONS — dados horários de reservatórios](https://dados.ons.org.br/dataset/dados_hidrologicos_ho).
- [CERAN — 14 de Julho](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHQJ.php).
- [Open-Meteo — emissões meteorológicas individuais e disponibilidade](https://open-meteo.com/en/docs/single-runs-api).
- [SGB — operação do sistema Taquari em 2025](https://rigeo.sgb.gov.br/handle/doc/25841).

Para divulgação à população, preservar as datas, a identificação de previsão independente e a divergência. Este trabalho não identifica áreas seguras nem substitui as orientações da Defesa Civil.
