# Passo Carreiro: busca limitada para 21–22/07/2026

**Não foi recuperada uma série horária/sub-horária aprovada alternativa que preencha a lacuna de nível ANA 86500000.** Foram quatro buscas e cinco consultas diretas públicas, sem autenticação, contato com terceiros, interpolação, ajuste ou importação no modelo. A conclusão é limitada aos caminhos consultados; não significa inexistência de dados em outros bancos ou arquivos do operador.

## ANA: registros existem, mas o sensor está reprovado

A [consulta pública ANA dos dois dias](https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?codEstacao=86500000&dataInicio=21%2F07%2F2026&dataFim=22%2F07%2F2026) respondeu HTTP200, com 192 registros distintos identificados como estação 86500000, de `2026-07-21 00:00:00` a `2026-07-22 23:45:00`, a cada 15 minutos literais.

- `NivelSensor`: 192 valores numéricos, todos com `CQ_NivelSensor = Dado reprovado`.
- `NivelFinal`: 188 valores vazios com QC vazio; quatro valores aprovados.
- `NivelManual`: os mesmos quatro valores aprovados; demais 188 vazios.
- `NivelDisplay`: 192 vazios, QC vazio.

| DataHora literal | NivelFinal / NivelManual (cm, convenção do acervo) | QC de ambos |
|---|---:|---|
| 2026-07-21 07:00:00 | 236.00 | Dado aprovado |
| 2026-07-21 17:00:00 | 570.00 | Dado aprovado |
| 2026-07-22 07:00:00 | 840.00 | Dado aprovado |
| 2026-07-22 17:00:00 | 852.00 | Dado aprovado |

Os 192 registros novos são **idênticos em todos os campos** aos mesmos horários do XML `outputs/mucum-propagacao-2026-09-21/raw/ana-86500000.xml`. Não houve recuperação por revisão entre essas duas capturas. Esses quatro níveis já estavam no acervo; são leituras pontuais, com intervalos de 10/14 horas, não uma série contínua de nível aprovado. O sensor reprovado não foi tratado como observação válida nem usado para preencher `NivelFinal`.

O XML e `ana-all-fields-original.jsonl` preservam todos os valores e QC, sem conversão, com índice XML 1-based e hash da origem. `ana-comparison.json` contém contagens por campo e a comparação de versões. Não houve arredondamento de timestamps, preenchimento com zero ou inversão de curva-chave. A existência de vazão reportada não autoriza reconstruir nível por uma curva não documentada.

## SGB/SACE

A [exportação pública SACE de Passo Carreiro](https://sace.sgb.gov.br/api/dados/taquari_54_cota.csv) respondeu HTTP200, com **2.878 linhas**, cobrindo apenas `2026-08-22 21:15:00` a `2026-09-22 00:30:00`. Não cobre os dois dias de julho. O GeoJSON público já preservado identifica o ponto 54 como Passo Carreiro, sigla 86500000, coordenadas −51,8325/−28,84888, `fusoHorario=GMT-3`.

O cabeçalho CSV é `data_hora_medicao;indice`, sem QC individual, offset ou unidade explícita. A ausência da janela nessa exportação recente não comprova ausência no banco histórico SACE. A inspeção do JavaScript público já preservado encontrou a chamada do gráfico e a área de download, mas não um contrato documentado de consulta arbitrária de julho. Não foram inventados parâmetros nem chamadas internas, administrativas ou autenticadas.

O valor cadastral `altitude=260` não comprova zero da régua, datum ou continuidade física do sensor em julho. O `GMT-3` do cadastro não certifica por si a conversão histórica da exportação. As ressalvas da pesquisa anterior de fuso permanecem.

## SIGMA e publicação estadual

Os arquivos públicos SIGMA de [21/07](https://sigmameteorologia.com/produtos/stations/2026-07-21/86500000.txt) e [22/07](https://sigmameteorologia.com/produtos/stations/2026-07-22/86500000.txt) retornaram **HTTP404**, com corpos HTML de erro preservados. Não retornaram séries vazias nem dados aprovados. SIGMA é uma republicação pública permitida no escopo desta tarefa; não foi presumida propriedade governamental ou independência em relação ao SGB/ANA.

Limite do inventário: o manifesto antigo `events-fetch-manifest.json` já continha metadados de 404 para essas duas URLs, sem corpos correspondentes. O levantamento inicial verificou arquivos de dados por estação/data e não detectou essas tentativas antes dos dois novos pedidos. Foram, portanto, duas reconsultas explícitas evitáveis, registradas em `sigma-prior-attempts.json`, e não retries automáticos; nesta rodada os corpos de erro foram preservados. Não se fez nova tentativa após os 404.

A [nota oficial estadual de 22/07/2026](https://www3.estado.rs.gov.br/centro-de-monitoramento-da-defesa-civil-do-rs-atualiza-prognostico-de-resposta-hidrologica) documenta chuva intensa na região das nascentes e a resposta esperada dos rios. Não contém série do posto 86500000, pares timestamp/nível ou exportação histórica. É contexto do episódio, não substituto das medições. A busca restrita por Passo Carreiro/Clima RS não devolveu outro caminho útil; isso não esgota o portal estadual.

## Tempo, qualidade e admissibilidade

`DataHora` no legado não traz offset. Os horários foram mantidos literais; UTC−03 continua sendo a hipótese do pipeline, sem nova certificação de contrato. A unidade cm da apresentação acima segue a convenção já usada para os campos ANA; o XML não inclui metadado físico completo de unidade/datum da estação. Horário HTTP `Date`, recebimento local e eventual `Last-Modified` da página não são horário de medição nem prova da primeira publicação desses dados.

Não foi encontrada documentação nova de referência vertical, revisão do zero/sensor ou disponibilidade efetiva dessas observações em cada origem de julho. A comparação atual com a versão antiga não prova que os dados foram publicados ou estavam aprovados no passado. Os QC literais foram preservados, sem supor aprovação irrevogável.

Próximo caminho, caso autorizado em outra etapa: exportação histórica oficial SGB/ANA com os valores originais do sensor, motivo/revisão da reprovação, níveis manuais, referência de régua e registros de recepção/publicação. A nova API Hidroweb exige acesso cadastrado conforme documentação já preservada; não foi acessada com credenciais. Nenhuma solicitação foi enviada. Até haver fonte admissível e protocolo separado, conservar os níveis ausentes e os valores reprovados como tais.

## Preservação

`request-manifest.json` guarda URL, início/fim UTC, status, headers, URL final, tamanho e SHA-256 de cada corpo, inclusive erros; `plan.json` foi escrito antes das consultas diretas. `search-log.json` contém as quatro consultas e resumo da evidência primária encontrada, não a resposta integral da ferramenta de busca. `reused-source-hashes.json` identifica o acervo reutilizado. `audit.py` realizou 15 verificações; `finalize.py` verifica novamente hashes de entradas e gera o manifesto dos artefatos próprios. Todos os registros antigos e modelos foram preservados.
