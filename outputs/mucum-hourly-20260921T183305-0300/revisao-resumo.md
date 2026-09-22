# Revisão solicitada com a medição das 18h

Nova emissão real 21/09/2026 às18:35:00 BRT. Muçum13,87m às18h; três usinas CERAN também às18h. Coleta nova:133 respostas públicas, sem falhas finais. A emissão original18:02 e seus recibos continuam intactos; nova emissão contém vínculos `manual_revision.previous_forecast` e motivo explícito. Todos os28pontos revisados permanecem no relatório diagnóstico, sem duplicar o denominador de amostras horárias programadas da meta. Antecedência calculada a partir18:35: o alvo19h tem aproximadamente25min, não1h.

| Alvo BRT | Radar m | HGE/ARNO m |
|---|---:|---:|
| 2026-09-21T19:00:00-03:00 | 14.721 | 15.019 |
| 2026-09-21T20:00:00-03:00 | 15.625 | 16.346 |
| 2026-09-21T21:00:00-03:00 | 15.926 | 17.683 |
| 2026-09-21T22:00:00-03:00 | 16.335 | 18.979 |
| 2026-09-21T23:00:00-03:00 | 16.308 | 20.293 |
| 2026-09-22T00:00:00-03:00 | 16.407 | 21.658 |
| 2026-09-22T01:00:00-03:00 | 17.651 | 22.969 |

15/28estimativas de vazão acima do máximo do treino. Máximo14Julho17.085,12m³/s versus9.452m³/s; isso não é teto físico nem intervalo de confiança. Divergência à meia-noite5,251m. Previsões experimentais; nenhum ajuste de PET3mm/dia, tau6h, corte21/09/2026 00h BRT ou promoção. Fontes auxiliares continuam com atrasos explicitados em idades-fontes.csv, incluindo quatro estações com360–600min; não foram apresentadas como novas.

Snapshot cumulativo registrado antes da emissão, índice atualizado para history nesta pasta. Relatório prospectivo: outputs/monitoramento-prospectivo/reports/20260921T213500499314Z. Ciclo concluído; janela18–19h ainda aberta, cobertura sem percentual. Zero pares elegíveis à meta e zero eventos independentes certificados.

Log: outputs/revisao-solicitada-20260921T183304-0300/pipeline.log. Artefatos conferidos por hash; vínculos dos recibos e presença das28linhas da revisão verificados.31testes locais passaram:9runner,15ledger,7cadência. O runner normal continua suprimindo duplicatas; revisão só com motivo explícito, coleta nova e observação aprovada exigida. Não houve deploy ou alteração do produto.
