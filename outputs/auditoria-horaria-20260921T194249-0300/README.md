# Auditoria local — 21/09/2026, 19h43 BRT

Runner normal executado com saída 0: ambas as emissões das 19h já estavam registradas. Duplicata suprimida; nenhuma previsão nova nesta chamada. Auditada `mucum-hourly-20260921T190023-0300`, emissões reais 19h02min15s BRT, modelos/ciclo e bandas reais 1–12h completos. Não se repetiu migração meteorológica nem revisão manual.

## Novas medições e verificação

ANA coletada às 19h43min19s: 174 observações preservadas, duas novas (14,61 m às 19h e 14,80 m às 19h15), nenhuma revisão. Dados aprovados pela origem; UTC−3 é a convenção adotada ainda não confirmada para o endpoint e o datum permanece pendente. Recibo `c80e4a97cedb5ad87021616ed223037e5ce288d545028e2b43a18827ae95e4f1`. Sem dados futuros e sem interpolação.

Relatório: `/Users/brunozilio/Documents/radar/outputs/monitoramento-prospectivo/reports/20260921T224328898770Z`. Agora 20 pares diagnósticos observados, 142 ainda não vencidos e zero elegíveis à meta. Nenhum evento independente certificado. As dez ausências exatas anteriores receberam medição. Meta ≥98% em ±0,50 m por banda real 1–12h, inclusive observado ≥7 m, não demonstrada; mínimos de 1.000 previsões por horizonte e dez eventos não atendidos.

Para alvo19h, emissão17h31 (antecedência real1,481h): Radar14,71683 m, erro0,10683 m; HGE15,12003 m, erro0,51003 m, acima da tolerância. Emissão17h01 preservada: erros0,80420/0,50908 m. A emissão18h02 possui apenas0,964h reais e não entra em1h; revisão18h35 permanece diagnóstica. Não há seleção de emissão favorável.

## Integridade, fontes e cobertura

487 caminhos/blobs conferidos, 56 artefatos de modelo/código e 207 recibos de entrada, todos anteriores à emissão; índice cumulativo aponta snapshot19h, com manifesto e33arquivos conferidos. Zero divergências de hash.133 respostas públicas sem erro final ou retry; pipeline sem erro. Quatro fontes auxiliares antigas, com420–660min de atraso na origem, permanecem registradas. Muçum e Carreiro18h30; CERAN18h na coleta do ciclo19h. A coleta nova ANA não substitui os insumos selados dessa emissão.

Cadence: janela18–19h completa (1/1 encerrada);19–20h ainda aberta, sem percentual próprio. Nenhuma janela encerrada pós-vigência sem início, falha, atraso ou incompletude. Ciclo19h tem fechamento; nenhum processo ativo é inferido. Falha17h27 e recuperação17h31 anteriores à vigência preservadas, sem cobertura retroativa.

## Extrapolação e limitações

13/28 saídas de vazão acima do máximo de treino;28/28 modelos com preditores fora de faixa.14Julho máximo17.364,854 m³/s contra9.452 m³/s no treino. CastroAlves domina os termos positivos: tendência3h de afluência +3.494,033; afluência +3.041,111; tendência6h +2.970,515; delta1h de defluência +2.201,380 m³/s. São atribuições matemáticas correlacionadas, não explicações físicas independentes.

Alvo22/09 08h, banda real12h: Radar17,40494 m e HGE28,63894 m, divergência11,234 m já presente no ciclo anterior. Alvo09h é banda13h. Extrapolação não é teto físico nem intervalo de confiança; sensibilidade PET/chuva não cobre a incerteza total. Previsões sinalizadas e erros permanecem no histórico.

Sem alteração de PET=3mm/dia, tau=6h, corte21/09 00h BRT, modelos, metas ou produto. Candidatos ET0 e mistura com persistência continuam sem promoção. Histórico ONS continua fora do treino. Zero33,985m versus33,96m, vigências e máximos sensor/manual2024 não foram conciliados nem declarados equivalentes. Sem deploy, publicação ou mensagem externa.

## Pesquisa independente

Agente concluiu `outputs/pesquisa-castro-operacao-20260921T224324Z/`: três buscas inéditas, nenhum documento primário novo aceito. Dois resultados ONS eram recomposição elétrica, sem evidência de recomposição hidráulica. Quatro hashes conferidos. Datas reais de conclusão/deplecionamento/recomposição de Castro Alves continuam pendentes; evitar repetição imediata dessas consultas.
