# Auditoria independente — idade explícita da âncora Radar

**28.574 verificações aprovadas, sem divergências.** As144aplicações dos72modelos anteriores e48aplicações dos24modelos novos reproduziram exatamente as previsões preservadas. As1.152métricas foram recalculadas com tolerância1e−12. Não houve fit, rede, promoção ou alteração das fontes.

## Reconstrução independente da idade

Os25.824rastros foram refeitos diretamente de`history/ana-86510000.npz` dos snapshotsA/B, com um cursor cronológico procurando o último registro anterior ou igual à consulta, sem importar o builder. A consulta é origem−15min emA e origem−30min emB; o registro expira após15min adicionais. **Não se pula um registro mais recente inválido para obter um valor antigo finito.** Bases eNaNs coincidem exatamente com o pai; a idade éNaN precisamente quando a base é ausente.

| Perfil | Idade finita da medição | Origens | Base ausente |
|---|---|---:|---:|
| A | 15min /30min | 12.822 /6 | 84 |
| B | 30min /45min | 12.824 /15 | 73 |

As84faltasA compreendem1consulta sem predecessor,27expiradas e56com último registro não finito. EmB são1,29e43, respectivamente. Todos os índices, consultas, timestamps selecionados, valores de origem, bases e idades conferem com`age-trace.csv`. A coluna extra não mudou as180anteriores.

A idade é fortemente associada ao perfil: correlação dePearson **0,9983715** entre idade e indicadorB nas25.667vistas com base finita.30min é o único valor compartilhado, muito raro emA. Essas vistas são pares construídos, não eventos independentes. ComoA/B também diferem em atrasos de outras fontes, a coluna pode identificar o perfil geral; o teste não isola efeito causal da idade deMuçum. É idade de medição retroconstruída, não latência histórica certificada de publicação ou idade no fim do runtime.

## Máscaras, pesos, controle e integridade

Protocolo registrado04:24:01.135046UTC e manifesto pré-fit04:25:38.880348UTC, anteriores à conclusão. Conferidos os90hashes de entrada, hash de idades, manifesto do pai e todos os artefatos finais. Os horários são registros preservados, sem atestado externo do instante efetivo de cada fit.

O sorteioPCG64(57) é o mesmo:6.408origensA/6.504B. As24máscaras, ordem cronológica, interseção comum e cortes estritos foram reconstruídos. A coluna de idade escolhida corresponde ao mesmo perfil do vetor e da base de cada origem. Respostas`alvo−base`, pesos, contagens e todos os metadados de treino permanecem os do candidato misto anterior. A configuração integral dos24novos modelos coincide com seu par anterior; a dimensão é181em vez de180. Nenhuma origem foi duplicada.

Os204.168registros preservam exatamente todos os campos anteriores, inclusive previsões dos três controles. São duas vistas de102.084origens×horizontes, sem selecionar perfil favorável. Nas cheias test,237alvos observados/236pares/uma falha por grupo; validation28alvos sem falha. As métricas gerais ecomplete24/missing24 também foram refeitas, mantendo falhas no denominador observado e alvos desconhecidos fora dos acertos. As864métricas dos controles são idênticas às do pai.

## Resultado e regressões

Comparando idade explícita contra o misto **sem idade**, no recorte cheia/full_schedule:

| Fase / perfil | Horizontes com mais / mesmos / menos acertos | Horizontes comMAE menor / igual / maior |
|---|---:|---:|
| ValidationA | 3 /9 /0 | 4 /4 /4 |
| ValidationB | 2 /9 /1 | 5 /4 /3 |
| TestA | 3 /6 /3 | 3 /3 /6 |
| TestB | 3 /5 /4 | 5 /3 /4 |

Em6h test, acertos pioram de170→165emA e166→159emB, sobre237alvos. OMAE sobe de0,602111→0,608193m e0,635535→0,640098m; máximos diminuem ligeiramente, sem eliminar as regressões. Em12h, permanecem75/237nos dois perfis:MAE1,328673m emA e1,384912m emB. Continuam abaixo dos controles correspondentes de91/237emA e77/237emB. OsCSV registram ambos os referenciais, sem escolher versões por horizonte.

**Conferência adicional solicitada para12h:** emvalidation e test, nenhum nó não terminal usa a coluna180. Todos os campos dos180predictors de cada modelo, incluindo nós e bitsets, são exatamente iguais ao misto sem idade; o intercepto também. Total360árvores conferidas. Isso explica a identidade estrutural nesses dois modelos, sem generalizar para modelos sem uso de idade que não foram comparados estruturalmente nesta subauditoria. Não foi repetida a inspeção dos demais horizontes feita pelo root.

## Limites e arquivos

Os períodos e perfis já foram examinados e são desenvolvimento. Não há evidência de melhoria uniforme, independência prospectiva ou alcance da meta98%. Joblibs não guardam toda a lista original de amostras/pesos: foram conferidos código, reconstruções, hashes e resumos, sem refazer a otimização das árvores.

`audit.py` e`verification.json` preservam28.574checks;`check_trees_h12.py` e`tree-h12-verification.json` cobrem a inspeção adicional. Há resumos de idade/falhas, amostras reconstruídas,144+48replays, métricas e contrastes. `input-hashes.json` identifica as fontes;`artifact-hashes.json` cobre os arquivos desta pasta, exceto o próprio manifesto. Nenhuma pesquisa ou auditoria anterior foi modificada.
