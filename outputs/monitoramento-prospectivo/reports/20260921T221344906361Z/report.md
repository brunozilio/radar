# Verificação das previsões — registro local

Gerado em 2026-09-21T22:13:44.906361+00:00. Pares elegíveis à meta: **0**.
A meta de 98% não foi demonstrada.

`diagnostic-scorecard.json` detalha MAE, viés, P90/P98 e erro máximo, separando
importações antigas das emissões registradas. Valores com fuso/datum pendentes
podem aparecer no diagnóstico, mas não são promovidos a evidência da meta.
O arquivo também mostra alvos únicos e episódios; pares horários dependentes
não fornecem por si só um intervalo de confiança nem eventos independentes.

Episódios observados agrupados: 1;
com começo/fim observados e sem lacunas: 0.
Eventos independentes certificados: 0.
Veja `flood-events.json`. O agrupamento diagnóstico não comprova independência;
várias previsões durante a mesma cheia não viram várias cheias na contagem.

Cobertura de entrega: 1/1
janelas horárias encerradas e avaliáveis. Percentual: 100.00%.
Sem janelas encerradas, não se informa 100% nem 0%. Veja `cadence.json` para
tentativas ausentes, falhas, entregas incompletas e limitações. Registro iniciado
sem fechamento não comprova processo ativo. Cobertura não é precisão do nível.

| Modelo | Horário BRT | Previsto (m) | Observado (m) | Erro (m) | Exclusões da meta |
|---|---|---:|---:|---:|---|
| radar_arvores_previsao_chuva | 21/09 16:00 | 10.35 | 11.64 | 1.29 | archival_import,registered_after_target,outside_1_to_12h_actual_lead_buckets,timezone_unverified,datum_unverified |
| radar_arvores_previsao_chuva | 21/09 17:00 | 11.21 | 12.97 | 1.76 | archival_import,outside_1_to_12h_actual_lead_buckets,timezone_unverified,datum_unverified |
| radar_arvores_previsao_chuva | 21/09 18:00 | 11.50 | 13.87 | 2.37 | archival_import,timezone_unverified,datum_unverified |
| hge_arno_reference | 21/09 16:00 | 10.74 | 11.64 | 0.90 | archival_import,registered_after_target,outside_1_to_12h_actual_lead_buckets,timezone_unverified,datum_unverified |
| hge_arno_reference | 21/09 17:00 | 11.92 | 12.97 | 1.05 | archival_import,outside_1_to_12h_actual_lead_buckets,timezone_unverified,datum_unverified |
| hge_arno_reference | 21/09 18:00 | 13.08 | 13.87 | 0.79 | archival_import,timezone_unverified,datum_unverified |
| radar_arvores_live_candidate | 21/09 18:00 | 13.43 | 13.87 | 0.44 | outside_1_to_12h_actual_lead_buckets,timezone_unverified,datum_unverified |
| hge_arno_live_candidate | 21/09 18:00 | 13.93 | 13.87 | 0.06 | outside_1_to_12h_actual_lead_buckets,timezone_unverified,datum_unverified |
| radar_arvores_live_candidate | 21/09 18:00 | 13.86 | 13.87 | 0.01 | outside_1_to_12h_actual_lead_buckets,timezone_unverified,datum_unverified |
| hge_arno_live_candidate | 21/09 18:00 | 14.02 | 13.87 | 0.15 | outside_1_to_12h_actual_lead_buckets,timezone_unverified,datum_unverified |

Importações de cálculos antigos ficam disponíveis para diagnóstico e nunca são
convertidas retroativamente em previsões registradas antes do evento. O horário real
do registro é independente da referência temporal usada no cálculo. Apenas medições
no horário exato, aprovadas pela origem, entram nos pares; não há interpolação.

O placar usa antecedência efetiva mínima: 1h significa de 1 até menos de 2 horas
reais entre registro e alvo, e assim por diante. A antecedência nominal é preservada
apenas para auditoria. Isso não permite contar uma previsão de 40 minutos como 1h.
Para avaliar 12h, o ciclo precisa emitir também alvos com ao menos 12h restantes.

Pendências de fuso/referência da régua, revisões e fontes indisponíveis são explícitas.
O registro é local, encadeado por hashes e sem sobrescrita pela ferramenta; não é
carimbo de tempo externo nem prova de disponibilidade de todos os ciclos horários.
