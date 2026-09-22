# Verificação independente: matriz observada Radar2020

As57.600 células(480×120) foram reconstruídas independentemente:11.520níveis,10.080Q/I e36.000chuva. Níveis eQ/I coincidem exatamente; chuva por sobreposição de intervalos completos coincide até2e-10mm, com máscarasNaN idênticas. Nenhum helper de features, chuva ou seleção operacional foi executado.

Diferença máxima chuva: 2.27e-13mm. As13.634células ausentes,453bases e454níveis contemporâneos conferem, assim como os1.920rastrosANA. Hashes dos manifestos e insumos conferem.

## Base atrasada versus alvo exato

Das480origens, 27 têm base indisponível e26 têm nível contemporâneo indisponível;22 coincidem. Há4origens com base finita/H(O)ausente e5com base ausente/H(O)finito. Isso reflete timestamps distintos: a base consultaO−15min e o alvo contemporâneo exigeO exato.
Em todas480origens existe linha exatamente na consultaO−15min; nenhuma base usa carry-forward adicional após consulta. Base ausente porQC:{'None': 4, 'Dado suspeito': 23}; H(O)ausente porQC:{'None': 3, 'Dado suspeito': 23}. Linha mais antiga aprovada não substitui a mais nova rejeitada/vazia. source/índice/valores estão nosCSVs.

Os pares h1/h6/h12 são447/437/426. Alvos são deslocados dentro deste bloco, sem cruzar anos ou prolongar além20/07; os últimos h alvos ficam indisponíveis. O máximo de resposta h12 é11,53m, sem inserir marca retrospectiva do pico.

## Q/I literal e diagnósticos

Todas8.640consultas Q/I foram conferidas por busca independente noCSVliteral: atraso60min, idade≤90min após consulta,23:59mantido. Reconstituem exatamente os21campos da matriz, incluindo transformações e diferenças1/2/4/8h. Nenhum flag participa do valor; JSON/CSV de diagnósticos são cópias exatas da auditoria anterior.
23origens usam algum zero e16usamQzero com componentes positivos. Estes zeros persistem nos campos correspondentes, sem substituição porNaN, componentes ou estimativas. Sinalização aritmética não é certificação oficial de erro.

## Chuva e limites

Os27postos foram reconstruídos diretamente das sériesALL-QC com intervalo finalizado, duração≤90min, QC/limites congelados, atrasos truncados em15min e pesos fixos. Não houve renormalização regional, chuva futura observada ou interpretação de ausência como mediçãozero; cobertura mínima0,5 regula os acumulados. Faltas/coberturas concordam nos75campos.

O acervoANA foi conferido campo por campo comXML na etapa anterior; aqui conferimoshashes, seleção, integração e rastros. JulhoONS parte doCSVnormalizado já auditado ehashParquet; não foi redecodificado. Esta igualdade numérica não certifica disponibilidade histórica, fuso, datum ou regime físico. Nenhum treino, rede, operação ou acesso aos anos2021/2022.
