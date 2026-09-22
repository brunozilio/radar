# Complemento CERAN/ONS 2023 — seis meses

Coleta concluída em 21/09/2026: fevereiro, março, abril, maio, julho e agosto. **13.058 registros** das três usinas, com 13.053 valores finitos de defluência e 13.053 de afluência. Nenhuma interpolação, máscara, ajuste de modelo ou alteração no treino.

Foram baixados exatamente seis CSVs integrais, todos HTTP 200, somando 93.179.889 bytes. Os Parquets foram preteridos porque os runtimes existentes não tinham leitor; os CSVs correspondentes vieram do mesmo catálogo oficial preservado. Janeiro, junho e setembro não foram baixados novamente. URLs, coleta UTC, headers, Content-Length e SHA-256 estão em source-manifest.json; os tamanhos recebidos coincidem com Content-Length.

Fonte e licença: [ONS — Dados Hidráulicos por Reservatório, base horária](https://dados.ons.org.br/dataset/dados_hidrologicos_ho), Creative Commons Atribuição conforme catálogo. Crédito ao ONS e aos agentes reportantes; extração, diagnóstico e hipótese horária são transformações locais.

## Cobertura

Identidades confirmadas nos seis arquivos: Castro Alves JIUHCA/código 97, Monte Claro JIUHMC/98 e 14 de Julho JIUHQJ/99.

| Mês | Horas esperadas por usina | Linhas Castro / Monte / Julho | Q máximo Castro / Monte / Julho, m³/s |
|---|---:|---:|---:|
| Fevereiro | 672 | 668 / 668 / 668 | 258 / 329 / 370 |
| Março | 744 | 744 / 744 / 744 | 453 / 550 / 426 |
| Abril | 720 | 718 / 719 / 719 | 175 / 346 / 370 |
| Maio | 744 | 744 / 744 / 744 | 779 / 1.121 / 1.079 |
| Julho | 744 | 734 / 734 / 734 | 2.630 / 4.343 / 4.568 |
| Agosto | 744 | 744 / 744 / 744 | 192 / 373 / 359 |

Não há timestamps duplicados, nem colisões após a interpretação hora-fim. São 46 horários-usina ausentes: 16 Castro, 15 Monte e 15 Julho. Campos finitos adicionais: nível montante 13.054 e jusante 13.053. Todos os campos originais, inclusive componentes e vazios, permanecem na extração, com arquivo e linha de origem.

Lacunas principais, em horários interpretados de fechamento:

- 17/02, 19–22 h: quatro horas nas três usinas; as 16–18 h contêm oito linhas com campos incompletos.
- 07/04, 15 h: todas; 12/04, 06 h: somente Castro.
- Julho: 01/07 23 h e 02/07 00 h; 19/07 15–17 h; 20/07 02–05 h; 22/07 00 h, nas três usinas.

## Janelas e eventos úteis

O principal acréscimo de cheia é **13/07/2023**: Castro 2.630 m³/s às 06 h, Monte 4.343 às 01 h e Julho 4.568 às 06 h, timestamps originais. Em cada janela de 73 horas centrada nesses picos, Q/I e ambos os níveis estão completos nas três usinas. Não inferir propagação física apenas dos horários dos máximos.

O período contínuo de 02/07 01 h até 19/07 14 h tem 422 horários com Q/I/níveis finitos nas três plantas. Maio também acrescenta evento: Castro 779 em 06/05 23 h, Monte 1.121 em 07/05 02 h e Julho 1.079 em 07/05 05 h.

complete-windows.csv identifica todos os segmentos, inclusive sete segmentos de pelo menos 37 horas com Q/I e níveis nas três usinas. A indicação de margem 24 h passada/12 h futura é apenas cobertura geométrica, não elegibilidade causal ou aprovação de qualidade. A completude não elimina os valores suspeitos abaixo. peak-window-coverage.json documenta os 73 horários em torno de cada máximo mensal.

## Sinais de qualidade preservados

- Oito linhas têm soma de componentes desconhecida porque falta ao menos um componente. Não foram convertidos vazios em zero.
- Nas linhas com componentes completos, não há defluência zero com soma maior que 1 m³/s nem residual absoluto entre total e componentes acima de 1 m³/s. O limiar é diagnóstico local, não certificação oficial.
- Há dois zeros de afluência de Julho: 18/02 19 h, Qdef 97; 11/04 14 h, Qdef 28 m³/s. Sem correção ou interpretação automática.
- Nenhum Q/I/nível negativo ou igual a 9999; nenhum nível ou defluência zero.
- **Revisar jusante de Julho em 13/02 16 h:** 69,00→62,02→69,02 m entre 15,16,17 h, com Qdef 28 e I 12 m³/s constantes; arquivo fevereiro, linhas 36538–36540. Salto suspeito, não invalidado oficialmente e não mascarado.
- O maior salto horário de Qdef é Julho em 12/07 20→21 h: 1.609→2.958 m³/s. Foi mantido como extremo observado, sem supor falha. Os maiores saltos por variável/usina/mês estão em largest-hourly-jumps.csv.

## Tempo, revisão e regime

O [dicionário oficial](https://ons-aws-prod-opendata.s 3.amazonaws.com/dataset/dados_hidrologicos_ho/DicionarioDados_DadosHidrologicosHorarios.pdf) identifica vazões em m³/s, níveis em metros e registro por hora-fim. din_instante está preservado literalmente; somente a auditoria de cobertura interpreta 23:59 como 24:00. Não foi descoberto novo contrato de fuso ou datum. Brasília continua hipótese para eventual pareamento, sem adicionar offset aos timestamps originais.

O catálogo informa dados reportados por agentes, não consistidos pelo ONS, sujeitos a lacunas e revisões. Last-Modified dos seis arquivos é 13/02/2025; logo, o conteúdo não prova a versão disponível em 2023 nem o instante original de publicação. Não há flags oficiais de aprovação individual nesta extração.

Todo o lote é anterior às avarias de maio/2024. A [apresentação ONS de 09/05/2024](https://www.gov.br/ana/pt-br/assuntos/monitoramento-e-eventos-criticos/eventos-criticos/apresentacoes-das-reunioes/apresentacao-ons-sala-crise-sul-2024_05_09.pdf) preservada documenta perda de comunicação em 01/05 e rompimento parcial do vertedouro de Julho em 02/05. A [nota CERAN de 04/05/2026](https://ceran.com.br/sem-categoria/ceran-atualiza-a-situacao-das-usinas-hidreletricas-apos-2-anos-das-cheias/) descreve recuperação posterior e obras. Conservar identificação pré-avarias e avaliar transferência ao regime 2025–2026 separadamente. Não converter níveis em volume ou inferir armazenamento instantâneo.

## Admissibilidade

O lote está pronto para definir um experimento separado de vazões com causalidade/latência presumida explícitas e cortes temporais fixados antes do ajuste. Não basta para validar níveis de Muçum: faltam alvos ANA compatíveis. Estes períodos já foram inspecionados e não são um novo teste cego. A janela de julho merece prioridade por cobertura e amplitude; o valor suspeito de fevereiro exige regra geral de QC previamente definida, sem escolher máscaras pelo erro do modelo.

Arquivos de apoio: catalog.json (estatísticas por variável), ceran-source-values.csv (originais selecionados), missing-hours.csv, semantic-review.csv, duplicate-source-rows.csv, reservoir-inventory.csv, selected-resources.json, reused-documentation.json (fontes anteriores e hashes), collect.py/audit.py e artifact-hashes.json.

