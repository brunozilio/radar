# Insumos hidrológicos de 2024 para pesquisa do Radar

**Coleta concluída; matriz de treinamento ainda não montada.** Foram preservados **29.449 registros ANA de 27 estações consultadas** e **6.060 linhas ONS das três usinas**. O lote expõe uma limitação decisiva: Carreiro não tem dados no endpoint durante o período inteiro. Manter o filtro original de 24 entradas iniciais completas admitiria **zero** origens novas.

## Escopo e coleta

O protocolo anterior à coleta está em `protocol.json` e `docs/radar-inputs-2024-collection-protocol.json`. Potenciais origens: 01/04/2024 a 01/05/2024, com alvos antes de 02/05. ANA foi consultada de 29/03 a 01/05, inclusive, preservando margem para históricos de até 48h e atrasos. Essa delimitação antecede a avaria reportada para 02/05, mas não certifica equivalência do regime com 2026.

Foram **80 requisições públicas novas**: 78 XMLs ANA (26 estações × três janelas mensais) e dois Parquets ONS de março/abril. Os três XMLs Muçum e o Parquet ONS de maio foram reutilizados com hash verificado. As 84 fontes têm URL, hash e origem/horário de coleta ou referência de reutilização em `source-manifest.json`. Todos os downloads terminaram; 10 respostas ANA HTTP200 contêm “Sem dados”. Elas permanecem preservadas e não foram tratadas como chuva ou nível zero.

## Níveis necessários ao Radar

Janela retida: 29/03 00h a 01/05 23h59, horários originais sem fuso explícito.

| Posto | Registros | Níveis aprovados | Vazios | Suspeitos |
|---|---:|---:|---:|---:|
| Muçum, 86510000 | 3.264 | 3.264 | 0 | 0 |
| Linha José Júlio, 86472000 | 3.264 | 3.175 | 84 | 5 |
| Santa Tereza, 86472600 | 3.260 | 3.232 | 26 | 2 |
| Carreiro, 86500000 | 0 | 0 | 0 | 0 |

Santa Tereza também tem quatro timestamps ausentes em 29/03, 21h–21h45. Carreiro não tem uma série preenchida com valores vazios: são três respostas explícitas sem registros. O agente reconstruiu somente os primeiros 24 campos, com atrasos 15/30/15/30min: **0/744 origens** satisfazem complete24, enquanto os outros 18 campos estariam completos em 683 origens. Essa reconstrução isolada não monta os 180/204 preditores e não constitui treino.

As dez respostas sem dados são três de cada estação 86493000, 86500000 e 86504900, mais uma de 86479000 em 01/05. Não há evidência nesta coleta de que repetir imediatamente a mesma consulta recuperaria dados. Não foram usados canais autenticados nem tentativas de contorno.

## Chuva e qualidade

`ana-coverage.csv` separa valores numéricos, aprovados e compatíveis com a regra atual do parser. O parser atual pode aceitar número sem QC, mas **não há números sem QC neste lote**; ainda assim as categorias foram mantidas distintas. Números negativos, limites de chuva e classificações originais são preservados para revisão. As estações 86200900 e 86495500 têm rótulos de chuva “Dado aprovado”, mas todos os valores ChuvaFinal estão vazios: rótulo de qualidade sem número não constitui observação.

A coluna de 3.264 slots de 15min é uma referência de grade densa, **não um denominador universal de disponibilidade**. Várias estações são horárias; quatro têm exatamente 816/816 registros horários na janela. A estação 86125000 tem cadência modal de 30min e timestamps com segundos `:02`, preservados. `ana-cadence.csv` registra distribuições de intervalos; não se copiou uma chuva horária para quatro intervalos de 15min.

As ponderações espaciais de `chuva-pesos.json` foram somente usadas para escolher as mesmas 27 estações. Ainda será necessário calcular a cobertura ponderada por bacia e janela, com as regras de acumulação/latência do candidato. Ausência não foi preenchida com chuva zero ou reanálise.

## ONS e reservatórios

Foram extraídos somente JIUHQJ, JIUHMC e JIUHCA, com nomes/códigos verificados. Março tem 744 linhas por usina; abril tem 718 em Julho e 720 nas outras duas. Maio preserva 552/554/564, incluindo lacunas e valores fornecidos anteriormente auditados. As duas lacunas adicionais de abril em Julho permanecem sem preenchimento. A seleção total é 6.060 linhas.

Os horários originais, inclusive 23h59, permanecem literais. Não foram convertidos em 00h, balanceados componentes, corrigidos zeros, inferidos volumes ou removidos extremos. A extração de maio inclui o mês inteiro para preservar o mesmo produto fonte; isso **não admite** automaticamente datas posteriores a 01/05 nas origens ou alvos de um experimento.

`ons-coverage.csv` descreve presença/ausência, zeros e extremos por campo. A extração usa DuckDB 1.4.4 em diretório temporário, removido após a auditoria, sem alterar runtimes compartilhados. `ons-auditor.py` e `ons-audit.json` preservam código/versão/hashes; a reprodução requer esse pacote em ambiente isolado e não precisa de nova coleta.

## Meteorologia e próxima etapa

O lote complementar em `../radar-insumos-2024-meteorologia-20260921/` preservou **12.600 valores finitos**, três modelos × cinco pontos × 840 horas. Todas as **44.640 janelas** de 3/6/9/12h estão completas nas 744 origens de abril–01/05. As 15 grades retornadas coincidem com as do acervo Radar, com mm e UTC−3 conferidos. A data de publicação histórica de cada previsão permanece não certificada.

Agora é possível montar uma matriz experimental com ausências explícitas. O contraste correto para avaliar o acréscimo usa uma referência que já aceite entradas incompletas; adicionar o lote ao filtro original complete24 não adicionaria treino. Isso não autoriza promoção: primeiro conferir a matriz completa, cobertura da chuva, derivados, cortes e referências; depois comparar com controles congelados sob protocolo novo. Os resultados anteriores do treino com faltas foram mistos e não se tornam positivos só porque há mais dados.

## Limites e integridade

Os originais e todas as classificações foram preservados em `raw/`, referências reutilizadas e `stations/*-all-qc.jsonl`. Não foi produzida normalização para inferência. Os 84 hashes das fontes e 13 artefatos meteorológicos foram conferidos pelo coordenador; o agente reconferiu os 81 XMLs ANA e os quatro postos de nível. Os valores continuam sujeitos a fuso, datum, revisão, sensor e regime operacional não certificados. QC aprovado não resolve esses pontos.

**Nenhum modelo foi treinado, promovido ou alterado na operação. A meta de 98% permanece não demonstrada.**
