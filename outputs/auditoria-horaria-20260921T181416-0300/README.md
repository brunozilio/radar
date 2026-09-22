# Auditoria horária de Muçum — 21/09/2026

Conferência real: 2026-09-21T18:14:16.900809-03:00. Runner autorizado executado com saída 0: ambos os modelos da referência 18h já estavam registrados, portanto não houve nova emissão nem coleta completa duplicada. Auditada a execução `/Users/brunozilio/Documents/radar/outputs/mucum-hourly-20260921T180020-0300`, emitida às 18:02:09 BRT, concluída antes do relatório do ciclo.

## Mudança relevante e extrapolação

Comparação com a emissão de 17:31: maior mudança em alvo comum HGE +5,211 m para 22/09 às 07h. Na banda real 12h (12h57min 50s), esse alvo tem Radar 17.142 m e HGE 30.262 m, diferença 13.121m. O ponto adicional 08h tem 13h57min 50s reais e NÃO pertence à banda 12h: nele a divergência é 13,595 m (Radar 17,074; HGE 30,669 m).

Há 16/28 saídas de vazão acima do máximo de treino e 28/28 modelos com entradas fora de faixa. Maior estimativa de 14 de Julho: 19.648,206 m³/s, contra máximo 9.452 m³/s no treino. Para esse modelo, Castro Alves contribui +5.062,307 m³/s pela variação de 1h da defluência, +3.630,150 pela tendência de 3h da afluência e +2.845,461 pela tendência de 6h. Contribuições de regressão são correlacionadas e não comprovam causalidade física. Máximo de treino não é limite físico; sensibilidade PET/chuva não representa a incerteza total.

## Insumos, preservação e verificação

- 133 respostas públicas sem falha final; 133 hashes de fontes, 56 artefatos únicos e 207 recibos de insumos conferidos. Pipeline sem traceback/erro. Snapshot cumulativo 18h e 33 arquivos conferidos contra índice/manifesto; não houve retorno a histórico estático.
- Muçum usado no cálculo: 13,45 m às 17h30, idade 30 min na origem. CERAN 17h, idade 60 min. Quatro fontes auxiliares permanecem antigas (360–600min), registradas em audit.json; não são medições novas. Meteorologia mantém emissão/ciclo desconhecidos, e chuva é estimativa.
- capture-ana às 18:13:15 BRT preservou 168 observações: 0 novas em relação ao ledger anterior e 0 revisões. Última leitura 13,67 m às 17h45, aprovada pela fonte; fuso/datum ainda pendentes. Recibo `75ec8f8f50b84ef7dfc89cbeb68e9dd06da1dda2f4f272a209481bf9ad6f618c`.
- Relatório atualizado: `/Users/brunozilio/Documents/radar/outputs/monitoramento-prospectivo/reports/20260921T211326675414Z`. 4 pares diagnósticos antigos, 6 pares vencidos sem observação exata e 96 ainda não vencidos; 0 elegíveis à meta. Sem interpolação ou substituição de observações. Um episódio aberto, nenhum evento independente certificado.
- Cadência: ciclo 18h concluído com ambos os modelos no mesmo ciclo e bandas 1–12 reais. Janela 18–19h ainda aberta; 0 janelas fechadas e percentual null. Não existe janela encerrada pós-vigência sem início a contabilizar neste corte. Falha 17:27 e recuperação 17:31 anteriores à vigência preservadas, sem cobertura retroativa. Nenhum registro iniciado em aberto.

Sem alteração de código, parâmetros, treinamento, produto ou agendamento. PET 3 mm/dia, tau 6h e corte 21/09/2026 00h BRT preservados; nenhum candidato promovido. Previsões sinalizadas permanecem no ledger. Meta 98% não demonstrada; insuficiência de evidência e de metadados permanece explícita.

Pesquisa independente concluída: `outputs/pesquisa-mucum-metadados-20260921T211404Z/README.md`. Duas fontes ANA/SGB arquivadas e hashes conferidos; interface histórica UTC−3 e documentação operacional de sensores não resolvem contrato atual do endpoint nem vigência do zero. Nenhum metadado promovido no ledger.
