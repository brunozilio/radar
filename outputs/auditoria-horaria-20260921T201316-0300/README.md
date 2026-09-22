# Auditoria horária de Muçum — 21/09/2026, 20h

Auditoria realizada em 2026-09-21T20:13:56.155678-03:00. O runner normal foi executado na raiz e suprimiu a duplicata das 20h (saída 0). Nenhuma nova previsão nesta chamada. A emissão já registrada das 20h04min38s BRT foi auditada em `/Users/brunozilio/Documents/radar/outputs/mucum-hourly-20260921T200235-0300`.

## Execução, fontes e continuidade

133 respostas coletadas, nenhuma falha final ou tentativa repetida no manifesto. 487 caminhos/blobs conferidos por SHA256: 56 artefatos únicos de modelo/código, 207 recibos de insumos e 33 arquivos do histórico cumulativo, sem divergências. Insumos registrados antes de ambas as emissões e bandas reais 1–12h completas. O índice atual aponta para o snapshot das 20h02, com manifesto conferido; nenhuma transição de grade reaplicada.

O pipeline desta chamada está em pipeline.log, sem erro. Não foi encontrado log independente do pipeline original dentro da pasta das 20h; não inferimos sua existência. Foram examinados run-result.json, manifesto, registros de ciclo e idades-fontes.csv. O ledger registra cycle_completed para o ciclo das 20h, sem cycle_failed vinculado.

Âncora Muçum 15,10 m às 19h45: idade de 15 min na referência e 19,64 min na emissão. CERAN às 19h, idade 60 min na referência; Carreiro às 19h30, idade 30 min. Quatro fontes auxiliares permanecem antigas (480–720 min); elas não são apresentadas como medições novas. Chuva meteorológica continua estimativa.

## Verificação pública

capture-ana às 20h13min36s BRT preservou 176 observações, zero novas e zero revisões em relação ao ledger imediatamente anterior; última disponível 15,10 m às 19h45. Recibo `c17bc1268a23b69d508a8f472483a685453e7e13a6c1877f59b18e3507f2f9db`. Dado aprovado pela origem, com fuso e datum ainda não verificados.

Relatório: `/Users/brunozilio/Documents/radar/outputs/monitoramento-prospectivo/reports/20260921T231336381908Z`. 20 pares diagnósticos confrontados, 12 pares vencidos sem observação exata das 20h e 158 ainda não vencidos. Zero pares elegíveis à meta, zero eventos independentes certificados. Não interpolar a observação faltante. Meta de 98% não demonstrada; histórico, diagnóstico e prospectivo continuam separados.

Cadência: 2/2 janelas fechadas (18–19h e 19–20h) completas. Nenhuma janela encerrada pós-vigência sem início, falha, atraso ou entrega incompleta. Janela 20–21h aberta, sem percentual próprio; registro iniciado não foi usado como prova de processo ativo. Falha e recuperação anteriores às 18h permanecem no relatório, sem cobertura retroativa.

## Divergência e extrapolação

Na banda real 12h, alvo 22/09 às 09h (12,923h após a emissão): Radar 17,955 m e HGE 27,243 m, diferença 9,288 m. O alvo 10h pertence à banda 13h. Em relação ao ciclo das 19h, HGE mudou −1,754 m no mesmo alvo 09h; Radar mudou até +1,023 m no alvo 04h. Diferença de previsão não comprova melhoria.

14/28 saídas de vazão excedem máximos de treino; todos os 28 modelos têm entradas fora das faixas históricas. Máximo previsto de 14 de Julho: 15.659,151 m³/s, versus 9.452 m³/s no treino. Não se trata de limite físico ou intervalo de confiança, e as previsões sinalizadas permanecem no placar.

No ponto máximo de Julho, os maiores termos positivos da regressão vêm de Castro Alves: afluência +2.743,298 m³/s, tendência de 6h da afluência +2.730,694, tendência de 3h +1.843,380 e delta de 1h da defluência +1.099,981. São atribuições estatísticas correlacionadas, não causalidade física; sensibilidade PET/chuva não cobre a incerteza dessas vazões. A extrapolação atual mantém a necessidade de revisão do regime hidráulico e referências temporais do histórico antes de treino.

PET=3 mm/dia, tau=6h, corte 21/09/2026 00h BRT e tolerância ±0,50 m preservados. Nenhum candidato promovido, previsão removida, deploy, publicação ou mudança do produto.

## Pesquisa delimitada

Agente concluiu `/Users/brunozilio/Documents/radar/outputs/pesquisa-ana-qualidade-20260921T231424Z`: três consultas sem documentação nova sobre CQ_NivelFinal/Dado aprovado. Manual ANA legado já conhecido preservado e hash conferido; contratos distintos não autorizam equivalência com consistência HidroWeb. Fuso, datum e semântica permanecem pendentes. Não repetir as buscas registradas em search-log.json.
