# Radar — exclusões pela exigência de 24 níveis/variações completos

**A inconsistência é real.** `hydro_latency_forecast.run` aplica `finite(H) & finite(target) & finite(X[:,:24]).all()` tanto ao treino quanto aos subconjuntos retrospectivos. Já sua previsão da última origem é acrescentada diretamente à inferência. O runner `hydro_hourly_forecast.calculate` também usa o filtro no treino e prevê a última origem sem exigir os 24 campos completos; quanto aos níveis, exige somente H atual de Muçum. Existem outras verificações operacionais, como chuva prevista ao vivo completa, que esta auditoria não remove nem testa.

O filtro abrange **24 campos: quatro estações × nível atual e variações de 0,5/1/2/4/8h**. São Muçum 86510000 e auxiliares 86472000, 86472600, Passo Carreiro 86500000. Portanto parte das exclusões vem de histórico de Muçum ausente, mesmo com seu nível-base atual finito.

## Efeito no teste preservado

Origem desde 01/07/2026 e alvo estritamente anterior a 21/09/2026, UTC−3 presumido. Elegível significa H-base e H-alvo finitos; cheia significa **alvo ≥7 m**, diferente do limiar ≥9 m empregado nos pesos de treino.

| Horizonte | Elegíveis todos | Antigos avaliados | Excluídos | Elegíveis cheia | Antigos cheia | Excluídos cheia |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 1.939 | 1.350 | 589 (30,38%) | 236 | 144 | 92 (38,98%) |
| 6h | 1.927 | 1.343 | 584 (30,31%) | 236 | 140 | 96 (40,68%) |
| 12h | 1.915 | 1.337 | 578 (30,18%) | 236 | 140 | 96 (40,68%) |

As chaves origem/alvo desses antigos subconjuntos coincidem exatamente com `retrospectivas-latencia.csv`, família `arvores_previsao_chuva`, nos três horizontes e nas fases test/today: seis verificações sem faltas ou extras. Esta é auditoria de cobertura, não cálculo de desempenho. O subconjunto antigo permanece válido como resultado **condicional à completude**; não representa desempenho em todas as origens com H disponível.

## Datas e causas

Os alvos de cheia excluídos estão concentrados em **2–4 de julho, 21–24 de julho e 14–15 de agosto**. Todos os excluídos de cheia apresentam pelo menos um campo de Passo Carreiro ausente. O maior nível-alvo excluído é **19,86 m** em cada horizonte. Em 1h, são 35 alvos excluídos na janela de 2–4/julho, 45 em 21–23/julho e 12 em 14–15/agosto; em 6h são 35/50/11 e em 12h 35/56/5. São agrupamentos descritivos de datas já inspecionadas, não novos eventos independentes de teste.

Em 1h geral, das 589 exclusões, 562 vêm apenas das auxiliares, 8 apenas das variações de Muçum e 19 de ambas. Há 540 casos com algum campo de Passo Carreiro ausente, 54 de 86472600, 27 de Muçum e 8 de 86472000; essas causas se sobrepõem. A extensão temporal máxima de uma variação é oito horas, por isso uma lacuna passada pode excluir uma origem cujo nível atual já retornou.

O treino inicial também perde 729/732/732 pares em 1/6/12h. A validação perde 588/591/587 pares gerais, mas **nenhum dos seus 28 alvos de cheia** em cada horizonte. Isso reforça que a validação antiga oferece pouca evidência sobre o comportamento em cheia com falta desses campos.

## NaN e interpretação do próximo experimento

O código-fonte local primário do scikit-learn **1.9.1** documenta suporte nativo a NaN no HistGradientBoostingRegressor. Se uma feature nunca esteve ausente no treino, a previsão com NaN segue o filho com mais amostras. O filtro antigo impede que os primeiros 24 campos ensinem rotas de missing durante o treino. Isso não prova que retirar o filtro melhora a precisão: requer comparação separada do baseline congelado ampliado e do candidato treinado com NaN, mantendo hiperparâmetros, alvos e cortes.

O denominador desta auditoria requer alvo observado para avaliar cobertura; a inferência de uma previsão não deve depender de alvo futuro disponível. Não há imputação, preenchimento de nível, novo treino, chamada de rede, HGE ou alteração operacional nesta entrega. Latências fixas do snapshot são hipóteses retrospectivas; não certificam publicação histórica ou datum. Nenhuma promoção.

## Evidência preservada

- `excluded-origin-targets.csv`: cada exclusão, origem, alvo, níveis e campos ausentes.
- `excluded-intervals.csv`: intervalos consecutivos de origens excluídas; não declaração automática de eventos hidrológicos.
- `coverage-summary.csv`, `daily-exclusions.csv`, `missing-features.csv`: contagens por divisão temporal, horizonte e subconjunto.
- `code/`, `code-evidence.json`, `sklearn-evidence.json`, `verification.json`: fontes revisadas, linhas, documentação local, hashes e reprodução do subconjunto original.

Reprodução: `PYTHONDONTWRITEBYTECODE=1 /tmp/radar-hge-venv/bin/python outputs/auditoria-cobertura-radar-20260921/audit.py`. Executa somente as funções puras de features/shift extraídas via AST e a auditoria local; não importa módulos operacionais.
