# Disponibilidade local das medições de Muçum

**O atraso presumido de 15 minutos não reproduziu as entradas dos ciclos regulares de 18h e 19h.** Ambos usaram a medição de 30 minutos antes da referência, com idade de aproximadamente 32 minutos na emissão. A leitura de referência−15 min não estava nos recibos vinculados a essas previsões.

## Evidência preservada

A auditoria verificou a cadeia local e os XMLs dos 20 recibos de observação, comparando os valores/qualidade extraídos com os registrados. São 19 coletas distintas: um mesmo resultado coletado foi registrado duas vezes após uma recuperação de execução e foi contado uma vez.

O período auditado vai de 16h48 a 19h45 BRT em 21/09/2026. Dez observações aprovadas têm horário válido posterior ao início da auditoria. A primeira recepção local ocorreu entre 18,19 e 43,33 minutos depois do horário da medição, com mediana de 27,50 minutos. Nenhuma dessas dez chegou ao nosso acervo em até 15 minutos.

**Isso não mede exatamente o atraso de publicação da ANA.** O intervalo entre nossas consultas, cache e execução também afeta a primeira detecção. O fornecedor pode ter disponibilizado um ponto antes de o coletarmos. Observações anteriores ao início da auditoria têm começo de disponibilidade desconhecido e foram excluídas desse resumo.

## Idade da âncora efetivamente usada

| Referência BRT | Emissão UTC | Modelo | Idade na referência | Idade na emissão | Leitura referência−15 min nos recibos | Revisão manual |
|---|---|---|---:|---:|---|---|
| 2026-09-21T16:00:00-03:00 | 2026-09-21T20:01:10.071258+00:00 | radar_arvores_live_candidate | 0.00 min | 61.17 min | True | False |
| 2026-09-21T16:00:00-03:00 | 2026-09-21T20:01:10.100814+00:00 | hge_arno_live_candidate | 0.00 min | 61.17 min | True | False |
| 2026-09-21T17:00:00-03:00 | 2026-09-21T20:31:09.277372+00:00 | radar_arvores_live_candidate | 0.00 min | 31.15 min | True | False |
| 2026-09-21T17:00:00-03:00 | 2026-09-21T20:31:09.338342+00:00 | hge_arno_live_candidate | 0.00 min | 31.16 min | True | False |
| 2026-09-21T18:00:00-03:00 | 2026-09-21T21:02:09.620438+00:00 | radar_arvores_live_candidate | 30.00 min | 32.16 min | False | False |
| 2026-09-21T18:00:00-03:00 | 2026-09-21T21:02:09.728188+00:00 | hge_arno_live_candidate | 30.00 min | 32.16 min | False | False |
| 2026-09-21T18:00:00-03:00 | 2026-09-21T21:35:00.363259+00:00 | radar_arvores_live_candidate | 0.00 min | 35.01 min | True | True |
| 2026-09-21T18:00:00-03:00 | 2026-09-21T21:35:00.457099+00:00 | hge_arno_live_candidate | 0.00 min | 35.01 min | True | True |
| 2026-09-21T19:00:00-03:00 | 2026-09-21T22:02:15.832959+00:00 | radar_arvores_live_candidate | 30.00 min | 32.26 min | False | False |
| 2026-09-21T19:00:00-03:00 | 2026-09-21T22:02:15.936195+00:00 | hge_arno_live_candidate | 30.00 min | 32.27 min | False | False |

As referências antigas de 16h/17h foram emitidas mais tarde. Uma idade zero em relação à referência nominal não significa dado instantâneo na emissão; por isso os dois relógios permanecem separados. Revisões manuais estão identificadas e não substituem a amostra agendada.

## Consequência para os experimentos

Os testes históricos com âncora ou aprendizado de erros após 15 minutos permanecem experiências sob essa hipótese, não réplicas certificadas da disponibilidade operacional. O próximo teste de sensibilidade deve variar a idade das entradas sem alterar alvos ou tolerância e, para validação prospectiva, usar exclusivamente os recibos efetivos disponíveis antes de cada emissão. Não atribuir atrasos retrospectivos uniformes como se fossem comprovados.

Não houve troca de observações, reescrita de emissões, mudança da elegibilidade, recalibração ou promoção. Os 107 testes locais passaram, incluindo exclusão de timestamps futuros, deduplicação de coletas e separação do histórico com início de disponibilidade desconhecido.
