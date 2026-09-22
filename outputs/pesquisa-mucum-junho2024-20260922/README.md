# Muçum — nova janela documental de junho/2024

A sondagem encontrou uma série completa de **672 níveis aprovados a cada 15 minutos**, entre **15/06/2024 00:00 e 21/06/2024 23:45**, estação ANA **86510000**. O máximo discreto é **17,69 m em 17/06/2024 13:15**, horário literal; não representa certificação do pico contínuo. É uma janela potencial para nova avaliação experimental, distinta de abril–01/maio/2024 já usado. Nesta rodada houve apenas pesquisa, uma sondagem de nível e auditoria de disponibilidade: nenhuma matriz, inferência, ajuste ou promoção.

## Fontes oficiais e confronto

A lista SGB já preservada indicou boletins de 16–20/06 antes de qualquer consulta direta nova. Foram obtidos somente:

- [Boletim SGB de 17/06/2024 às 22h](https://www.sgb.gov.br/sace/boletins/Taquari/20240617_22-20240617%20-%20231329.pdf): Muçum 1590 cm, também identificado por código na p.2.
- [Boletim SGB de 20/06/2024 às 07h](https://www.sgb.gov.br/sace/boletins/Taquari/20240620_07-20240620%20-%20091414.pdf): Muçum 879 cm.
- [ANA, consulta legada de 15–21/06/2024](https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?codEstacao=86510000&dataInicio=15%2F06%2F2024&dataFim=21%2F06%2F2024): HTTP200, 563465 bytes, 672 registros.

Os dois pontos do boletim coincidem exatamente com `NivelFinal` no XML atual. A unidade cm é explícita nos boletins; o XML não traz unidade junto ao campo. Apenas a apresentação do nível neste relatório divide por100. Campos brutos e horários originais não foram alterados.

O boletim de20/06 tem narrativa dizendo Muçum acima do alerta, apesar de tabela/gráfico879cm e alerta900cm. Preservamos essa inconsistência editorial; não trocamos valores nem a classificamos como metadado de qualidade. O máximo discreto da semana está abaixo do limiar de inundação1800cm apresentado nesses boletins; o episódio é de elevação/cheia monitorada, sem certificação aqui de inundação urbana em Muçum.

## Cobertura e QC

| Item | Resultado |
|---|---:|
| Registros / timestamps únicos | 672 /672 |
| Intervalos consecutivos de900s | 671 |
| Horas exatas | 168 |
| Lacunas na grade esperada / duplicatas / conflitos | 0 /0 /0 |
| `NivelFinal` e `NivelSensor` finitos e aprovados | 672 em cada campo |
| Níveis nulos / negativos / zeros | 0 /0 /0 |
| Faixa de `NivelFinal` | 124–1769cm |
| `ChuvaFinal` / `VazaoFinal` finitos e aprovados | 672 /672 |
| `NivelManual` e `NivelDisplay` | ambos nulos em672 registros |

ALL-QC e todos os campos originais estão em `ana-86510000-all-qc.jsonl`, ordenados sem arredondar, com arquivo/hash/índice XML1-based. A auditoria reconcilia integralmente JSONL↔XML. `summary.json` contém também QC dos campos acessórios, sem afirmar que vazão reportada é medição física independente nem certificar a semântica da chuva nesta rodada.

Apenas como teste de disponibilidade do contrato existente: em168 origens horárias, com âncora consultada emO−15min e idade máxima15min, alvo no horário exato e ambos níveis aprovados, há **166/161/155 pares emh1/6/12**, respectivamente. Em cada horizonte há126 pares com alvo≥7m, limiar analítico sem relação automática com alerta oficial. A primeira origem não tem a margem anterior nesta sondagem; as últimas h origens excedem a janela e são excluídas explicitamente. Não houve adaptação da grade ou preenchimento. Esses números não atestam disponibilidade dos120/180 preditores nem constituem avaliação de previsão.

## Continuidade e regime permanecem pendentes

Os dois boletins avisam, na p.3, que sensores e plataformas foram perdidos na cheia de maio, comprometendo previsões enquanto eram reinstalados. Linha José Júlio aparece sem nível, com indicação de manutenção. Eles não dão data de reinstalação, identificação do sensor de Muçum ou nivelamento ligando réguas anteriores/novas. Dados atuais aprovados e dois valores coincidentes não resolvem essas lacunas nem certificam que a versão consultada estava disponível em tempo real em2024. O aviso genérico também não permite afirmar que o sensor específico de Muçum permaneceu desligado durante toda a semana.

As cotas dos boletins usam referência local da régua. O acervo anterior mantém não conciliados os zeros publicados33,985m e33,96m, sem vigência que permita certificar equivalência apósmaio. Não aplicamos offset. `DataHora` permanece literal, sem timezone no XML; não há novo contrato explícito do serviço legado, horário de publicação ou histórico de revisão. UTC−03 não foi elevado de hipótese a certificação.

Contexto operacional primário já existente, sem novo download:

- [ONS, reunião09/05/2024, p.12](https://www.gov.br/ana/pt-br/assuntos/monitoramento-e-eventos-criticos/eventos-criticos/apresentacoes-das-reunioes/apresentacao-ons-sala-crise-sul-2024_05_09.pdf): perda de comunicação/estações emmaio, dano no vertedouro de14deJulho e envio de dados medidos e/ou estimados. O relato também informa retorno deCastroAlves em07/05; não é um calendário operacional completo de junho.
- [CERAN, balanço de04/05/2026](https://ceran.com.br/sem-categoria/ceran-atualiza-a-situacao-das-usinas-hidreletricas-apos-2-anos-das-cheias/): cota operacional de14deJulho recuperada emdezembro/2024, obras concluídas emmarço/2025. Logo junho situa-se entre a avaria e a restauração descritas. Não inferimos sua curva ou vazão operacional a partir dessas datas; MonteClaro também sofreu inundação da casa de força.

A semana tem resolução e níveis úteis para investigar diversidade/intensidade, mas o conjunto de entradas de montante/chuva/ONS, o regime efetivo e os metadados da régua precisam de protocolo próprio antes de treinamento ou comparação. Não é automaticamente um teste independente; seus níveis já foram inspecionados nesta pesquisa. Nenhum resultado comprova98%.

## Encerramento e reprodução

Escopo fechado: **4 buscas oficiais e3 GETs pequenos**, sem retentativas ou expansão. O quarto GET autorizado não foi necessário. `plan.json` foi escrito antes das consultas diretas; `search-results.json` preserva o resultado das buscas. Os três corpos/headers/URLs e horários reais UTC estão em `raw/*.receipt.json` e `source-manifest.json`; documentos reutilizados são referenciados por hash em `reused-source-hashes.json`, com recibos originais apontados. Data da coleta:22/09/2026.

`python3 audit.py` reconstrói apenas os artefatos locais de auditoria. `collect.py` existe como registro e respeita recibos existentes; não é necessário executá-lo novamente. `manifest.json` e `manifest-check.json` selam os artefatos desta pasta. Não foi encontrada licença de redistribuição específica nos corpos novos; uso local de fontes públicas com atribuição, sem publicação dos arquivos em serviço externo. Arquivos operacionais e acervos anteriores permanecem intocados.
