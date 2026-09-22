# Auditoria horária — Radar Muçum

Auditoria: 2026-09-22T01:03:04.968916+00:00. Emissão real: 21/09/2026 22:02:08,546775 BRT. Apenas Radar; experimental, sem promoção ou mudança do corte 21/09/2026 00h BRT.

## Execução e integridade

A chamada inicial encontrou o bloqueio ocupado. O processo concorrente 66300 foi confirmado no sistema e seu pipeline preservado; ele concluiu o ciclo das 22h. A segunda chamada normal retornou 0 e suprimiu duplicação. A disputa pelo bloqueio não é classificada como ciclo horário falho: nenhum cycle_started adicional foi lançado. A tentativa permanece em pipeline.log e invocation.json.

- Saída: /Users/brunozilio/Documents/radar/outputs/mucum-hourly-20260921T220010-0300.
- 133 respostas públicas; nenhum erro final ou retry de fonte. Pipeline do ciclo sem exceções.
- 616 verificações de hash sem divergência, 22 artefatos, 202 recibos e 33 arquivos do snapshot cumulativo.
- History-index aponta snapshot 22h; manifesto, arquivos e vínculo ao pai 21h íntegros. Sem reaplicar weather-transition.
- Muçum 16,17 m às 21h30, idade 30min na origem; CERAN 21h, idade 60min. Quatro fontes auxiliares têm 600–840min de atraso (detalhes em audit.json): limitação de disponibilidade preservada, sem apresentar essas leituras como atuais.

## Previsão e mudança

Máximo da trajetória calculada: 18.337 m em 2026-09-22T02:00:00-03:00, prazo real 3.964293h. Não equivale a pico real garantido.
Maior mudança para o mesmo alvo versus emissão21h02: +0.905m em 2026-09-22T05:00:00-03:00.
Banda real12h: alvo22/09 11h, 17,617m e12,964293h reais. Alvo23h tem0,964293h e fica fora da banda1h; alvo12h tem13,964293h e fica fora da banda12h.
Meteorologia live difere da previsão do dia anterior usada no treinamento. Nenhum ajuste ou promoção decorre da mudança da curva.

## Verificação e cadência

Relatório após cycle_completed: /Users/brunozilio/Documents/radar/outputs/monitoramento-prospectivo/reports/20260922T010304804272Z.
23 pares Radar diagnósticos;8 alvos vencidos sem medição exata às22h;92 ainda não vencidos. Zero pares elegíveis, zero eventos independentes certificados. Meta98% não demonstrada; sem tamanho amostral ou incerteza suficiente.
Capture-ana preservou183 observações,0novas e0revisões frente ao ledger imediatamente anterior. Última16,17m21h30. Fuso/datum pendentes; aprovação pela fonte não resolve referência vertical.
Desde a rodada anterior desta automação, alvo21h observado15,85m: emissão18h02 errou0,555834m com2,963994h reais; emissão19h02 errou0,142489m com1,962269h. A emissão17h31 errou0,699609m; erros permanecem no histórico, revisão manual fora da amostra programada e prazos<1h separados.

Cadência:4/4janelas encerradas completas;22–23h ainda aberta sem percentual próprio, com ciclo concluído e somenteRadar exigido após transição. Nenhuma janela encerrada pós-vigência sem início, falha, tardia ou incompleta. As janelas antigas preservam requisitos originais e a falha17h27 anterior à vigência continua registrada. Cobertura de entrega não é precisão.

Nenhum código de modelo, produto, treino ou referência histórica alterado; sem deploy, publicação ou mensagens externas. Pesquisa documental independente será ligada a esta auditoria ao terminar.

Pesquisa concluída: /Users/brunozilio/Documents/radar/outputs/pesquisa-mucum-reinstalacao-20260922T010222Z/README.md. Três consultas inéditas; boletim primário SGB18/06/2025 preservado apenas como evidência pontual de publicação operacional. Quatro hashes conferidos. Não resolve reinstalação, fuso, zero ou vínculo sensor–régua; nenhuma série importada.
