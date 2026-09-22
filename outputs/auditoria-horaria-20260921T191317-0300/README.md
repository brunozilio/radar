# Auditoria horária — 21/09/2026, 19h BRT

Runner normal executado às19h13; saída0 e duplicata19h suprimida. Não houve emissão nova nesta chamada. Auditada a execução19h00–19h02 em outputs/mucum-hourly-20260921T190023-0300. As emissões reais foram19:02:15.832959(Radar) e19:02:15.936195(HGE). Ambas cobrem todas as bandas reais1–12h.

487 caminhos/blobs conferidos sem divergência, incluindo56artefatos de modelo,207recibos únicos de entrada e33arquivos do snapshot cumulativo. Recibos de insumo precedem as emissões. O índice aponta o snapshot19h, filho da revisão18h33.133respostas de fontes, sem erros finais ou no pipeline. As quatro fontes auxiliares antigas têm atrasos420–660min na origem; a limitação permanece registrada, sem apresentar dados antigos como novos. Âncora usada:Muçum14,25m18h30;CERAN18h eCarreiro18h30.

Nova capture-ana19:13:31 preservou172observações,1nova e0revisões. Última:14,44m18h45, aprovada pela origem. Fuso/datum continuam pendentes no ledger. Nenhuma alteração retrospectiva em observações ou emissões. A nova leitura atualiza verificação; não reemite a previsão19h.

Relatório prospectivo atualizado após cycle_completed:10pares diagnósticos,10ausências de medição exata,142não vencidos,0pares elegíveis e0eventos independentes certificados. A meta98%, os mínimos1000por horizonte/10eventos, tolerância0,50m e recorte observado>=7m permanecem inalterados; nenhuma precisão foi demonstrada. Cadence:18–19h completa(1/1janela encerrada),19–20h ainda aberta sem percentual próprio; nenhum ciclo pós-vigência encerrado sem início, tardio ou incompleto. Falha17h27 anterior à vigência permanece preservada; início de ciclo não é prova de processo ativo.

Extrapolação:13/28saídas acima do máximo do treino;28/28modelos com entrada fora da faixa. Máximo14Julho17.364,854m³/s contra9.452m³/s no treino. No máximo, Castro contribui slope3hI+3494,033;I+3041,111;slope6hI+2970,515;delta1hQ+2201,380m³/s. São termos correlacionados da regressão, não causas físicas ou incerteza calibrada. PET/chuva não cobrem a incerteza total. Nenhum valor sinalizado foi excluído.

Banda real12h(alvo08h22/09,12h57min44s após emissão):Radar17,405m/HGE28,639m, divergência11,234m. O ponto09h é banda13h. Resultados continuam experimentais, com meteorologia live diferente do treino. PET3mm/dia,tau6h,corte21/09/2026 00hBRT preservados; nenhum candidato promovido ou modelo ajustado no evento.

Pesquisa independente em outputs/pesquisa-ons-temporal-20260921T221420Z:3buscas inéditas sem novo contrato aplicável a23:59/hora24 ou vínculo histórico do exportador ONS. Documentos anteriores verificados; sem nova série ou alteração de elegibilidade. Histórico ONS continua fora do treino. Nenhum deploy, publicação, mensagem externa ou mudança de produto.

Detalhes verificáveis em audit.json,hash-checks.json,verify.py,capture-ana.json e report-result.json desta pasta.
