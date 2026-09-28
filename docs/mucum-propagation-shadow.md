# Muçum: registro da avaliação inicial do modelo hidrométrico

**Atualização de 23/09/2026:** o usuário solicitou publicar esta previsão experimental e retirar a trava que a mantinha fora do gráfico. O caminho ativo agora segue o [contrato de publicação hidrométrica](mucum-hydrometry-public.md), sem exigir chuva. O restante deste documento registra a fase inicial de avaliação paralela; seus resultados científicos não foram alterados.

O candidato `mucum-hydrometry-shadow-v1` calcula o nível de Muçum usando níveis e vazões observados, inclusive suas mudanças nas horas anteriores. Ele pode ser avaliado quando faltam medições de chuva, desde que **todas as suas próprias entradas estejam completas**. Suas saídas ficam arquivadas para comparação futura; `publishable: false` impede tratá-las como substituição aprovada da previsão pública.

Este documento descreve a implementação e a validação local. A confirmação da versão efetivamente implantada e da execução remota deve constar da evidência de implantação correspondente.

## Entradas e execução

- Estação-alvo: ANA/SGB `86510000`, Muçum. Níveis adicionais: `86472000`, `86472600` e `86500000`.
- Vazão afluente `I` e defluente `Q` das usinas Castro Alves, Monte Claro e 14 de Julho, mantidas como variáveis separadas. Somar suas vazões contaria repetidamente água que passa pela mesma cascata.
- Regressões Ridge independentes para os horizontes nominais de 1 a 6h. O artefato congelado está em `model-artifacts/mucum-propagation-v1/model.json`; inferência não ajusta coeficientes.
- O candidato selecionado tem 58 variáveis e precisa de até 11h de histórico exato. Não interpola, não carrega a última leitura para outra hora e não substitui ausências por zero. A chuva e a previsão meteorológica não entram nesse contrato.

`hydro_site_projection.py` chama `hydro_propagation_live.run_shadow` após a coleta e antes da trava de chuva do modelo público. Assim, o candidato é registrado mesmo quando essa trava impede uma nova previsão pública. O modelo público mantém seus requisitos existentes.

O adaptador busca a referência completa mais recente, limitada a **3h de idade real**. Cada ponto mantém seu alvo original `referência + horizonte`; pontos já vencidos são removidos. Uma referência atrasada não produz seis novas horas artificiais. O resultado registra `referenceAt`, `generatedAt`, `nominalLeadHours`, `realLeadHours` e os motivos de indisponibilidade.

## Defasagens: associação estatística, sem tempo de viagem garantido

As defasagens foram selecionadas somente no treino, pela correlação positiva entre primeiras diferenças, em uma grade de 0 a 24h. Os valores selecionados ficaram entre 3 e 8h para os níveis e vazões de montante. Eles podem misturar propagação, operação das usinas, afluentes não medidos e chuva comum a várias regiões. Não medem diretamente o tempo de deslocamento da água até Muçum nem implementam o roteamento hidráulico do MGB-IPH.

O [diagnóstico separado de chuva](../outputs/propagacao-chuva-defasagens-20260923/report.json) compara chuva regional acumulada em 3h com mudança do nível de Muçum em 3h, testando atrasos de 0 a 48h. Exige cobertura regional de pelo menos 50%, 96 pares e 24 pares com chuva. A escolha usa somente treino, com embargo de 54h nas partições seguintes.

| Região | Atraso escolhido no treino | Correlação no treino | Na validação, com o mesmo atraso |
|---|---:|---:|---:|
| Baixo Antas | 12h | 0,355 | 0,168 |
| Carreiro | 13h | 0,362 | 0,150 |
| Prata-Turvo | 12h | 0,365 | 0,168 |
| Alto Antas | 12h | 0,386 | 0,048 |
| Tainhas | 12h | 0,329 | 0,128 |

Há platôs de atrasos próximos e forte variação entre períodos. No episódio atual faltam pares suficientes para estimar essas correlações. Portanto, **não há base para afirmar que a chuva do Alto Antas sempre chega em 12h**. Esse diagnóstico não altera os pesos nem fornece entradas ao candidato sem chuva.

## Calibração e resultado

O [protocolo congelado](mucum-propagation-validation-protocol.json) foi registrado antes do ajuste. Foram comparados Ridge contemporâneo, Ridge com defasagens, persistência do nível local e tendência linear local de 2h, nos mesmos pares completos.

- Treino: alvos anteriores a **01/10/2025, 00h BRT**.
- Validação: origens a partir desse corte mais 33h, com alvos anteriores a **01/07/2026, 00h BRT**.
- Teste: origens a partir do corte de julho mais 33h, com alvos anteriores a **21/09/2026, 00h BRT**.
- Episódio de 21–23/09: diagnóstico separado, já conhecido durante o desenvolvimento.

O embargo de 33h cobre o máximo permitido de 27h de histórico das variáveis e 6h de alvo. A validação escolhe `alpha` entre 1, 10, 100 e 1000; depois os coeficientes são ajustados em treino+validação, conservando as defasagens escolhidas no treino. O teste não escolhe parâmetros.

A [auditoria independente](../outputs/propagacao-auditoria-20260923/README.md) aprovou 1.898 verificações sem retreinar: hashes, datas, partições, seleção, equações dos coeficientes, previsões congeladas, métricas e disponibilidade. O [experimento original](../outputs/propagacao-modelo-20260923/execution-manifest.json) permanece preservado.

O candidato com defasagens foi escolhido pela validação, mas o contemporâneo obteve MAE menor nos seis horizontes do teste. No episódio atual, o candidato selecionado teve **95,65%** de pares dentro de ±0,50m em 1h e **60,98%** em 6h. Em 6h, o acerto próximo ao pico foi **28,57%**. Esses resultados impedem promover o candidato como previsão pública aprovada.

O replay usa horários de observação e pressupõe emissão naquela hora. Arquivos históricos podem conter revisões e não comprovam quando cada informação estava disponível. Há ainda diferenças a verificar entre intervalos horários ONS e leituras CERAN, além da referência vertical das estações. A validação de 1h contém somente 14 pares com alvo ≥7m. As médias não demonstram desempenho em eventos extremos independentes.

## Recibos, relógio e avaliação prospectiva

Cada execução exige os sete arquivos brutos correspondentes às quatro estações e três usinas, acompanhados de hash e horário de recebimento. O adaptador verifica checksum, leitura aprovada da ANA e recibos recebidos até a emissão, com idade máxima de 1h. Revalida essa idade depois da inferência. Recibos futuros, fontes incompletas ou referências antigas produzem `status: unavailable` com motivo registrado.

O arquivo `propagation-shadow.json`, os dados brutos e os recibos integram o arquivo imutável da tentativa, associado a `projection/receipts/<attempt-id>.json`. O arquivamento deve concluir antes de considerar a previsão como evidência verificável. Tentativas indisponíveis também devem permanecer no histórico. Não existe descarte por uma janela de 48h.

O avaliador offline usa como emissão efetiva o maior instante entre **geração e arquivamento imutável**. Descarta pontos cujo alvo já venceu antes do arquivamento, deduplica a primeira emissão admissível antes de abrir as observações e compara somente com nível exato aprovado de Muçum. Não preencher observação ausente nem contá-la como acerto.

Isso depende de relógios corretos e fusos explícitos no coletor, runtime e armazenamento. O relógio de observação, o recebimento da fonte, a geração e o arquivamento são instantes distintos. Não retroceder `generatedAt` nem avançar artificialmente `--as-of` para fazer um caso passar. `--as-of` futuro é rejeitado. O índice do avaliador recebe a identidade e o horário do objeto R2 de um extrator previamente verificado; um hash fornecido manualmente não prova existência remota ou horário de publicação.

A avaliação separa horizontes nominais e antecedência real. Uma saída com 40 minutos restantes não comprova 1h de antecedência. Tentativas sem previsão, alvos futuros e observações ausentes ficam separados. O relatório atual é descritivo; a certificação ainda exige agrupar cheias independentes e demonstrar cobertura durante indisponibilidade real de chuva.

A [meta de precisão](forecast-accuracy-goal.md) continua sendo pelo menos **98% de erros absolutos ≤0,50m**, por antecedência real e também no recorte ≥7m, com no mínimo 1.000 pares prospectivos por horizonte e dez eventos independentes de cheia. Esses mínimos não garantem desempenho futuro. Não é necessário atingir 98% para coletar shadow; atingir a meta tampouco pode ser declarado a partir deste replay.

## Reproduzir e avaliar

Executar a partir da raiz do projeto, com o ambiente Python e as dependências de `scripts/hydro-hourly-requirements.txt`. Cada novo experimento deve usar outro diretório. Os comandos abaixo são locais; não publicam modelo ou previsão. O treino requer registrar previamente protocolo, argumentos e hashes, como em `execution-manifest.json` do experimento original.

```sh
# Reconstruir dados a partir dos arquivos brutos preservados.
python scripts/hydro_propagation_data.py \
  --baseline outputs/mucum-propagacao-2026-09-21 \
  --collection outputs/mucum-hourly-20260923T084211-0300 \
  --out outputs/propagacao-dados-repro

# Novo ajuste local com o dataset congelado; não usar o diretório original.
python scripts/hydro_propagation_model.py train \
  --dataset outputs/propagacao-dados-20260923/exact-hour-level-flow.npz \
  --dataset-metadata outputs/propagacao-dados-20260923/manifest.json \
  --train-end 2025-10-01T00:00:00-03:00 \
  --validation-end 2026-07-01T00:00:00-03:00 \
  --test-end 2026-09-21T00:00:00-03:00 \
  --output outputs/propagacao-modelo-repro

# Conferir o experimento já congelado sem novo ajuste.
mkdir outputs/propagacao-auditoria-repro
cp outputs/propagacao-auditoria-20260923/audit.py outputs/propagacao-auditoria-repro/audit.py
python outputs/propagacao-auditoria-repro/audit.py

# Reproduzir o diagnóstico de chuva; ele não treina o candidato.
python scripts/hydro_rain_response_lags.py \
  --levels outputs/propagacao-dados-20260923/exact-hour-level-flow.npz \
  --rain outputs/mucum-auditoria-2026-09-21/telemetria-corrigida.npz \
  --output outputs/propagacao-chuva-repro

# Avaliar recibos extraídos e verificados, usando o horário atual como corte.
python scripts/hydro_evaluate_propagation_shadow.py \
  --issues CAMINHO_DO_INDICE_VERIFICADO.json \
  --observations DIRETORIO_DA_COLETA_ANA \
  --output outputs/propagacao-avaliacao-nova
```

O treino grava `model.json`, `evaluation.json`, `predictions.csv` e seu checksum; recusa substituir uma execução existente. O avaliador prospectivo grava `evaluation.json`, `pairs.csv` e hashes. O índice é uma lista de objetos com `issue` (caminho do JSON extraído), `evidenceReceiptKey`, `archiveSha256`, `archivedAt` e, preferencialmente, `issueSha256`. A coleta de observações deve conter `collection-manifest.json` e `raw/ana-86510000-fresh.xml`.

Os testes específicos estão em `test_hydro_propagation_data.py`, `test_hydro_propagation_model.py`, `test_hydro_propagation_live.py`, `test_hydro_rain_response_lags.py` e `test_hydro_evaluate_propagation_shadow.py`, no diretório `scripts`. Mudanças no modelo ou nos contratos exigem novo protocolo/versão e avaliação; não editar retroativamente o experimento congelado.
