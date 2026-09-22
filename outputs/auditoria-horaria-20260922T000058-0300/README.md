# Ciclo 00h BRT de 22/09: duas tentativas falharam, sem nova previsão

Auditado em 2026-09-22T00:06:34.075822-03:00. Relatório prospectivo: /Users/brunozilio/Documents/radar/outputs/monitoramento-prospectivo/reports/20260922T030530777772Z.

- Execução normal e uma recuperação fresca falharam antes do cálculo por HTTP 500 em fontes ANA obrigatórias. Primeira: Muçum86510000; segunda: 9 estações ANA. Cada coleta tem133respostas registradas;93/86fontes SIGMA retornaram404, respectivamente. Não se conclui causa operacional a partir do HTTP.
- Saídas intactas: outputs/mucum-hourly-20260922T000059-0300 e outputs/mucum-hourly-20260922T000218-0300. Pipelines e resultados da chamada estão nesta auditoria. Ambos os ciclos têm cycle_failed no ledger.
- Não existem run-result.json nem idades-fontes.csv novos, pois o cálculo não iniciou. A ausência é parte da falha, não sucesso silencioso. Nenhuma emissão antiga é reapresentada como nova.
- Índice cumulativo continua no snapshot23h, com manifesto,33arquivos e vínculo ao pai íntegros. As idades do ciclo23h foram lidas somente como histórico; elas não descrevem um insumo novo de00h. Não houve reaplicação da migração meteorológica.
- 115verificações de hash sem divergência: arquivos recebidos nas duas tentativas, snapshot, capturaANA e pesquisa. Cadeia de registros verificada pelo leitor do ledger.

## Verificação e cobertura

capture-ana00h01m59sBRT funcionou:95observações preservadas,2novas e0revisões em relação ao ledger imediatamente anterior. Última leitura17,32m às23h30de21/09, Dado aprovado na origem. Fuso e referência vertical permanecem pendentes. A consulta curta funcionar não supre a falha da coleta completa de preditores.

Relatório após as duas falhas:40paresRadar diagnósticos,10alvos vencidos sem observação exata e87alvos ainda não vencidos;0pares elegíveis e0eventos independentes certificados. Meta98% não demonstrada.

Cadência:6/6janelas encerradas completas; nenhuma janela encerrada sem início, falha de entrega, atraso ou incompletude. A janela00–01h está aberta e sem percentual próprio, com duas tentativas falhas e nenhuma entrega até este relatório. Não confundir100% das seis janelas encerradas com sucesso da janela atual. Requisitos históricos preservados.

## Erros conservados

Alvo23h observado17,07m. Emissões17h31 e18h02 subestimaram o nível em1,724865m e1,615209m, com5,480756h e4,963994h reais. Emissões19h02,20h04 e21h02 tiveram erros0,235364m,0,011673m e0,029032m, respectivamente. A subida observada23h excedeu as previsões antigas; isso descreve o erro, sem provar sua causa física. Não ajustar neste evento nem chamar os acertos curtos de validação independente. Revisões manuais e importações históricas continuam separadas.

Pesquisa delimitada: outputs/pesquisa-mucum-nivelamento-20260922T030138Z. Três consultas novas encontraram apenas versões de documento já estudado. Nenhum download duplicado, evidência nova de vigência do zero ou conciliação marco–régua–sensor. Dois hashes conferidos. Não repetir essas consultas.

Nenhuma mudança de scripts operacionais, parâmetros, corte estatístico, produto, publicação ou deploy. Modelo retirado não executado/importado. Próxima rotina deve usar o runner normal, mantendo falhas e lacunas; não montar uma coleta híbrida nem reutilizar observações antigas como novas.
