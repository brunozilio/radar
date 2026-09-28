# Auditoria independente do modelo hidrométrico de Muçum

1898 verificações aprovadas; 0 falhas. Nenhum ajuste de coeficientes, retreinamento, alteração dos artefatos experimentais ou escrita em produção.

O código e os números permitem prosseguir com execução prospectiva em **shadow**. Não há evidência para substituir a previsão pública: o episódio atual tem erros importantes na subida e no pico, e faltam validação prospectiva, disponibilidade histórica comprovada e eventos independentes.

## Escopo verificado

- Hashes de código, teste, protocolo, dataset, manifesto e arquivos brutos referenciados; checksum das previsões.
- Grade horária exata; observação-base e alvo da estação 86510000 em cada linha, sem criação de verdade interpolada.
- 225 correlações de primeiras diferenças reconstruídas somente antes do corte de treino; lags escolhidos conferidos.
- Cortes cronológicos, embargo de 33h, índices de todas as partições e disponibilidade natural de cada família reconstruídos independentemente.
- Seleção de alpha e família conferida pelos scores de validação registrados; score do candidato selecionado também reconstruído diretamente do CSV.
- Médias, escalas, extremos e interceptos finais reconstruídos em treino+validação; os coeficientes satisfazem as equações normais Ridge, sem resolver o sistema novamente.
- Todas as 72 avaliações agregadas e respectivos recortes recontados. Inferência dos coeficientes congelados reproduzida para os 12 conjuntos teste/stress do modelo selecionado. Baselines reproduzidos para as três partições.
- Faixas residuais empíricas p05/p95 conferidas contra as previsões de validação congeladas. Não representam intervalos com cobertura garantida.

Os outros alphas e o controle contemporâneo não possuem todos os coeficientes congelados neste artefato. Suas métricas foram auditadas a partir das previsões salvas; não houve refit para reconstruí-los. O protocolo e o código congelados permitem examinar a seleção; o manifesto não é, isoladamente, uma prova externa de que o processo nunca leu outros dados.

## Resultado do candidato selecionado

Cada horizonte abaixo é nominal a partir da observação. O replay pressupõe emissão no instante de referência; não reconstitui atraso histórico de recebimento nem comprova os prazos reais de produção.

| Horizonte | Teste n | Teste MAE | Teste ±0,50m | Episódio atual n | Episódio MAE | Episódio ±0,50m |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 771 | 0.032m | 100.00% | 46 | 0.089m | 95.65% |
| 2h | 770 | 0.071m | 99.87% | 45 | 0.246m | 88.89% |
| 3h | 769 | 0.104m | 98.70% | 44 | 0.367m | 79.55% |
| 4h | 769 | 0.138m | 97.53% | 43 | 0.505m | 67.44% |
| 5h | 769 | 0.169m | 94.80% | 42 | 0.620m | 64.29% |
| 6h | 768 | 0.213m | 89.84% | 41 | 0.753m | 60.98% |

A família com lags foi escolhida nos seis horizontes pela regra prévia de validação. O controle contemporâneo teve MAE menor nos seis horizontes do teste. Essa constatação não autoriza trocar a escolha depois de ver o teste. As duas alternativas permanecem candidatas; o melhor desempenho médio do controle merece investigação em outro experimento previamente definido.

## Episódio de 21–23 de setembro

O máximo **horário** observado no recorte foi 18,71m às 04h BRT de 22/09. Isso não pretende substituir o máximo de medições sub-horárias. As fases de evento usam os alvos antes, dentro e depois de uma janela de ±3h desse máximo; são diagnósticos retrospectivos, nunca entradas de previsão.

- 1h: 44/46 pares dentro de ±0,50m (95,65%); subida conhecida na origem: 16/18 (88,89%).
- 6h: 25/41 pares dentro de ±0,50m (60,98%); subida conhecida na origem: 6/18 (33,33%).
- 6h na janela do pico: 2/7 pares (28,57%), MAE de 1,170m, viés positivo de 1,170m.
- 6h na recessão após o pico: 20/25 pares (80%), MAE de 0,348m.
- O maior erro de 6h no episódio foi 2,874m. A melhora contra persistência não demonstra atendimento à meta.

A fase conhecida na origem usa exclusivamente a inclinação das duas horas anteriores: subida >0,05m/h; descida <-0,05m/h; estabilidade entre os limites. O intervalo do pico usa verdade posterior apenas para diagnóstico. A separação não certifica eventos hidrológicos independentes.

## Disponibilidade e denominadores

| Partição / h1 | Horas programadas | Alvos exatos conhecidos | Persistência natural | Contemporâneo natural | Com lags / interseção |
|---|---:|---:|---:|---:|---:|
| train | 4391 | 4373 | 4362 | 3328 | 2150 |
| validation | 6518 | 6484 | 6454 | 5274 | 3439 |
| test | 1934 | 1911 | 1907 | 1199 | 771 |
| stress_current | 57 | 56 | 56 | 53 | 46 |

Todos os quatro métodos foram comparados nos mesmos pares da interseção. Isso evita vantagem por trocar o conjunto entre os métodos, mas não mede sozinho a cobertura operacional. O dataset tem 12.969 horas; 6.522 não têm todas as entradas da família com lags. A tabela e `coverage.csv` preservam também a disponibilidade natural dos métodos.

No episódio atual há 57 origens horárias; 46 têm entradas completas do candidato. No horizonte de 1h há 56 alvos conhecidos e 46 pares; em 6h há 51 alvos conhecidos e 41 pares. Alvos além do fim do snapshot permanecem desconhecidos e separados, não falhas nem acertos. Não há reconstrução de cobertura de chuva histórica suficiente para certificar ganho especificamente durante uma falha real de pluviometria.

## Limitações que impedem promoção

1. Os períodos históricos já foram usados em desenvolvimento do Radar. Teste cronológico não equivale a novos eventos independentes; o episódio corrente é diagnóstico conhecido.
2. Na validação de 1h existem apenas 14 pares com alvo≥7m e dois com alvo≥9m; nenhum alvo−origem≥1m. A parcela ausente do score é omitida explicitamente, não interpretada como erro zero.
3. Hashes e recibos recentes preservam os arquivos atuais, mas não demonstram que cada valor histórico estava publicado na hora simulada. Fontes podem conter revisões.
4. ONS identifica intervalos horários, enquanto leituras recentes CERAN podem ser instantâneas. Sua equivalência operacional não está certificada, assim como a estabilidade do datum de todas as estações.
5. Os lags de 3–8h aqui encontrados são associações estatísticas condicionadas à amostra e ao modelo. Não são tempos físicos comprovados da água nem eliminam remanso, operações de reservatórios ou afluentes ausentes.
6. Não há conjunto independente suficiente para bootstrap por evento, certificação dos estratos de subida/pico/recessão, ou meta de 98%. Muitos pontos horários correlacionados não substituem dez eventos independentes.
7. As faixas de erro vêm da validação do modelo antes do refit treino+validação; precisam ter sua cobertura verificada prospectivamente no modelo final. Não tratá-las como limites de segurança.

## Arquivos

- `checks.json`: verificações individuais, hashes e resíduos das equações Ridge.
- `metrics.csv`: métricas recalculadas por família, partição e horizonte.
- `strata.csv`: níveis≥7/9m, subida futura, fase conhecida na origem e fases do episódio atual.
- `coverage.csv`: oportunidades, entradas disponíveis, verdades desconhecidas e interseção.
- `paired-comparisons.csv`: diferenças pareadas e contagens melhor/pior/igual.
- `frozen-inference-replay.csv`: reprodução sem ajuste do modelo selecionado.
- `audit.py`: auditor independente; não importa o módulo de treinamento nem chama solver/fit.
