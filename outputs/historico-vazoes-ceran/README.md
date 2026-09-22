# CERAN: vazões ONS horárias de julho/2020 e maio/2024

Coleta pública em 21/09/2026. Auditoria de disponibilidade e qualidade, sem incorporação ao treino. Arquivos originais, URL, instante de coleta, cabeçalhos HTTP e SHA-256 estão em `raw/` e `source-manifest.json`; extração reproduzível em `extract_audit.py`. Foram obtidos os dois Parquets mensais completos (1.137.491 e 1.280.788 bytes), filtrados apenas os três identificadores abaixo. Os catálogos de nomes/contagens de todas as usinas estão em `inventory-*.csv` para auditar a identificação; nenhuma série adicional foi extraída.

## Identificação e cobertura

| Usina | Identificador ONS | Código de otimização | Mês | Linhas / 744 horas | Afluência não nula | Defluência não nula | Horas sem linha* |
|---|---|---:|---|---:|---:|---:|---:|
| 14 DE JULHO | JIUHQJ | 99 | 2020-07 | 744 | 744 | 744 | 0 |
| MONTE CLARO | JIUHMC | 98 | 2020-07 | 744 | 744 | 744 | 0 |
| CASTRO ALVES | JIUHCA | 97 | 2020-07 | 744 | 744 | 744 | 0 |
| 14 DE JULHO | JIUHQJ | 99 | 2024-05 | 552 | 525 | 552 | 192 |
| MONTE CLARO | JIUHMC | 98 | 2024-05 | 554 | 525 | 553 | 190 |
| CASTRO ALVES | JIUHCA | 97 | 2024-05 | 564 | 530 | 563 | 180 |

São **3.902 linhas selecionadas**, com nomes/códigos concordantes nos dois meses. A coluna de bacia do fornecedor contém `JACUI`; foi preservada, sem substituir automaticamente pela denominação hidrológica local. Não há duplicações dos timestamps das três usinas. Detalhes por campo, zeros, extremos, lacunas e balanço em `summary.json`.

\*Grade interpretada: cada dia tem horas-fim 01h…23h e o registro 23:59 tratado provisoriamente como fechamento de 24h. O valor original permanece intacto. Este tratamento é uma inferência explicitamente marcada, não contrato confirmado do exportador.

## Problemas concretos de qualidade

**O pico de maio/2024 não está coberto.** 14 de Julho e Monte Claro não possuem linhas de 01/05 às 10h até 05/05 às 01h (88 fechamentos horários); Castro Alves, de 01/05 às 11h até 05/05 às 01h (87). Há outras lacunas longas após isso. Não interpretar máximo disponível do arquivo como máximo real do evento, nem interpolar este apagão.

**Julho/2020 tem linhas completas, mas zeros suspeitos no pico.** Em 08/07, 14 de Julho registra afluência zero às 10–15h e defluência zero às 10–17h; Monte Claro registra afluência zero às 04–18h e defluência zero às 05–18h. São valores fornecidos, não nulos preenchidos pelo coletor. A plausibilidade precisa de confirmação externa.

O teste diagnóstico `Qdef − Qtur − Qvert − Qoutras`, somente quando todas as componentes são informadas, encontra oito divergências acima de 1 m³/s em 14 de Julho em julho/2020. Às 17h de 08/07, Qdef=0, Qvert=9.971 e Qoutras=37, resultando em residual −10.008 m³/s. Em maio/2024 são 326, 325 e 326 linhas acima desse limiar, respectivamente em 14 de Julho, Monte Claro e Castro Alves, com residuais absolutos máximos de 19, 18 e 20 m³/s. Os detalhes estão em `balance-review-*.csv`. O limiar é diagnóstico local, não aprovação/reprovação oficial; não foi somada ou subtraída componente para alterar a fonte. Balanço consistente tampouco valida os zeros de Monte Claro.

## Semântica, unidades e tempo

O [catálogo ONS](https://dados.ons.org.br/dataset/dados_hidrologicos_ho) declara que esta base horária reproduz dados dos agentes, não consistidos pelo ONS, sujeitos a lacunas e revisões. O [dicionário](https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/dados_hidrologicos_ho/DicionarioDados_DadosHidrologicosHorarios.pdf) define vazões em **m³/s**, níveis em metros e volume útil em percentual. O catálogo usa **hora-fim**: 01h representa a hora anterior. O PDF do dicionário usa a palavra “consolidados” em sua descrição, mas isso não deve sobrepor a advertência explícita de qualidade do catálogo atual. Licença anunciada: Creative Commons Atribuição; creditar ONS e explicitar transformações.

A rotina primária ONS **RO-AO.BR.02, revisão08, vigência02/07/2024**, preservada em `raw/ons-RO-AO-BR02-rev08.pdf`, pp.3–5, define defluência como a soma liberada por turbinas, vertedouro e outras estruturas. Transferência é separada. Afluência é obtida por balanço hidráulico, incluindo alteração de armazenamento; não equivale necessariamente a medição direta nem vazão natural sem ação das usinas. A seção4 estabelece **horário oficial de Brasília** para os registros da rotina e descreve tratamento de horário de verão. A seção5.1.6 estabelece envio após fechar a hora. [Fonte ONS](https://www.ons.org.br/%2FMPO%2FDocumento%20Normativo%2F4.%20Rotinas%20Operacionais%20-%20SM%205.13%2F4.3.%20Rotinas%20P%C3%B3s-Opera%C3%A7%C3%A3o%2F4.3.2.%20Apura%C3%A7%C3%A3o%20de%20Dados%2FRO-AO.BR.02_Rev.08.pdf).

**Limite da confirmação:** a convenção Brasília está explicitamente documentada para a rotina, mas a revisão consultada é posterior aos dois meses coletados. Não foi encontrada nesta rodada declaração do exportador Parquet que garanta continuidade histórica ou explique `23:59`. Os timestamps do Parquet não trazem offset. Por isso a derivação UTC está nomeada `hour_end_utc_assuming_brasilia`, com status de vínculo exportador/período ainda pendente. Nos meses coletados, `America/Sao_Paulo` resulta em UTC−03 segundo a base de fusos local. O arquivo fonte nunca foi deslocado.

## Arquivos e uso posterior

- `ceran-2020-07-source-values.csv`, `ceran-2024-05-source-values.csv`: somente filtro e ordenação; todas as colunas e valores originais preservados.
- `ceran-all-interpreted.csv`: mesmos valores, mais colunas derivadas de intervalo/fuso com hipóteses explícitas e status `AGENT_REPORTED_NOT_VALIDATED_BY_ONS`.
- `summary.json`: contagens, intervalos sem dados por variável, zeros e diagnóstico de balanço; nenhuma linha marcada “aprovada”.
- `extract_audit.py`: processamento offline; requer pandas e DuckDB1.4.4. O DuckDB foi usado em dependência temporária dentro desta pasta, sem alterar o ambiente compartilhado; o diretório temporário foi removido após a extração.

Para auditoria futura, priorizar Castro Alves/2020, cuja série não apresenta zeros em afluência/defluência e passa o diagnóstico de balanço; isso não constitui validação física. Para Monte Claro e 14 de Julho, obter esclarecimento dos zeros de 08/07/2020 e dados faltantes de 01–05/05/2024. Canal público ONS do catálogo: `relacionamento.agentes@ons.org.br`; referência complementar pública CERAN: https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHCA.php. Nenhum contato foi realizado.

A base histórica baixada em 2026 não contém instantes de disponibilização original nem versões conhecidas ao vivo. Não usar vazão futura observada ou revisão posterior como se estivesse disponível ao emitir uma previsão passada. Este lote não foi destinado a treino/teste, não promoveu modelo e não comprova 98% de acerto.

Contexto adicional: ver `operational-context.md` para perda de comunicação e avarias em maio/2024, restauração2024–2025 e obrasCastroAlves desde novembro2025, confirmadas em fontes ONS/CERAN.
