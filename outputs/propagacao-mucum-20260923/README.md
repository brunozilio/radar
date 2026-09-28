# Modelo complementar de Muçum — implementação e produção, 23/09/2026

Implementado, treinado, auditado e implantado **somente em avaliação paralela (shadow)**. O candidato usa níveis e vazões atuais e anteriores para acompanhar a resposta da bacia quando faltam medições de chuva. Não é uma implementação do MGB-IPH nem uma medição física do tempo de viagem da água.

**Execução real confirmada às 10h02 BRT:** o servidor calculou quatro alvos futuros, de 11h a 14h, a partir da referência completa de 08h. O arquivo foi preservado no R2 às 10h02min29s, antes desses alvos. A previsão pública permaneceu com a trava de dados completos; não houve promoção do candidato.

## O que mudou

- Dataset de 12.969 horas, de abril/2025 a setembro/2026, reconstruído a partir de ANA, ONS e CERAN, com identidades de estação/usina preservadas e lacunas explícitas.
- Novo modelo congelado `mucum-hydrometry-shadow-v1`: quatro níveis, seis variáveis de vazão, tendências anteriores e defasagens selecionadas somente no treino. Não soma vazões de usinas em cascata, não preenche ausências e não se retreina durante a coleta.
- Adaptador de produção independente da trava de chuva. Exige suas próprias medições completas, sete recibos recentes e hashes válidos. Conserva a referência original e exclui alvos vencidos.
- Arquivamento permanente de `propagation-shadow.json`, dados brutos, recibos, código e pesos, inclusive quando a previsão principal está bloqueada.
- Avaliador prospectivo offline que compara cada alvo com o nível exato aprovado de Muçum, considera o horário efetivo de arquivamento, evita duplicar emissões e separa dados ausentes de erros/acertos.

O fluxo usa a verificação existente da aplicação a cada 15 minutos. Não foi criada uma tarefa agendada no Codex. Só há inferência quando as entradas exigidas pelo respectivo modelo estão completas.

## Resultado e decisão

No episódio conhecido de 21–23/09, a avaliação retrospectiva do candidato selecionado produziu:

| Horizonte nominal | Pares | Erro absoluto médio | Dentro de ±0,50 m |
|---|---:|---:|---:|
| 1h | 46 | 0,089 m | 95,65% |
| 2h | 45 | 0,246 m | 88,89% |
| 3h | 44 | 0,367 m | 79,55% |
| 4h | 43 | 0,505 m | 67,44% |
| 5h | 42 | 0,620 m | 64,29% |
| 6h | 41 | 0,753 m | 60,98% |

O candidato melhorou sobre persistir o nível atual e prolongar a tendência local. Entretanto, o controle Ridge sem as defasagens selecionadas teve MAE menor nos seis horizontes do teste e em cinco dos seis horizontes do episódio atual. Isso não autoriza escolher outro modelo depois de consultar o teste: a seleção anterior foi preservada e a promoção pública permanece desabilitada.

Os erros aumentaram na subida e no pico: em 6h, apenas 6/18 pares de origens em subida e 2/7 próximos ao pico ficaram dentro de ±0,50 m. O maior erro de 6h foi 2,874 m. A **meta de 98% não foi atingida**.

Os números são retrospectivos, com horizontes contados da observação e emissão simulada naquele instante. Não comprovam antecedência real operacional. Há poucas cheias na validação, dados históricos possivelmente revisados e diferenças entre disponibilidade natural das famílias: no teste de 1h, 1.199 pares completos para o controle contemporâneo contra 771 com defasagens. A comparação pareada usa os mesmos 771 casos, e os demais denominadores permanecem registrados.

## Sobre a chuva que ainda está chegando

As associações entre níveis/vazões de montante e Muçum selecionaram defasagens de 3–8h, dependendo da variável. Elas não são tempos físicos certificados de deslocamento da água.

O diagnóstico separado da chuva selecionou associações próximas de 12–13h no treino, mas a estabilidade foi baixa. Para Alto Antas, a correlação caiu de 0,386 no treino para 0,048 na validação. Portanto, não fixamos “Alto Antas chega em 12h” no sistema. Esse diagnóstico não fornece chuva fictícia ao modelo complementar nem muda os pesos do modelo público.

## Prova da execução em produção

- Alvo: `radar.brunozilio.com`, Worker `sofik-monitoramento-taquari`.
- Worker: `40815fff-9890-4c2a-810c-f9cfeffedce5`, 100% da implantação.
- Container: versão **66**, observado em estado `running`.
- Imagem: `sha256:ef9d3ee132ab2058958a09272c028549e127955b34a37ca07d24a311365c8542`.
- Modelo: `8adc838b20fba1ec3edd63db53e4575b0b8df59c22a777ada434ed773fb58c97`.
- Recibo: `projection/receipts/34c5583a-570f-4579-8177-298f68d90136.json`.
- Emissão: 23/09/2026, **10:02:08 BRT**; arquivamento: **10:02:29 BRT**; referência: **08:00 BRT**.

Foram baixados os dois arquivos imutáveis da tentativa e verificados os hashes, o manifesto de runtime, cada membro do pacote, o modelo e os sete recibos/dados usados. O arquivo da tentativa contém o shadow calculado e não contém uma nova `forecast.json` pública. A API pública respondeu 200 com `waiting_for_data`.

A referência de 08h possuía níveis/vazões completos, mas cobertura de chuva de Alto Antas de **44,5%**, inferior aos 50% exigidos. Nas 09h também faltava o nível de Santa Tereza; os dados das 10h ainda não estavam disponíveis. Isso explica por que o candidato calculou enquanto a previsão pública permaneceu bloqueada.

A primeira avaliação prospectiva teve **quatro alvos futuros e zero pares já verificáveis**. Nenhum percentual de acerto foi calculado. O avaliador usa o máximo entre geração e arquivamento: o primeiro alvo tinha cerca de 57 minutos de antecedência efetiva, embora fosse H+3 em relação à referência de 08h.

Evidências: [estado de produção](production-confirmed.json), [prova dos arquivos](production-shadow-proof.json), [seleção de referência](production-reference-selection.json), [primeira avaliação](prospective-first-evaluation/evaluation.json), [índice de recibos](prospective-index.json).

## Validação concluída

- **280 testes Python** e **69 testes Node** aprovados.
- `npm run build` concluído; pacote de runtime com 201 arquivos e hashes verificados.
- Dry-run e implantação Cloudflare concluídos; versão em execução conferida separadamente.
- Teste local do pacote comprovou shadow calculado/arquivado e previsão pública bloqueada sem criar resultado público.
- Auditoria independente: **1.898 verificações aprovadas**, nenhuma falha, sem novo ajuste de coeficientes.

Documentação e reprodução: [contrato operacional](../../docs/mucum-propagation-shadow.md), [protocolo congelado](../../docs/mucum-propagation-validation-protocol.json), [auditoria independente](../propagacao-auditoria-20260923/README.md), [experimento preservado](../propagacao-modelo-20260923/execution-manifest.json), [diagnóstico de chuva](../propagacao-chuva-defasagens-20260923/report.json).

Para considerar promoção, falta demonstrar desempenho prospectivo em dados realmente disponíveis antes dos alvos, especialmente em subidas/picos e durante falta real de chuva. O controle contemporâneo merece um novo experimento previamente definido; os resultados atuais não serão reutilizados como teste independente. A meta de 98% exige ainda os critérios de amostra, antecedência real e eventos independentes já registrados no protocolo.
