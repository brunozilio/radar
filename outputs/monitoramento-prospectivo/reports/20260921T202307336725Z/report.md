# Verificação das previsões — registro local

Gerado em 2026-09-21T20:23:07.337206+00:00. Pares elegíveis à meta: **0**.
A meta de 98% não foi demonstrada.

| Modelo | Horário BRT | Previsto (m) | Observado (m) | Erro (m) | Exclusões da meta |
|---|---|---:|---:|---:|---|
| radar_arvores_previsao_chuva | 21/09 16:00 | 10.35 | 11.64 | 1.29 | archival_import,registered_after_target,outside_1_to_12h_actual_lead_buckets,timezone_unverified,datum_unverified |
| radar_arvores_previsao_chuva | 21/09 17:00 | 11.21 | 12.97 | 1.76 | archival_import,outside_1_to_12h_actual_lead_buckets,timezone_unverified,datum_unverified |
| hge_arno_reference | 21/09 16:00 | 10.74 | 11.64 | 0.90 | archival_import,registered_after_target,outside_1_to_12h_actual_lead_buckets,timezone_unverified,datum_unverified |
| hge_arno_reference | 21/09 17:00 | 11.92 | 12.97 | 1.05 | archival_import,outside_1_to_12h_actual_lead_buckets,timezone_unverified,datum_unverified |

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
