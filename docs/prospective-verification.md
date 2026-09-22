# Registro e verificação prospectiva

Desde a retirada solicitada em 21/09/2026, somente Radar é calculado e apresentado
nos relatórios ativos. O registro recusa novas emissões/importações HGE/ARNO.
Recibos, resultados e relatórios antigos permanecem intactos para auditoria.
O pacote do site exclui o código e os parâmetros exclusivos do modelo retirado.

## Inventário de episódios de cheia

O relatório inclui `flood-events.json`, produzido por `scripts/hydro_flood_events.py`
com a política registrada `docs/flood-event-grouping-policy.json`. A política
agrupa leituras aprovadas acima ou iguais a7m e exige72h de leituras abaixo de7m
para separar episódios. Intervalos maiores que20min ou revisão para qualidade
inválida interrompem a comprovação da recessão. O agrupamento é por estação e
referência vertical; previsões repetidas não multiplicam eventos.

**É um inventário diagnóstico, não uma certificação de independência.** Os72h
são uma escolha conservadora a ser revisada para a bacia, não um limiar calibrado
nem uma aplicação da regraFEH/NRFA. A [NRFA](https://nrfa.ceh.ac.uk/data/about-data/peak-flow-data/data-types/peaks-over-threshold-pot)
documenta que vários picos podem pertencer ao mesmo evento e utiliza critérios
de recessão em vazão. Não se transfere uma razão de vazões diretamente para
cotas de uma régua com zero arbitrário.

Eventos com começo desconhecido, ainda abertos ou com lacunas permanecem
explícitos. A integridade de fuso/datum também fica separada. Revisões da fonte
podem alterar o inventário; cada relatório conserva o horário-limite, o hash
final da cadeia lida, recibos e cópia dos códigos de avaliação. Nenhuma previsão
ou revisão recebida depois desse horário participa de uma avaliação retrospectiva.
O critério de pelo menos10eventos independentes segue não demonstrado.

O arquivo `diagnostic-scorecard.json` mostra também MAE, viés, P90/P98 e erro
máximo por modelo/versão, banda de antecedência real e recorte>=7m. Importações
antigas ficam em grupos separados. Ausência de medição mantém a contagem do
status, sem virar acerto. O diagnóstico pode conter observação com metadados
pendentes; o campo `goal_eligible_n` preserva essa distinção. `unique_target_times`
e `observed_flood_clusters` expõem repetições e dependência. Não se produz um
intervalo binomial supondo que previsões horárias sejam independentes.

`scripts/hydro_prospective_ledger.py` guarda recibos locais encadeados por SHA-256
em `outputs/monitoramento-prospectivo/`. Publicações são atômicas e não sobrescrevem
registros existentes. O horário de registro vem do relógio da máquina e não pode
ser informado pelo pacote de previsão. O encadeamento detecta edição dos registros
lidos; não equivale a carimbo externo, certificação ou proteção contra remoção de
toda a cauda do registro por alguém com acesso ao disco.

## Uso

```sh
/tmp/radar-hge-venv/bin/python scripts/hydro_prospective_ledger.py capture-ana
/tmp/radar-hge-venv/bin/python scripts/hydro_prospective_ledger.py report
```

`capture-ana` consulta somente Muçum, hoje e ontem, na API pública ANA; arquiva
XML, URL, hash, horário real da coleta e todas as revisões de qualidade. Não
envia mensagens nem altera o produto. A cada relatório, a revisão mais recente
da observação substitui a anterior inclusive quando passa a suspeita/ausente.

`import-saved --radar PASTA` preserva cálculos antigos para diagnóstico.
Essas importações **nunca entram na meta prospectiva** e não recebem horário
retroativo. A previsão salva das 15h já foi importada de forma idempotente.

## Emissão nova

O pipeline horário deve capturar seus insumos como `input_receipt` ou
`observation_receipt` via `store_blob` e `append`, antes de produzir a previsão.
Depois, `issue --packet pacote.json` registra um pacote com:

- `station_id`, `datum_id`, `model_id`, `model_version`;
- `reference_at` e `produced_at`, ambos com fuso; `training_cutoff`;
- `input_receipts`, IDs de recibos já registrados, cujos blobs são verificados;
- `model_artifacts`, lista de `{path, sha256}` dos artefatos locais do modelo;
- `points`, lista de `{valid_at, nominal_lead_h, level_m}`.

O chamador não pode informar `issued_at` ou `recorded_at`. Modelo/artefatos precisam
ser congelados antes da emissão. O registro valida hashes, cronologia e alvos,
mas não substitui uma auditoria do treinamento ou da disponibilidade das fontes.
O ciclo `scripts/hydro_hourly_forecast.py` conecta coleta, cálculo e emissão.
Ele produz somente a versão experimental de árvores do Radar. Registra XMLs, respostas meteorológicas,
histórico usado, matrizes de entrada e hashes dos modelos treinados. Os scripts
legados não passam a ser prospectivos só por produzirem CSVs.

```sh
/tmp/radar-hge-venv/bin/python scripts/hydro_hourly_forecast.py
```

O comando consulta fontes públicas ANA/CERAN/SIGMA/Open-Meteo, cria uma pasta
nova em `outputs/mucum-hourly-*`, calcula somente Radar e registra a emissão
em `outputs/monitoramento-prospectivo`. Falta de fonte necessária, chuva inválida,
cálculo sem 12 horas futuras restantes interrompem
a emissão. Nenhum deploy, alteração no produto ou envio externo é executado.
O runtime temporário precisa existir; versões estão em `scripts/hydro-hourly-requirements.txt`.

O ajuste estatístico continua restrito a alvos anteriores a 21/09/2026 00h BRT.
Hiperparâmetros foram fixados pela seleção histórica anterior, sem nova busca a
cada ciclo. Os artefatos são salvos para reprodução. O uso de previsão meteorológica
atual na entrada difere do arquivo do dia anterior usado no treinamento; por isso
essas saídas recebem uma identidade experimental própria e **não representam
promoção automática** da referência anterior. Horas nominais 13 e 14 reutilizam
hiperparâmetros de 12h, mas treinam seus próprios alvos históricos; sua precisão
ainda precisa ser medida. As duas horas extras cobrem o tempo gasto na execução.

## Antecedência real e cobertura

A hora de referência do cálculo não é necessariamente a hora real de emissão.
O placar usa bandas de antecedência mínima: `h` significa **pelo menos h e menos
de h+1 horas reais** restantes até o alvo. Preserva também o prazo nominal para
auditoria. Assim, uma saída nominal de 2h publicada 30min depois da referência
é avaliada na banda de pelo menos 1h, com antecedência exata de 1,5h visível.
Não pode comprovar o objetivo de 2h. Isso exige que o ciclo entregue ao menos
um alvo com 12h reais restantes para avaliar a última banda da meta.

Previsões vencidas ao registrar, alvos sem leitura exata, dado não aprovado,
referência da régua diferente e metadados não verificados não entram na taxa.
Pendências ficam contabilizadas. A contagem de pares não mede disponibilidade
da automação; a cobertura de entrega é auditada separadamente, conforme abaixo.

## Estado da verificação

A documentação ANA consultada apoia UTC−03 para Hidro-Telemetria. O contrato do
endpoint e a referência física vigente da régua continuam explicitamente pendentes;
os recibos coletados mantêm esses indicadores falsos. Fontes estão em
`outputs/historico-cheias-mucum/documentation/fuso-e-referencia.md`.

A ferramenta nunca declara a meta atingida automaticamente: independência dos
eventos, quantidade de amostras, todos os horizontes e cobertura ainda precisam
passar pela auditoria definida em `forecast-accuracy-goal.md`.

## Próxima integração

O antigo comando `scripts/hydro_hourly_run.py` agora encaminha exclusivamente
ao runner Radar com registro prospectivo e proteção contra duplicação. Seu
cálculo e relatório com dois modelos foram removidos. As funções estatísticas
em `scripts/hydro_hourly_models.py` seguem disponíveis para reprodução histórica;
o runner ativo mantém corte e hiperparâmetros fixos. Não misturar as identidades
dessas versões.

O histórico incremental foi integrado em `scripts/hydro_history.py`. Cada coleta
produz um snapshot materializado e verificado em `history/` dentro da pasta do
ciclo, com ANA, CERAN e meteorologia em arquivos separados. O índice em
`outputs/monitoramento-prospectivo/history-index/current.json` aponta atomicamente
para o último snapshot íntegro. Recibos mais antigos não podem sobrepor os novos;
revisões inválidas substituem valores anteriores, sem preencher lacunas com zero.

As medições ANA/CERAN posteriores ao recebimento são excluídas e contabilizadas.
As previsões meteorológicas podem ter alvos futuros, mas permanecem estimativas
identificadas, separadas da chuva observada. Mudança na grade meteorológica,
hash incorreto ou conjunto incompleto de fontes interrompe a atualização. O
checkpoint válido anterior permanece disponível. Os arquivos cumulativos são
registrados como insumos antes do cálculo e da emissão seguinte.

Em `outputs/historico-incremental-validacao/replay-verification.json`, duas coletas
reais foram consolidadas e as181séries do snapshot17h foram reproduzidas sem
diferenças (tolerância absoluta1e-10). Testes adicionais cobrem a passagem de20dias,
revisões nulas, recusa de dados antigos e detecção de adulteração. Isso valida a
continuidade do armazenamento; não aumenta, por si só, a precisão do modelo nem
preenche períodos em que nenhuma coleta ocorreu. O acompanhamento continua
experimental e local.

## Cobertura de entrega, separada da precisão

`scripts/hydro_cadence.py` mede janelas horárias fixas. O protocolo foi registrado
antes do início de sua vigência:21/09/2026 às18h BRT. Apenas janelas inteiramente
encerradas entram no denominador; a primeira se encerra às19h. Antes disso a
taxa permanece não calculável, sem alegar100% ou0%. Não se inventa cobertura
retroativa. Tentativas e falhas anteriores continuam visíveis separadamente.

A política original exigia ambos os modelos. A retirada do HGE é registrada em
um recibo `cadence_model_transition`, com vigência na próxima hora cheia. A partir
dessa vigência, uma janela exige um ciclo concluído e a emissão Radar antes do
fim exclusivo da janela. Os critérios anteriores continuam aplicados às janelas
passadas; nenhuma falha ou ausência histórica é apagada. Cada pacote precisa cobrir todas
as bandas reais de1–12h. Não se combinam tentativas diferentes, referências
diferentes ou pacotes parciais para fabricar uma entrega completa. O pacote
registra o ID do início do ciclo, que deve anteceder sua produção. O relatório
é escrito depois do recibo de conclusão. Falha, ausência de início, atraso ou
entrega incompleta ficam discriminados em `cadence.json`.

O protocolo mede entrega por hora, não prova o instante de disparo do agendador
nem que um registro aberto ainda corresponda a processo em execução. Cobertura
de entrega nunca substitui a taxa de acerto do nível do rio.

## Correção explícita da grade meteorológica

O ciclo17:27 parou ao detectar uma mudança na grade. O coletor passou a usar
as coordenadas originais de `chuva-prevista-query.json`, corrigindo o reaproveitamento
indevido das coordenadas retornadas pelo GFS para consultar outros modelos.
As grades novas de ECMWF/ICON coincidem com seus respectivos históricos de treino.

`docs/weather-grid-transition-20260921.json` documenta a migração pontual, vinculada
aos hashes exatos dos arquivos anterior/novo e à grade histórica esperada. Nenhum
horário já coletado pode ser perdido na migração. A política só foi passada à
tentativa de recuperação; execuções futuras usam o checkpoint corrigido normalmente.
A primeira falha permanece no registro, e a tentativa nova em
`outputs/mucum-hourly-20260921T172707-retry/` emitiu os dois modelos às17:31 BRT.
