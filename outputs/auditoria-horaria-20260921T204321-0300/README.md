# Auditoria horária — 2026-09-21T20:45:05.019870-03:00

Runner executado normalmente; duas emissões das20h já registradas, duplicata suprimida. Nenhuma previsão nova ou revisão manual. Auditada emissão20h04m38s BRT em `outputs/mucum-hourly-20260921T200235-0300`.

527 caminhos/blobs conferidos por SHA256, 56 artefatos e 207 recibos de insumos; 33 arquivos do snapshot cumulativo. Divergências: 0. As133 respostas não têm falhas finais ou retries; pipeline original localizado e sem exceção. Ambos modelos cobrem bandas reais1–12h e ciclo está concluído. Quatro fontes auxiliares antigas480–720min na referência permanecem registradas; Muçum19h45(15min), Carreiro19h30(30min), CERAN19h(60min).

Nova captura ANA20h43m39s BRT:178 observações, zero novas/revisões contra o ledger imediatamente anterior. Última15,41m20h15. Qualidade Dado aprovado na fonte; fuso e datum continuam pendentes. O alvo20h=15,26m, recebido por outra coleta após a rodada anterior desta automação, permite agora32 comparações diagnósticas;158 ainda não vencidas e nenhuma medição exata vencida ausente. Zero pares elegíveis, zero eventos independentes certificados;98% não demonstrados.

Para alvo20h, emissão regular18h02m09s tem1,964h reais: Radarerro0,2451m e HGEerro1,4557m. HGE permanece fora de±0,50m. Revisões manuais e prazos menoresque1h separados. Nenhuma observação interpolada nem exclusão por erro/extrapolação.

Cobertura:2/2 janelas encerradas completas;20–21h ainda aberta, sem percentual próprio. Nenhuma janela encerrada pós-vigência sem início, falha, atraso ou entrega incompleta. Falha17h27 permanece anterior à vigência, sem cobertura retroativa.

Extrapolação inalterada:14/28 saídas acima do treino;28/28 regressões com entradas fora. Julho máximo15.659,151m³/s versus9.452m³/s no treino. Castro domina termos positivos: I+2743,298; tendência6hI+2730,694; tendência3hI+1843,380; delta1hQ+1099,981m³/s. Atribuições correlacionadas, não causas físicas nem intervalo de confiança. Parâmetros PET3mm/dia, tau6h e corte21/09 00h mantidos; nenhuma promoção.

Relatório: `/Users/brunozilio/Documents/radar/outputs/monitoramento-prospectivo/reports/20260921T234339475977Z/report.md`. `audit.json` preserva cadência, idades, extrapolação e diagnóstico dos pares. Nenhuma mudança no produto, publicação, deploy ou mensagem externa.

Pesquisa independente: `outputs/pesquisa-castro-vigencia-20260921234335Z/README.md`; três consultas, nenhuma fonte primária nova aceita. Quatro hashes conferidos. Primeira consulta teve filtro de domínio incorreto, limitação preservada. Não repetir; cronologia operacional/curvas hidráulicas ainda pendentes.
