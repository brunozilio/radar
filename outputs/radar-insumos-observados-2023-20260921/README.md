# Acervo observado Radar — 29/08 a 30/09/2023

**Coleta concluída dentro do limite: 27 novos GETs ANA, 11 XMLs reutilizados e nenhuma consulta nova ONS/NWP.** O plano foi gravado antes de todas as requisições. As respostas novas foram HTTP200; ausência de dados da estação permanece distinta de falha de transporte.

São **27 séries com 19.265 registros**, 17.083 valores de chuva aprovados. No conjunto de 38 respostas novas/reutilizadas, 31 contêm registros e sete informam Sem dados. Não há duplicação de timestamps dentro de estação. Isso não significa cobertura integral dos 33 dias.

## Procedência e escopo

collection-plan.json preserva data do pré-registro, inventário, pesos/latências por hash e cada janela autorizada. Os oito postos da coleta anterior foram consultados apenas de05 a30/09; seus XMLs29/08–04/09 foram reutilizados. Os18outros postos receberam uma consulta29/08–30/09. Muçum recebeu apenas29–31/08, pois todo setembro já estava preservado em três respostas. Não houve retentativa automática ou sobreposição deliberada de consultas.

## Inventário por estação

| Estação | Registros | Níveis aprovados | Chuvas aprovadas | Cadência modal (min) | Último registro original |
|---|---:|---:|---:|---:|---|
| 86060010 | 792 | 0 | 792 | 60 | 2023-09-30 23:00:00 |
| 86099000 | 760 | 760 | 760 | 60 | 2023-09-30 23:00:00 |
| 86102000 | 760 | 760 | 760 | 60 | 2023-09-30 23:00:00 |
| 86117000 | 760 | 760 | 760 | 60 | 2023-09-30 23:00:00 |
| 86125000 | 0 | 0 | 0 | — | Sem registro |
| 86125050 | 760 | 760 | 760 | 60 | 2023-09-30 23:00:00 |
| 86160000 | 3128 | 3113 | 2639 | 15 | 2023-09-30 23:45:00 |
| 86163000 | 642 | 642 | 642 | 60 | 2023-09-30 23:00:00 |
| 86200900 | 753 | 753 | 0 | 60 | 2023-09-30 23:00:00 |
| 86280500 | 763 | 763 | 763 | 60 | 2023-09-30 23:00:00 |
| 86298000 | 668 | 668 | 668 | 60 | 2023-09-25 23:00:00 |
| 86403000 | 760 | 760 | 760 | 60 | 2023-09-30 23:00:00 |
| 86410800 | 757 | 757 | 757 | 60 | 2023-09-30 23:00:00 |
| 86447000 | 153 | 153 | 153 | 60 | 2023-09-04 08:00:00 |
| 86448000 | 672 | 672 | 672 | 60 | 2023-09-25 23:00:00 |
| 86450000 | 147 | 147 | 147 | 60 | 2023-09-04 03:00:00 |
| 86471000 | 161 | 161 | 161 | 60 | 2023-09-04 17:00:00 |
| 86472000 | 2683 | 2682 | 2681 | 15 | 2023-09-25 22:30:00 |
| 86472600 | 16 | 0 | 0 | 15 | 2023-09-30 23:45:00 |
| 86479000 | 154 | 154 | 154 | 60 | 2023-09-04 09:00:00 |
| 86488000 | 257 | 257 | 257 | 60 | 2023-09-25 16:00:00 |
| 86493000 | 156 | 156 | 0 | 60 | 2023-09-04 12:00:00 |
| 86495500 | 752 | 752 | 0 | 60 | 2023-09-30 23:00:00 |
| 86500000 | 0 | 0 | 0 | — | Sem registro |
| 86504900 | 0 | 0 | 0 | — | Sem registro |
| 86505500 | 159 | 159 | 159 | 60 | 2023-09-04 14:00:00 |
| 86510000 | 2652 | 2311 | 2638 | 15 | 2023-09-25 22:45:00 |

QC aprovado é atributo da fonte, não nova certificação física. approved_numeric exige valor numérico e CQ aprovado; valores aprovados negativos permanecem explicitamente contabilizados. parser_compatible é uma contagem diagnóstica separada, sem modificar as séries.

## Ausências e ressalvas principais

- **Muçum86510000:** 2.652registros, 2.311níveis aprovados,11suspeitos e330vazios. Nenhum registro após25/09 22h45. A interrupção no pico já conhecida continua: último nível aprovado04/09 19h30, retorno08/09 14h15. A marca retrospectiva não foi inserida. Os516slots sem registro incluem28em04/09 22h–05/09 04h45,4em07/09 10h–10h45 e484após25/09 22h45.
- **Linha José Júlio86472000:** 2.683registros,2.682níveis aprovados e1vazio;2.681chuvas aprovadas e2vazias. Último registro25/09 22h30;485slots de15min ausentes no fim da janela.
- **Santa Tereza86472600:** a primeira resposta29/08–04/09 é Sem dados. A extensão contém apenas16registros de30/09 20h–23h45, todos sem nível e chuva finais. Não interpretar como recuperação de observações utilizáveis.
- **Passo Carreiro86500000,86125000 e86504900:** zero registros em toda a janela. Não são zeros de nível, vazão ou chuva.
- **86450000 e86479000:** as extensões05–30/09 retornaram Sem dados; seus registros permanecem limitados à coleta anterior, encerrando04/09 às03h e09h respectivamente. São postos de peso importante nas regiões Baixo Antas e Carreiro.
- **86160000:**3.128registros;2.639chuvas aprovadas e489vazias, última chuva aprovada25/09 22h45 embora os registros continuem até30/09. 36timestamps faltam no início29/08 00h–08h45 e4em24/09 20h–20h45. Seus níveis incluem11suspeitos e4vazios, preservados.
- **86200900,86493000,86495500:** contêm registros, mas nenhum valor numérico aprovado de ChuvaFinal. QC isolado não constitui chuva observada.
- Nas estações predominantemente horárias, o diagnóstico usa792slots em33dias, não3.168slots de15min. Cobertura menor pode resultar de lacunas reais, início/fim antecipado ou cadência diferente. coverage.json mantém ambos os diagnósticos e todos os intervalos; nenhum deles implica precipitação zero.

Respostas Sem dados no acervo:86472600 e86500000 em29/08–04/09;86125000 e86504900 em29/08–30/09;86450000,86479000 e86500000 em05–30/09. São mensagens Error no XML com HTTP200, preservadas em source-manifest.json. Não ocorreu falha de rede registrada no lote novo.

## Normalização sem apagar QC

stations/ contém27JSONL integrais com todos os campos/QC originais, data literal, arquivo de origem, SHA256 e índice do registro XML; e27NPZ com time_original, source_file, source_record_index, level_m_raw, flow_m3s_raw, rain_mm_raw, counter_mm_raw e quatro arrays deQC. A única transformação de unidade é NivelFinal cm→m. Números suspeitos/negativos continuam presentes; NaN representa ausência/não-numérico e o texto original permanece noJSONL. Não se aplicou máscara de elegibilidade, interpretação de época/fuso, interpolação, ajuste de curva ou preenchimento.

OsNPZ são acervo normalizado comQC, **não arquivos prontos para o pipeline**. Um futuro builder deve aplicar explicitamente seu protocolo causal/QC e cobertura, mantendo separados dado ausente e valor zero. As duas estações auxiliares sem nível impedem complete24, mas nenhuma política de treino foi alterada aqui.

## ONS reaproveitado,23h59 literal

- Agosto: outputs/historico-ceran-2023-complemento-20260921/ceran-source-values.csv, filtrado apenas por din_instante iniciado em2023-08 para esta auditoria.744registros por usina,31horários23h59 por usina. EsseCSV também contém outros meses; um futuro consumidor precisa selecionar a janela.
- Setembro: outputs/historico-cheia-setembro-2023/ons-ceran-source-values.csv.714registros por usina,30horários23h59 por usina. As lacunas previamente conhecidas não foram preenchidas.
Ambos osCSVs coincidem com os hashes dos manifestos originais; oCSV bruto deagosto e oParquet desetembro também foram conferidos. ons-references.json inclui links oficiais, metadados prévios e hashes. Foi lida apenas a coluna din_instante; a coluna histórica hour_end_interpreted_assumed doCSV deagosto foi ignorada. Nenhum23h59 foi convertido para00h e nenhum download ONS foi realizado.

## Limites e arquivos

Nenhuma previsão meteorológica foi coletada ou substituída por reanálise/chuva futura. O acervo apenas permite desenhar depois um estudo observado de120campos. Não foram montados acumulados regionais, matriz, alvos, treino ou inferências. Fuso histórico, disponibilidade na emissão, referência vertical e comparabilidade dos regimes permanecem não certificados. Setembro2023 já foi inspecionado e não é um holdout novo.

Scripts: collect.py --plan registra o plano; collect.py --collect respeita sidecars existentes e não repete pedidos; audit.py processa apenas fontes locais; finalize.py verifica a normalização, hashes e este relatório. Não executar novamente o plano existente. source-manifest.json e ons-references.json vinculam fontes completas; coverage.json e qc-summary.csv detalhamQC/cadências/lacunas; validation.json registra verificações; artifact-hashes.json cobre os artefatos próprios.

**320 verificações de integridade/normalização passaram.** Nenhum arquivo anterior, modelo, pipeline ou automação foi alterado. Sem HGE/ARNO, promoção ou comunicação externa.
