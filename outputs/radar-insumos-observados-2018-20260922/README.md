# ANA observado2018 —27postos, duas janelas de10dias

Acervo fechado de27/08–05/09 e27/09–06/10/2018; os três primeiros dias de cada janela são aquecimento. Somente coleta pública e auditoria de campos/QC/cobertura: nenhum modelo, matriz, previsão, NWP, ONS ou mudança de contrato operacional.

Plano anterior à rede,54GETs novos com até2conexões e sem retries/redirecionamento automático. Oito XMLs centrais foram reutilizados integralmente porhash, inclusive quatro respostas Sem dados. Todas as62respostas retornaram HTTP200:42 contêm registros e20 retornam mensagem explícita Sem dados. Nenhuma falha de rede/HTTP nesta rodada. Ausência no endpoint não prova ausência em todos os acervos.

Foram9626 registros brutos e9626 linhas ALL-QC, sem duplicatas idênticas para unir nem timestamps conflitantes. Campos originais permanecem no topo do JSONL; textos/valores não foram convertidos. Elementos XML vazios são null, distintos de campos inexistentes e de zero numérico reportado. `source_file`, `source_sha256`, `source_record_index`(1-based) e `source_references` preservam a origem de cada linha. O algoritmo só une dicionários originais integralmente idênticos; conflitos seriam separados em `conflicts.json` e não resolvidos.

| Janela | Linhas | NivelFinal finito/aprovado | ChuvaFinal finita/aprovada |
|---|---:|---:|---:|
|27/08–05/09|4866|4808|4860|
|27/09–06/10|4760|4648|4757|

Esses são totais de registros de postos/resoluções diferentes, não amostras equivalentes de treino, horas integráveis ou chuva acumulada regional. As nove linhas de chuva não aprovadas/vazias continuam preservadas. Há dois ChuvaFinal vazios, ambos em Muçum na segunda janela, nenhuma chuva numérica negativa. Zero reportado é mantido; ausência nunca foi preenchida comzero.

Oito postos têm Sem dados em ambas as janelas:86060010,86125000,86125050,86160000,86280500,86472600,86500000,86504900. Cada série vazia tem seu JSONL vazio vinculado ao status/recibo; contagem de campos vazios igualzero em uma série sem linhas NÃO indica disponibilidade ou chuva zero.

Linha José Júlio86472000 tem956/960 linhas de15min, todas de nível/chuva aprovados; a primeira mantém lacuna05/09 15:45–16:30. Muçum86510000 tem240 horários porjanela, níveis aprovados236/237; registros de QC não aprovado continuam nas séries. Não alteramos a incompatibilidade já documentada da âncora operacionalO−15min na grade horária deMuçum.

Cuidados de cadência: a maioria dos demais postos com dados apresenta moda3600s; isso não certifica grade completa. 86200900 tem48/59 registros, moda4h/3h, diversos intervalos maiores (até39h/20h); não pode ser tratado como série horária completa ou chuva integrada sem contrato específico. 86450000 começa apenas31/08 13h na primeira janela; na segunda há241registros porque inclui **04/10/2018 23:01:00**, valor literal adicional, que não foi arredondado, excluído ou unido ao23h. 86495500 sótem23registros na segunda janela, até27/09 22h. As grades de900/3600s em `coverage.json` são diagnóstico de presença exata; os buracos de15min de uma estação horária não são necessariamente falha do fornecedor.

Tabela porposto/janela (aprovação exige texto explícito Dado aprovado e valor finito; todosQC originais permanecem disponíveis):

| Janela início | Posto | Registros | Moda(s) | Nível aprovado | Chuva aprovada | Chuva vazia | Chuva numérica com outroQC |
|---|---|---:|---:|---:|---:|---:|---:|
|2018-08-27|86060010|0|None|0|0|0|0|
|2018-08-27|86099000|240|3600|240|240|0|0|
|2018-08-27|86102000|240|3600|240|240|0|0|
|2018-08-27|86117000|225|3600|225|225|0|0|
|2018-08-27|86125000|0|None|0|0|0|0|
|2018-08-27|86125050|0|None|0|0|0|0|
|2018-08-27|86160000|0|None|0|0|0|0|
|2018-08-27|86163000|240|3600|240|240|0|0|
|2018-08-27|86200900|48|14400|48|48|0|0|
|2018-08-27|86280500|0|None|0|0|0|0|
|2018-08-27|86298000|151|3600|151|151|0|0|
|2018-08-27|86403000|240|3600|240|240|0|0|
|2018-08-27|86410800|240|3600|240|240|0|0|
|2018-08-27|86447000|240|3600|240|240|0|0|
|2018-08-27|86448000|240|3600|240|240|0|0|
|2018-08-27|86450000|131|3600|131|131|0|0|
|2018-08-27|86471000|240|3600|240|240|0|0|
|2018-08-27|86472000|956|900|956|956|0|0|
|2018-08-27|86472600|0|None|0|0|0|0|
|2018-08-27|86479000|240|3600|240|240|0|0|
|2018-08-27|86488000|240|3600|186|240|0|0|
|2018-08-27|86493000|239|3600|239|239|0|0|
|2018-08-27|86495500|236|3600|236|236|0|0|
|2018-08-27|86500000|0|None|0|0|0|0|
|2018-08-27|86504900|0|None|0|0|0|0|
|2018-08-27|86505500|240|3600|240|240|0|0|
|2018-08-27|86510000|240|3600|236|234|0|6|
|2018-09-27|86060010|0|None|0|0|0|0|
|2018-09-27|86099000|240|3600|240|240|0|0|
|2018-09-27|86102000|240|3600|240|240|0|0|
|2018-09-27|86117000|240|3600|240|240|0|0|
|2018-09-27|86125000|0|None|0|0|0|0|
|2018-09-27|86125050|0|None|0|0|0|0|
|2018-09-27|86160000|0|None|0|0|0|0|
|2018-09-27|86163000|240|3600|148|240|0|0|
|2018-09-27|86200900|59|10800|59|59|0|0|
|2018-09-27|86280500|0|None|0|0|0|0|
|2018-09-27|86298000|120|3600|120|120|0|0|
|2018-09-27|86403000|240|3600|240|240|0|0|
|2018-09-27|86410800|240|3600|240|240|0|0|
|2018-09-27|86447000|239|3600|239|239|0|0|
|2018-09-27|86448000|239|3600|239|239|0|0|
|2018-09-27|86450000|241|3600|241|241|0|0|
|2018-09-27|86471000|240|3600|240|240|0|0|
|2018-09-27|86472000|960|900|960|960|0|0|
|2018-09-27|86472600|0|None|0|0|0|0|
|2018-09-27|86479000|240|3600|240|240|0|0|
|2018-09-27|86488000|240|3600|223|240|0|0|
|2018-09-27|86493000|239|3600|239|239|0|0|
|2018-09-27|86495500|23|3600|23|23|0|0|
|2018-09-27|86500000|0|None|0|0|0|0|
|2018-09-27|86504900|0|None|0|0|0|0|
|2018-09-27|86505500|240|3600|240|240|0|0|
|2018-09-27|86510000|240|3600|237|237|2|1|

## Arquivos e limites

`stations/2018-08-27/ana-COD-all-qc.jsonl` e `stations/2018-09-27/ana-COD-all-qc.jsonl`:54 séries ordenadas, inclusive16vazias. `raw/`: respostas integrais, recibos e54registros de tentativa; `source-manifest.json` conserva coleta/URL/headers/UTC/hash e links de reuso, `source-status.json` distingue parsed/no_data_api/falhas e guarda mensagens. `coverage.json`, `field-coverage.csv` e `daily-coverage.csv` resumem campos,QC,cadências e lacunas; `conflicts.json` está vazio. `prepare.py` registra o escopo; `collect.py` respeita recibos/tentativas existentes, nunca repete erro automaticamente; `audit.py` verifica todos os registros XML↔JSONL, inclusive proveniência.

Os cabeçalhos HTTP e horários de coleta não certificam primeira publicação ou revisões históricas. Timestamps são literais sem aplicação de fuso/DST; referência vertical/unidade contratual/continuidade da régua não foram verificadas nesta rodada. A Linha aparece em manutenção no boletim contemporâneo02/09, mas o acervo recuperado agora contém níveis aprovados: não confundir acesso retrospectivo com disponibilidade emtempo real. Os dados permanecem observados, não previsão meteorológica.

Nenhum atraso/peso foi ajustado, nenhuma grade foi interpolada, nenhum campo foi imputado. A cobertura não é avaliação de precisão e não torna a meta98% atingida. Admissibilidade de treino e de chuva integrada ficará para protocolo separado.

Verificação final: **319 checks passaram**,62 hashes de fontes revisados ao final,54 novas tentativas dentro do plano,9626 registros XML representados exatamente uma vez. Manifesto próprio verifica todos os artefatos após esta auditoria.
