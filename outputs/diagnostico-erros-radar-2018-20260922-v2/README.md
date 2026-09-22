# Por que menor erro médio não aumentou os acertos de12h

O diagnóstico usa todas as102.084 linhas já avaliadas, sem ajustar ou executar novamente modelos. São695 grupos descritivos e3.456 verificações de reconciliação. Os agrupamentos foram definidos para investigar o resultado conhecido; não são novos testes independentes.

No test com nível observado≥7m e horizonte nominal12h, há237 alvos,236 pares e uma falha. As transições entre controle e candidato+2018 são:

| Resultado | Quantidade |
|---|---:|
| Ambos acertam dentro de0,50m |63|
| Controle acerta; candidato erra |16|
| Controle erra; candidato acerta |12|
| Ambos erram |145|
| Previsão ausente nos dois |1|

Isso recompõe79→75 acertos. Nos145 pares em que ambos erram, o MAE cai2,11118→2,02776m; a soma dos erros absolutos cai12,09536m. A redução total dessa soma emtodos os236 pares é12,50106m. Portanto, quase toda a melhora do erro médio vem de casos que continuam fora da tolerância. A média menor não equivale a maior taxa de acertos.

Na faixa[7,9)m, os acertos caem50→45/120 e o MAE sobe0,75603→0,78922m. Em≥9m, passam29→30/117 (116pares e uma falha), e o MAE cai2,10656→1,96445m. Essas faixas usam o alvo observado e só servem ao diagnóstico posterior; não podem escolher o modelo antes de conhecer o futuro.

Usando somente a tendência conhecida na origem (dH1, limiares±0,10m/h sem arredondamento), os acertos de12h emcheia mudam26→30 nos68 alvos de tendência descendente,26→21 nos69 estáveis e27→24 nos98 ascendentes; dois alvos têm tendência desconhecida, um deles sem previsão. Isso não demonstra causalidade física nem autoriza selecionar modelos por tendência depois de olhar o teste.

O CSVpor data de alvo mostra concentração do ganho médio em22–23/julho, com pioras emoutras datas. Dias de calendário não são eventos hidrológicos independentes. A validation também piora:9→8/28 acertos e MAE0,85009→1,00172m. Nenhum recorte muda a conclusão de não promover o candidato.

`annotated-pairs.csv` preserva cada linha, nível/tendência, qualidade de disponibilidade e transição; `strata.csv` contém todos os agrupamentos; `target-days-h12.csv` mantém os17 dias dos dois períodos. Verdade desconhecida é contada no conjunto geral e nunca rotulada como cheia. No recorte observado≥7m, scheduled_rows refere-se apenas aos alvos conhecidos nesse recorte, diferentemente da agenda geral; os totais originais são reconciliados porobserved/pairs/failures/hits.

A primeira execução do diagnóstico foi interrompida após confirmar que acessava repetidamente o NPZ de forma preguiçosa, descomprimindo a matriz emcada linha. Sua pasta foi preservada. A versão final carrega os arrays uma única vez; fórmulas e fontes permaneceram iguais. Não houve alteração de modelos, previsões ou tolerância. Meta98% permanece não comprovada.
