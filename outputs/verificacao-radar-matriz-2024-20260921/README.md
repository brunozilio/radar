# Verificação independente da matriz Radar 2024

**124 verificações passaram; nenhum erro concreto identificado no escopo auditado.** Nenhuma consulta de rede, ajuste de modelo, execução HGE ou alteração da matriz/fontes foi realizada.

Matriz: outputs/radar-matriz-2024-20260921/features.npz, 744 origens horárias de 01/04/2024 00h até 01/05/2024 23h, 180 colunas. Grade anterior de 15 minutos começa em 29/03 e termina em 01/05 às23h45. Horários seguem UTC−3 presumido pelo preparo, sem nova certificação de fuso histórico.

## Chuva prevista

As 44.640 células das colunas120–179 foram comparadas por chave modelo/localização/origem/janela com o window-coverage.jsonl produzido na coleta meteorológica, e também recalculadas diretamente dos timestamps das respostas completas. Ordem confirmada: gfs_seamless, ecmwf_ifs025, icon_global; cinco localizações na ordem original; acumulados3/6/9/12h. Cada soma usa O+1,...,O+W, excluindo O, exclusivamente precipitation_previous_day1.

Diferença máxima nas duas comparações: **1,4210854715202004e−14 mm**, compatível com a ordem de redução de soma Python versus NumPy. Critério registrado: atol1e−12, rtol0. Portanto, equivalência numérica dentro dessa tolerância; não foi alegada igualdade binária da chuva. Não há células ausentes nesse bloco.

## Níveis e ausência de Carreiro

Leitura independente dos registros ANA all-qc.jsonl preservados. Para cada consulta, seleciona-se o registro mais recente até O−atraso, respeitando validade máxima de900s depois desse corte. Nível vazio/suspeito no registro mais recente continua ausente: não se busca registro finito mais antigo. Conversão cm→m e QC reproduzidos.

Foram reproduzidos exatamente os quatro níveis brutos e atrasados em toda a grade de15min, as17.856células dos primeiros24preditores e todos os2.976registros do level-source-trace.csv por chave estação/origem. Nenhuma fonte selecionada é posterior ao corte ou à origem. Base é Muçum atrasado15min. Os seis preditores Carreiro permanecem totalmenteNaN e complete24 é falso nas744origens.

As120colunas de telemetria também foram recompostas a partir de quarter-hour.npz: igualdade exata das89.280células, incluindo transformações de vazões, diferenças, chuvas e coberturas. Isso verifica alinhamento e transformação. A chuva observada regional **não foi reconstruída independentemente dos XMLs ANA nesta auditoria**; reproduzir seus derivados a partir da grade não equivale a verificar sua agregação desde a fonte.

## Conferência adicional de vazões ONS

Reconstruí independentemente Q/I de Julho, Monte Claro e Castro Alves diretamente de ons-ceran-source-values.csv, sem usar a grade como fonte. Os seis campos brutos e os seis atrasados reproduzem exatamente quarter-hour.npz; os21preditores derivados, colunas24–44, reproduzem exatamente **15.624células** da matriz, incluindo NaNs.

Seleção: último registro com timestamp≤O−60min; idade admissível de até90min **após esse corte**, sem buscar valor finito anterior quando o registro selecionado éNaN. Foram verificadas4.464consultas campo/origem e nenhuma fonte é posterior ao corte. Nos casos utilizáveis deste lote, a maior idade após o corte é60min, correspondente a120min desde a origem.

Os timestamps23h59 foram mantidos literalmente:62seleções por usina (Q/I),186no total. Exemplo: origem01/04 01h → corte00h → fonte31/03 23h59, idade pós-corte60s. Não houve conversão de23h59 para00h. Entre os1.488pares campo/origem de cada usina, permaneceram24indisponíveis emJulho,24emMonte e22emCastro. Todos estão preservados em ons-source-trace.jsonl; source_row nesse arquivo é o índice1-based após filtrar e ordenar os registros da usina, não a linha original doCSV/Parquet.

Limite: esta conferência parte doCSV preservado de valores originais, não realiza nova extração dos Parquets ONS. Não certifica os dados como medições fisicamente corretas nem corrige contradições de componentes.

## Alvos futuros e fronteira

features.npz não armazena doze matrizes de alvos futuros. **truth é a observação contemporânea H(O)**. Para horizonte h, o consumidor precisa usar H(O+h), equivalente ao deslocamento negativo de h posições nessa grade horária.

Conferi h1–12 contra lookup exato da fonte Muçum: igualdade exata. Há **744−h alvos finitos**: h1=743, h6=738, h12=732. Os últimos h alvos ficam ausentes, porque o lote hidrológico termina em01/05; a margem meteorológica até02/05 não autoriza inventar observações nem incluir labels fora do corte. Último alvo finito em todos os horizontes:01/05/2024 23h.

## Integridade e limites

Todos os hashes declarados no manifesto da matriz e em preparation.json foram conferidos. source-manifest.json registra os arquivos efetivamente lidos nesta auditoria. artifact-hashes.json registra os artefatos próprios; verify.py permite repetir a checagem somente local.

O preparo e o protocolo são coerentes no escopo conferido. Ainda não estão certificados: disponibilidade histórica das observações/rodadas, continuidade vertical das réguas, equivalência de versões meteorológicas ou regime operacional das usinas. Aplicar atrasos de2026 ao lote2024 continua uma hipótese. Esta auditoria não treina, não promove candidato e não demonstra generalização ou assertividade prospectiva.
