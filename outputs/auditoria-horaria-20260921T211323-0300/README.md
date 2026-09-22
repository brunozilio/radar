# Auditoria horária — 21/09/2026, 21h BRT

Runner normal executado às21h13: saída0 e duplicata21h suprimida. Nenhuma previsão nova nesta chamada. O ciclo preservado em `/Users/brunozilio/Documents/radar/outputs/mucum-hourly-20260921T210023-0300` foi emitido às21h02m20s, antes da retirada do HGE. Ambos os recibos antigos permanecem íntegros e cobrem as bandas reais1–12h.

## Fontes e integridade

133 respostas sem falha final ou retry; pipelines do ciclo e desta chamada sem exceção.492 caminhos/blobs conferidos sem divergências, incluindo56artefatos únicos,207recibos de insumos e33arquivos do snapshot cumulativo. O script vivo mudou após a emissão pela retirada do HGE; o blob de código registrado na emissão continua íntegro. O índice21h e seu manifesto-pai20h foram conferidos. Não foi reaplicada migração meteorológica.

Muçum usado no ciclo:15,56m20h30 (idade30min); CERAN20h (60min). Quatro fontes auxiliares antigas,540–780min na referência, permanecem uma limitação. Chuva de modelo continua estimativa.

## Verificação

Coleta ANA21h13m40s:180observações preservadas,1nova (15,73m20h45),0revisões contra o ledger anterior. Qualidade da origem: Dado aprovado; fuso e datum seguem pendentes. Medição exata21h ainda ausente. Recibo `8c897692287dde9f32675cde51b66fdeeb9c9b3e3f89b290d1365ac7b820e578`.

Relatório `/Users/brunozilio/Documents/radar/outputs/monitoramento-prospectivo/reports/20260922T001547913468Z`:16pares Radar diagnósticos,7alvos vencidos sem medição exata e86ainda não vencidos.0pares elegíveis e0eventos independentes certificados; meta98% não demonstrada.109pares de modelos retirados preservados no arquivo histórico do relatório. Nenhuma observação interpolada ou substituída.

Cadência:3/3janelas encerradas completas;21–22h continua aberta, sem percentual próprio. Nenhuma janela encerrada pós-vigência ausente/falha/tardia/incompleta. Falha17h27 e emissões anteriores à vigência permanecem no histórico. Transição registrada às21h14m48s para exigir somente Radar a partir de22h BRT; requisitos anteriores não foram reescritos.

## Mudança do Radar e diagnóstico histórico

Radar21h02 prevê17,854m01h e17,036m10h22/09, esta última com12,961h reais (banda12h). Para o mesmo alvo10h, queda de1,100m contra emissão20h04. Continua experimental, sem promoção.

O upstream-extrapolation do ciclo antigo foi lido:12/28saídas acima do máximo de treino;28/28com entradas fora da faixa. Máximo14Julho11.393,353m³/s contra9.452m³/s no treino. Castro:afluência+1.361,869; tendência6h+1.293,853; delta1hdefluência−525,495m³/s. São termos correlacionados, não causas físicas, limite do rio ou intervalo de confiança. O HGE antigo mudou−5,614m no mesmo alvo10h; a divergência Radar/HGE desse alvo é4,804m. Nenhum cálculo HGE novo nesta auditoria.

O runner e placar atuais já estavam alterados pela tarefa coordenadora para somente Radar, conforme remoção expressa registrada em docs/forecast-accuracy-goal.md. O texto recebido pela automação estava defasado; não reintroduzi o modelo. Nenhuma edição de scripts/modelos/produto, deploy, publicação ou mensagem externa. Corte, tolerância, referências e erros preservados.

## Pesquisa delimitada

Agente preservou relatório ANA2025 hospedado SGB, página24: estação de Muçum destruída em2024. Recuperação18/19 estações é agregada, sem comprovar recuperação individual ou vigência do zero. PDF/hash conferidos; fuso/datum seguem pendentes. Três consultas inéditas preservadas em `/Users/brunozilio/Documents/radar/outputs/pesquisa-mucum-20260922T001359Z`. Nenhuma série nova ou alteração de treino.
