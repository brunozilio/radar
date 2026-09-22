# Extensão CERAN anterior a setembro/2023

Pesquisa limitada em 21/09/2026: **existe um caminho público concreto para ampliar janeiro–agosto/2023**. Foram verificados somente dois recursos mensais novos do ONS, janeiro e junho, com resposta HTTP 200, fonte integral preservada e SHA-256. O acervo anterior tinha julho/2020, setembro/2023, maio/2024 e 2025–2026; não foram encontrados os meses janeiro–agosto/2023 já baixados, evitando duplicação.

## Evidência obtida

Fonte: [ONS — Dados Hidráulicos por Reservatório, base horária](https://dados.ons.org.br/dataset/dados_hidrologicos_ho). O catálogo já preservado lista oito Parquets mensais de janeiro a agosto. A existência das três usinas e das variáveis foi confirmada diretamente nos CSVs de janeiro/junho; nos seis outros meses ainda é disponibilidade catalogada, não cobertura auditada.

| Mês | Usina / ID / código | Linhas / esperadas | Q / I / nível montante / jusante presentes | Máximo Q defluente |
|---|---|---:|---:|---:|
| Janeiro | Castro Alves / JIUHCA / 97 | 739 / 744 | 739 / 739 / 739 / 739 | 130 m³/s |
| Janeiro | Monte Claro / JIUHMC / 98 | 739 / 744 | 739 / 739 / 739 / 739 | 194 m³/s |
| Janeiro | 14 de Julho / JIUHQJ / 99 | 739 / 744 | 739 / 739 / 739 / 739 | 198 m³/s |
| Junho | Castro Alves / JIUHCA / 97 | 718 / 720 | 717 / 717 / 717 / 718 | 1.687 m³/s |
| Junho | Monte Claro / JIUHMC / 98 | 718 / 720 | 718 / 718 / 718 / 718 | 2.558 m³/s |
| Junho | 14 de Julho / JIUHQJ / 99 | 718 / 720 | 718 / 718 / 718 / 718 | 2.850 m³/s |

São 4.371 linhas selecionadas, sem timestamps duplicados. Em junho, os máximos ocorrem em 16/06, às 17 h Castro,18 h Monte e 20 h Julho; horários originais. A janela 15–17/06 contém 72 linhas de cada usina, todas com Q/I. Não inferir tempos de propagação apenas da diferença dos picos.

Janeiro oferece condições observadas de vazões menores; junho acrescenta uma subida significativa antes do episódio de setembro. São úteis para estudar variação temporal e eventos fora da amostra já examinada, mas dois meses não validam sazonalidade anual nem estabilidade entre anos. Janeiro–agosto completos teriam 5.832 horas por usina antes de lacunas.

## Lacunas e sinais de qualidade, sem correção

Janeiro: cinco horas ausentes simultaneamente nas três usinas,27/01 às 15–17 h e 28/01 às 16–17 h. Junho: duas horas ausentes simultaneamente,03/06 às 00–01 h, sob interpretação de fechamento 23:59 como 24:00. Castro Alves tem ainda Q/I/nível montante vazios em 12/06 às 14 h.

14 de Julho tem afluência 0 em 09/01 às 19 h, defluência 28 m³/s e montante 103,36 m. O zero foi mantido e não prova ausência de escoamento natural nem falha. Não há zero defluente com componentes positivos; nenhum residual absoluto Qdef−Qtur−Qvert−Qoutras excede 1 m³/s nas linhas com componentes finitos. Esse limiar é sinalização local, não aprovação oficial; a falta de flags não certifica os dados. Todas as variáveis, vazios e extremos permanecem na extração.

O ONS informa dados reportados pelos agentes, não consistidos, sujeitos a lacunas e revisões. Vazões são m³/s, níveis metros; não interpretar nível como altitude com datum comprovado. Os CSVs mensais retornam Last-Modified de fevereiro/2025: não documentam a versão disponível ao emitir uma previsão em 2023. Licença catalogada Creative Commons Atribuição, com crédito ao ONS e transformações explícitas.

## Tempo e regime operacional

O catálogo define hora-fim. Mantivemos din_instante original; a conversão 23:59→24:00 foi usada apenas para contar lacunas, com hipótese explícita. A norma ONS RO-AO.BR.02 Rev.08 usa horário de Brasília, mas vigora em 02/07/2024: o vínculo específico do exportador de 2023 continua pendente. Não interpretar os timestamps ingênuos como UTC confirmado. Não há arquivo de latência/publicação original.

Todo o lote2023 antecede as avarias de maio/2024. A [apresentação ONS de 09/05/2024](https://www.gov.br/ana/pt-br/assuntos/monitoramento-e-eventos-criticos/eventos-criticos/apresentacoes-das-reunioes/apresentacao-ons-sala-crise-sul-2024_05_09.pdf), já preservada, registra perda de comunicação com as três usinas em 01/05 e rompimento parcial do vertedouro de 14 de Julho em 02/05. Isso é contexto físico/operacional, não um coeficiente automático de correção.

A [nota CERAN de 04/05/2026](https://ceran.com.br/sem-categoria/ceran-atualiza-a-situacao-das-usinas-hidreletricas-apos-2-anos-das-cheias/), também reutilizada, informa recuperação da cota operacional de 14 de Julho em dezembro/2024 e conclusão das obras em março/2025; Monte Claro teve a casa de força inundada e recuperada; obras preventivas em Castro Alves começaram em novembro/2025. As fontes não estabelecem aqui curvas/regras operacionais diárias ou magnitude de mudança da relação entre entradas e saídas.

Assim, marcar 2023 como pré-avarias e manter comparação separada com transição 2024 e recuperação 2025–2026. Não misturar indistintamente para justificar ganho no regime atual. Afluência, defluência e níveis de reservatório não autorizam inferir armazenamento ou conservação de massa instantânea sem curvas/intervalos apropriados.

## Próximo lote concreto

Os seis recursos ainda não coletados — fevereiro, março, abril, maio, julho e agosto/2023 — estão em next-monthly-resources.json, com URLs oficiais e IDs; Parquets somam 7.466.278 bytes segundo catálogo. Reutilizar janeiro/junho desta pasta e setembro do acervo anterior, sem novos downloads desses meses. Auditar os seis meses antes de definir qualquer treino/validação temporal; períodos aqui inspecionados não devem depois ser apresentados como teste cego.

Para um experimento de vazão, gerar entradas somente de intervalos encerrados antes da origem, com atraso presumido explícito e sem Q/I futuro. Não fabricar lacunas. Para avaliar nível em Muçum, ainda será preciso acervo ANA compatível; este lote de usinas sozinho não fornece os alvos de nível.

Arquivos: source-manifest.json(URL/coleta/headers/hash), raw/(dois CSVs integrais), ceran-source-values.csv(filtro das três usinas e linha de origem), catalog.json(variáveis/QC/cobertura), missing-hours.csv, june-event-coverage.json, reservoir-inventory.csv, reused-documentation.json(hashes/fontes reutilizadas), collect.py/audit.py(receitas locais). Nenhuma alteração em modelos, fontes anteriores, recorte de teste ou automação.
