# Conferência inicial do contrato de chuva2018

Somente leitura dos helpers e reconstrução independente a partir do acervo ALL-QC já selado, sem importar executores operacionais, treinar ou consultar a rede. A matriz do coordenador ainda não foi comparada nesta etapa.

O contrato existente aceita incremento somente se QC/valor passam pelo parser e se a duração desde o timestamp anterior satisfaz0<dt<=5400s. A função de integração não faz QC por si; cabe ao builder aplicar explicitamente Dado aprovado, valor finito e0<=ChuvaFinal<=150mm. Não se deve remover linhas reprovadas antes de calcular dt: seus timestamps delimitam os intervalos seguintes. O primeiro registro não tem intervalo anterior e não contribui.

Cada incremento só fica disponível quando seu extremo final já ocorreu. Quando um intervalo já encerrado cruza a borda esquerda de uma janela, a fração é proporcional à duração sobreposta; é uma hipótese uniforme dentro daquele intervalo, não observação intra-intervalo. Não há extensão da última chuva até a consulta. Um intervalo de3/4h é rejeitado integralmente por exceder90min; não é dividido em blocos nem contado como tempo coberto. Isso pode excluir chuva realmente ocorrida: ausência de contribuição não significa precipitação fisicamente zero.

Caso86200900:48/59 leituras finitas/aprovadas, mas apenas5/8 intervalos admissíveis, totalizando5/8h. Respectivamente42/50 intervalos acima90min ficam excluídos; em cada janela há ainda1primeiro registro sem intervalo. Seu atraso congelado é4h(16slots de15min). A escassez reduz a cobertura regional; o peso não é redistribuído aos postos disponíveis.

Caso86450000: preservar04/10/2018 23:01:00 literal, incremento0.00 aprovado. Ele cria intervalo60s desde23h; a próxima leitura00h fecha3540s. Ambos são admissíveis, somente após seus finais. Não arredondar23:01 a23h ou00h, nem substituir um incremento por taxa horária. O zero reportado do minuto cobre60s medidos; não é preenchimento de lacuna. A integração geométrica independente conserva esses limites exatos.

Os27 atrasos são congelados de `outputs/auditoria-latencias-chuva-20260921/latencies.json`, com truncagem `int(delay_seconds/900)*900`, sem recomputar atraso pelo dado2018. Pesos regionais são os já fixados, soma dos montantes parciais e das coberturas ponderadas, sem renormalizar; P ficaNaN quandoC<0,5. Somente no somatório, ausência de um posto contribui0à soma e0à cobertura; isso não autoriza preencher sua série observada comzero. Se a cobertura atinge0,5, P continua sendo soma parcial ponderada, não estimativa renormalizada de toda a área.

Reconstrução independente por sobreposição de intervalos encerrados, sem `observed_rain_windows` ou `telemetry_features`: duas tabelas168×75 de chuva/cobertura. Primeira janela7567 células finitas/5033NaN; segunda7898/4702. Arquivos `rain-reconstructed-*.npz`, `rain-intervals-by-station.csv`, `rain-exceptional-intervals.csv` e `rain-regional-coverage-independent.csv` preparam a futura conferência. Cálculo usa diferenças entre timestamps literais, sem atribuir fuso físico; publicação, revisões,datum e disponibilidade histórica permanecem não certificados.

O limite de90min, o limiar0,5, os atrasos e os pesos foram mantidos. Nada foi ajustado com base na cobertura ou nos erros de modelos. Esta pasta permanece aberta para auditoria das matrizes após aviso de estabilidade do coordenador.
