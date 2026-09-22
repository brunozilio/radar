# Onde a inclusão de junho piorou a validação

O diagnóstico percorreu as102.084previsões congeladas, sem novo treino ou aplicação de modelo. Todos os12horizontes foram divididos por nível observado, tendência conhecida na origem, disponibilidade das18variáveis de montante e transição de acerto/erro. As691agregações reconciliam os resultados originais;204grupos de data/horizonte preservam todos os dias com alvo≥7m. Datas não são eventos independentes.

A regressão de9h na validação aparece em28alvos de8–9/11/2025:17→9acertos. Previsões mais de0,50m acima do observado passaram de10 para18; abaixo passaram de1 para1. Todos28casos tinham montante completo. Portanto, a ausência de entradas nesses casos não explica sozinha a regressão; o diagnóstico não identifica o mecanismo causal do ajuste.

| Recorte de9h | Pares | Acertos controle → junho | MAE controle → junho |
|---|---:|---:|---:|
| Alvo entre7e9m |25|15→6|0,645→1,028m|
| Alvo≥9m |3|2→3|0,313→0,173m|
| Tendência conhecida subindo≥0,10m/h |12|7→1|0,787→1,408m|
| Tendência conhecida estável entre−0,10e+0,10m/h |16|10→8|0,477→0,583m|

Os recortes por alvo usam verdade futura somente para explicar erros; não podem escolher modelos na emissão. Os grupos de tendência e nível se sobrepõem. Os três alvos≥9m ocorreram com tendência conhecida estável; são grupos distintos dos12casos de tendência crescente. No agregado, o ganho dos três níveis altos não compensa a regressão da maioria. Em8h também predomina erro por excesso:7→15casos, com20→13acertos no total. Não se escolheu somente9h para alterar a regra: os demais resultados estão integralmente em `strata.csv`.

A composição do treino ajuda a formular uma hipótese, sem prová-la. Em9h da validação, junho acrescenta159linhas a4.351:7,08% do peso total combinado, mas32,90% do peso no recorte de alvos≥7m e36,06% no recorte≥9m. Entre exemplos com |delta|≥1m, a média assinada é1,4315m emjunho contra0,4912m no conjunto recente. Contudo, a média no grupo de alvos≥7m é menor emjunho, e as variáveis também diferem; não é válido atribuir todo o excesso a uma simples mudança de média ou subtrair uma correção fixa.

Os96grupos de composição abrangem todos os24ajustes. Vetores de resposta e pesos coincidem exatamente com os salvos antes dofit. A próxima hipótese deve examinar a influência excessiva de um episódio nos exemplos raros, mantendo comparação simétrica e avaliação completa. Nenhuma ponderação foi alterada nesta etapa, nenhum modelo promovido e nenhum98% reivindicado. A meta permanece não demonstrada.

A última consulta atual,04h10BRT, ainda só disponibilizou a medição03h45:18,73m. A observação exata das04h segue ausente nesse recibo; nenhuma interpolação foi feita para pontuar os alvos pendentes.
