# Auditoria independente — mistura de perfis de atraso Radar

**2.157 verificações aprovadas; nenhuma divergência encontrada.** Foram reaplicados72modelos congelados em144combinações modelo×perfil, com previsões exatamente iguais às salvas. As864métricas foram recalculadas diretamente das204.168linhas, com tolerância numérica1e−12 para métricas. Nenhum modelo foi ajustado por esta auditoria.

## Preparação e treino conferidos

O protocolo tem registro04:10:35.814040UTC; o manifesto pré-fit é04:12:30.163548UTC; a conclusão é04:17:53.998674UTC, em22/09/2026. Os29hashes de entradas e os dois hashes de matrizes/máscaras preparadas foram conferidos no manifesto pré-fit e no final, assim como todos os artefatos do experimento. A ordem dos registros e do código é coerente com o sorteio anterior aos fits. Não existe nesta auditoria um relógio externo autenticado que certifique o instante efetivo de cada ajuste.

As duas matrizes foram reconstruídas diretamente dos snapshots selados, sem helpers operacionais:12.912origens anteriores a21/09/2026,180colunas, mesma grade horária, mesmos alvos e mesmas60colunas meteorológicas. Bases e ausências de cada perfil foram preservadas. O sorteio independente com`Generator(PCG64(57)).integers(..., dtype=int8)` reproduziu exatamente6.408origensA e6.504B. O vetor é único para todos os folds/horizontes e não usa alvos ou erros.

As24máscaras de treino foram refeitas pela interseção de base/24entradas finitas nos dois perfis e alvo comum finito. Foram preservados os cortes estritos e a exclusão da fronteira deoutubro entre os blocos que compõem o treino test. Os três modelos de cada fold/horizonte recebem as mesmas origens em ordem cronológica, sem duplicação. O candidato escolhe um vetor completo e a base do mesmo perfil; resposta e peso foram reconstruídos com essa base. Conferimos os72registros de treino, contagens por perfil, alvo alto, somas de pesos, última data de alvo e configurações congeladas. Todos os modelos têm180entradas e180iterações; parâmetros completos coincidem entre as três famílias de cada fold/horizonte.

`training-reconstruction.csv` registra hashes das matrizes, respostas e pesos reconstruídos; `reconstructed-samples.npz` guarda índices, respostas e pesos. Isso confere o contrato e os artefatos, sem repetir a otimização das árvores. Os joblibs não armazenam a lista completa original de amostras/pesos usados pelo fit; não se reivindica uma prova independente da trajetória de otimização.

## Cobertura e denominadores

Há102.084origens×horizontes físicas, cada uma avaliada duas vezes nos perfisA/B, totalizando204.168linhas e48grupos fase×perfil×horizonte. Chaves, ordem, horários dos alvos, bases, verdade e população complete24/missing24 conferem. A inferência usa apenas base finita da vista avaliada; ausência nas entradas auxiliares não exclui automaticamente uma previsão de avaliação.

As864métricas incluem três famílias, duas fases, dois perfis,12horizontes, três populações e recortes geral/cheia. Alvo desconhecido permanece separado; falha com alvo conhecido entra no denominador observado, não nos pares nem como acerto. Nas cheias test são237alvos observados,236pares e uma falha por grupo; na validation28alvos, sem falha. Não se somam as duas vistas como eventos independentes.

## Resultado misto, sem domínio entre perfis

Comparação sempre contra o controle correspondente ao perfil, no recorte cheia/full_schedule:

| Fase / perfil | Horizontes com mais / mesmos / menos acertos | Horizontes com menorMAE |
|---|---:|---:|
| ValidationA | 6 / 4 / 2 | 9/12 |
| ValidationB | 4 / 2 / 6 | 2/12 |
| TestA | 5 / 2 / 5 | 5/12 |
| TestB | 4 / 2 / 6 | 4/12 |

Em6h test, os acertos melhoram nos dois perfis:162→170 emA e154→166 emB, sobre237alvos. Em12h test, pioram:91→75 emA e77→75 emB. OMAE12h passa de1,246947→1,328673m emA e1,352281→1,384912m emB; os máximos sobem de7,575214→7,792800m e6,959959→7,606918m, respectivamente. Em12h validationB,11→8acertos/28. Os contrastes completos e controles cruzados estão nosCSV, sem escolha de família/perfil por horizonte.

Esses controles foram reajustados com a interseção comum; **não são reprodução dos modelos operacionais originais**. Ambos os perfis e períodos já foram inspecionados e são desenvolvimento. Dois perfis de atraso atuais não cobrem toda a distribuição de atrasos nem certificam disponibilidade histórica. Não houve promoção, emissão ao vivo, rede ou demonstração da meta98%.

## Arquivos e integridade

`audit.py` é reproduzível no runtime preservado NumPy2.5.3/sklearn1.9.1, com duas threads; não importa o runner ou código de treino. `verification.json` contém os2.157checks. `inference-replay.csv`, `independent-metrics.csv` e `matching-profile-contrasts.csv` preservam as conferências. `input-hashes.json` identifica as fontes lidas. `artifact-hashes.json` cobre esta auditoria, exceto o próprio manifesto. Nenhuma entrada, pesquisa anterior ou resultado do experimento foi alterado.
