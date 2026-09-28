# Chuva como sinal anterior às vazões: avaliação de 28/09/2026

O modelo público `mucum-hydrometry-public-v1` recebe níveis de quatro réguas e afluência/defluência das três usinas, mas não recebe precipitação. Portanto, uma chuva forte ainda não refletida nessas séries não pode antecipar uma subida por esse caminho. Isso é uma limitação estrutural, não uma falha pontual de leitura.

Foi congelado o [protocolo](rain-leading-signal-protocol.json) antes do cálculo e executado `scripts/hydro_rain_leading_experiment.py` nos arquivos de nível/vazão de horas exatas e chuva regional auditada. Cada atributo de chuva usa somente janelas observadas encerradas **uma hora antes** da origem. Cobertura inferior a 50% em qualquer uma das cinco regiões ou das quatro janelas exclui a hora de **ambos** os modelos; ausência jamais vira chuva zero. Família hidrométrica e intensidade da regularização são as do artefato público. Os dois braços usam exatamente os mesmos horários de treino e avaliação. O código e os resultados detalhados estão em `outputs/experimento-sinal-chuva-antecedente-20260928-revisado/`.

| Conjunto, H+6 | Horas | MAE só hidrometria | MAE com chuva | Acertos ±0,50 m só hidrometria | Acertos ±0,50 m com chuva |
| --- | ---: | ---: | ---: | ---: | ---: |
| Validação inteira | 3.104 | 0,131 m | 0,197 m | 98,3% | 95,7% |
| Validação, chuva regional ≥50 mm/6h | 69 | 0,114 m | 2,494 m | 97,1% | 1,4% |
| Validação, chuva ≥100 mm/6h | 8 | 0,036 m | 2,646 m | 100% | 0% |
| Período rotulado teste | 768 | 0,212 m | 0,210 m | 90,0% | 89,7% |
| Período rotulado teste, chuva ≥100 mm/6h | 0 | — | — | — | — |
| Cheia de setembro fora do ajuste | 4 | 1,633 m | 1,500 m | 25% | 25% |

Nos 69 horários de validação com chuva regional ≥50 mm/6h, a regressão com chuva previu subida ≥1 m que não ocorreu ≥0,5 m em **61** horários; a hidrométrica, em **zero**. Horas da mesma tempestade são dependentes e não representam 69 cheias distintas. Apenas duas tempestades históricas desse arquivo atingiram ≥100 mm/6h em alguma região, e o período rotulado teste não contém nenhuma. A observação de chuva foi recuperada retrospectivamente: o instante em que cada dado ficou disponível na época não está comprovado. Os períodos já foram examinados em pesquisas anteriores.

**Decisão:** rejeitar essa inclusão direta de chuva na previsão numérica pública. O painel público passa a avisar junto ao gráfico que a chuva a montante ainda sem resposta hidrométrica pode causar subestimação. Os valores previstos e o hash do modelo público permanecem como estavam; a mensagem descreve sua limitação real.

**Próxima hipótese a testar:** modelar primeiro a resposta por sub-bacia, incluindo chuva observada e prevista com horários de disponibilidade registrados, para então propagar as vazões resultantes e a contribuição incremental até Muçum. Um alerta antecipado de chuva deverá ser distinto de uma previsão numérica de nível e avaliado por tempestades independentes, inclusive falsos alarmes e eventos com operação de barragens diferente. As séries persistidas de chuva já incluem `created_at`; ainda é preciso verificar qualidade específica da chuva e a cobertura espacial antes de usá-las prospectivamente.
