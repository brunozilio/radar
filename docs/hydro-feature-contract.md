# Contrato causal de entradas do Radar

`radar-180-contemporaneous/v2` identifica 120 campos observados e 60 campos NWP,
na ordem de `hydro_feature_contract.feature_names()`. Um snapshot registra o vetor
realmente usado na emissão, seus recibos, referência, disponibilidade, estação,
datum, relatório de entradas completas e identidade do modelo/runtime.

A referência é a hora mais recente com entradas completas, posterior à última
publicada e com idade real de no máximo três horas. A emissão preserva essa hora,
registra `reference_age_seconds` e mantém somente os alvos originais H+1 a H+6
que ainda estão no futuro. O horizonte nominal não é estendido para compensar
o atraso. Os recibos têm até uma hora de idade na emissão. Snapshots v1 continuam
legíveis com suas regras originais, mas o dataset v2 rejeita contratos anteriores
explicitamente; não há conversão automática nem mudança das fórmulas das features.

`build_snapshot` recebe somente argumentos nomeados: `reference_at`, `issued_at`,
`station_id`, `datum_id`, `feature_values`, `sources`, `input_readiness` e
`model_metadata`. Ele retorna JSON serializável ou lança `ContractError`.
`validate_snapshot` retorna os motivos de rejeição sem executar modelos.

Cada item de `sources` contém `kind`, `id`, `available_at` e `sha256` do corpo
original. Sete fontes `observed` são obrigatórias: níveis 86510000, 86472000,
86472600, 86500000 e usinas julho, monte, castro. Seu `observed_through` deve
coincidir exatamente com a hora de referência. As três fontes `nwp` têm IDs
gfs_seamless, ecmwf_ifs025 e icon_global, `product: "current_forecast"` e
`field: "precipitation"`. `forecast_reference_at` pode ser nulo quando o provedor
não informa a emissão meteorológica. O horário de recebimento nunca é apresentado
como emissão do provedor. Todos os recibos devem estar disponíveis até a emissão.
Os demais arquivos de chuva e pesos devem permanecer ligados ao manifesto bruto
preservado em `model_metadata` e no arquivo de auditoria da emissão.

Níveis e vazões da hora de referência são exatos. Os derivados históricos mantêm a receita
existente: último nível anterior ao instante com idade até 900 s; vazões até
5.400 s. A chuva usa os intervalos efetivamente medidos, rateio proporcional quando
a janela corta um intervalo, pesos espaciais fixos e cobertura mínima de 50% nas
cinco regiões. Isso não equivale a garantir que todos os postos ou lags sejam
medidas exatas. Não há imputação do vetor final, e chuva ausente não vira tempo
seco. `current_nwp_features` integra os horários futuros exatos do produto atual;
não aceita `precipitation_previous_day1` como substituto.

O contrato do vetor não valida o treinamento de um modelo antigo. O metadado
`model` pode registrar esse legado, permitindo guardar entradas atuais para um
experimento futuro. `require_training_contract` deve receber a identidade
declarada pelo dataset de treino; ausência ou identidade legada bloqueia o ajuste.
Não atribuir o identificador contemporâneo a matrizes históricas anteriores.

## Dataset offline

`hydro_snapshot_dataset.py` não consulta a rede, ajusta modelos nem promove versões.
Consome snapshots JSON, observações JSON e um plano explícito:

```sh
python3 scripts/hydro_snapshot_dataset.py \
  --snapshots /caminho/snapshots.json \
  --observations /caminho/observations.json \
  --plan /caminho/plan.json \
  --output /caminho/novo-dataset
```

Cada observação exige `station_id`, `datum_id`, `valid_at`, `available_at`,
`level_m`, `quality: "approved"` e `receipt_sha256` válido; `source` descreve a origem.
O pareamento é exato por estação, datum e instante. Uma revisão recebida depois
do corte não pode entrar no treino; uma revisão inválida já recebida não permite
recuperar silenciosamente o valor aprovado antigo. Não interpolar lacunas.

O plano exige `train_end`, `validation_end`, `test_end`, `as_of`,
`nominal_horizons_hours`, `minimum_rows_per_horizon`, `minimum_events_per_split`
e `events`. Os dois campos `minimum_*` são objetos com inteiros positivos para
`train`, `validation`, `test`. Cada evento tem `id`, `split`, `start_at`, `end_at`;
eventos inteiros ficam em um único período, sem sobreposição. `embargo_hours`
opcional amplia a separação. Alvos que alcançam o final do evento/período são
removidos; entradas posteriores e rótulos indisponíveis também. Uma única emissão
por estação/datum/hora é selecionada pela última emissão válida, nunca pelo erro.

A saída contém as disponibilidades e motivos de rejeição. O comando retorna 2
quando faltam amostras/eventos em qualquer horizonte/período, guardando o relatório;
retorna 0 quando as exigências declaradas permitem iniciar um experimento offline.
Isso não comprova precisão: `validation_status` continua `not_evaluated`,
`promotion_allowed` e `accuracy_claim_allowed` permanecem falsos. O diretório de
saída deve ser novo; arquivos congelados não são sobrescritos. As definições de
eventos e os limites precisam ser fixados antes de comparar os modelos.
