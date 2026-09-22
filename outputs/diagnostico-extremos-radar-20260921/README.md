# Onde o Radar errou nas subidas extremas

Diagnóstico posterior dos quatro candidatos históricos, sem ajuste, mudança de dados, exclusão de erros ou emissão. Não é uma nova avaliação independente nem prova de causalidade.

## Concentração dos maiores erros

Os 12 maiores erros de 12h da combinação têm origem entre **21/07/2026 às 12h e 23h**, com alvos na madrugada/manhã de 22/07. Todos têm ausentes os seis campos de nível/variação do Carreiro. O maior erro ocorre na origem 19h: base de Muçum **3,42 m**, alvo às 07h **16,50 m**, previsão **8,8133 m**, erro **−7,6867 m**. Os outros três modelos também subestimam esse alvo: referência 9,5709 m; treino com faltas 8,5785 m; níveis adicionais 10,0141 m.

A resposta real alvo−base desse caso é **13,08 m**, contra máximo de **8,09 m** no treino de 12h. O máximo de treino ocorre em 29/06/2025 às 02h, base 5,23 m e alvo 13,32 m. Incluir as linhas com falhas de telemetria amplia o treino de 9.495 para 10.814 linhas, mas não aumenta esse máximo. Nos horizontes 1h/6h, os máximos também ficam iguais entre os dois memberships: 1,24/5,41 m.

“Resposta de 12h” é o alvo no horizonte nominal menos a base atrasada, não a diferença entre duas medições exatamente separadas por 12h. Neste acervo, a regra imposta à base de Muçum tem atraso de 15min; as latências históricas reais não foram comprovadas. Não confundir a faixa observada no treino com um limite matemático obrigatório do regressor.

## O problema não se limita às respostas fora da faixa

Na cheia da fase test, para a combinação em 12h:

| Resposta alvo−base em relação ao treino | Pares | Acertos ≤0,50 m | MAE | Viés |
|---|---:|---:|---:|---:|
| Acima do máximo | 12 | 0 | 6,6862 m | −6,6862 m |
| Abaixo do mínimo | 26 | 3 | 1,7242 m | +1,7242 m |
| Dentro da faixa | 198 | 77 | 0,9558 m | −0,4563 m |

Os três grupos somam os 236 pares e 80 acertos do relatório anterior. Existe ainda **um alvo de cheia sem previsão**, fora desses grupos porque falta a base e não é possível calcular a resposta. Ele continua registrado como falha, não como ausência de cheia.

Mesmo o grupo dentro da faixa só acerta 77/198; ampliar a amplitude do histórico, sozinho, não demonstraria a meta. O sinal dos erros fora da faixa é compatível com respostas subestimadas nas subidas e superestimadas nas descidas, mas esta estratificação não identifica a causa isolada.

O dia-alvo 22/07 tem 23 pares, MAE 4,3923 m e responde por 11,58% da soma dos erros absolutos dos 1.915 pares de test em 12h. O dia 23/07 acrescenta 5,35%. São agrupamentos por dia civil para diagnóstico, não eventos hidrológicos independentes certificados; o número de pares por dia não garante observação completa.

## Sinais disponíveis e limitações da atribuição

Na origem 19h, apesar da ausência do nível do Carreiro, a entrada de chuva acumulada de 12h dessa bacia é 75,0461 mm; a do Baixo Antas é 52,4065 mm. A vazão defluente de Julho representada na entrada é 944 m³/s e a afluente 1.170 m³/s. São valores do vetor histórico atrasado, não certificados como disponíveis naquele instante. Os modelos já tinham esses campos: a auditoria não demonstrou que adicioná-los novamente resolveria o erro.

As 2.448 células do vetor completo nas 12 origens estão em `july-input-window.csv`, na ordem das 204 colunas congeladas. Vazões Q/I nesse CSV estão divididas por 1.000, conforme o modelo. `training-response-ranges.csv` registra máximos, mínimos e origens por corte/horizonte/membership. `response-strata.csv` preserva os resultados de todas as quatro versões, 12 horizontes e dois cortes. `largest-errors.csv` guarda 20 maiores por versão; a seleção é explicitamente posterior aos resultados.

## Conferência do Carreiro na fonte original

Em `outputs/mucum-propagacao-2026-09-21/raw/ana-86500000.xml`, a janela 21/07 de 11h30 a 23h tem todos os **47 registros de 15min**, porém **46 têm NivelFinal vazio e CQ ausente**. A única leitura preenchida é das 17h: 570 cm, “Dado aprovado”. Portanto, nesse trecho não são registros faltantes nem níveis descartados por rejeição de qualidade: os níveis já vêm vazios da fonte. O trecho e o hash estão em `carreiro-source-check.json`.

O atraso imposto de 30min disponibiliza os 5,70 m às 17h30 na grade intermediária. Na consulta das 17h45, o registro selecionado passa a ser o das 17h15, com nível vazio; a implementação preserva esse vazio e não procura um valor antigo preenchido. Assim, nenhuma das 12 origens horárias recebe o nível; seus seis campos derivados permanecem NaN. A revisão independente reproduziu exatamente os primeiros 24 campos nessas origens: 72 células Carreiro ausentes em 288, com os outros 18 campos sempre finitos.

Na janela ampliada de 03h30 a 23h, a revisão independente contou 79/79 níveis aprovados em cada um dos outros três postos, contra 2/79 no Carreiro (07h=2,36 m e 17h=5,70 m). Isso não autoriza estender a última leitura através de vazios sem política de idade e qualidade. A vazão reportada do Carreiro também tem uma leitura isolada às 17h entre valores muito diferentes, mas QCarreiro não integra diretamente os 120 campos atuais do Radar; não atribuímos os erros a esse campo.

Próximas hipóteses a distinguir: amplitude insuficiente de respostas no treino e relação entre chuva/propagação e nível que os modelos atuais não aprenderam, preservando a falha real da série de níveis. Não atribuir todo o erro a um sensor nem promover correção baseada apenas neste episódio. Os dados de cheias antigas já coletados precisam manter seus critérios de referência, disponibilidade e regime operacional antes de entrar em novos candidatos.

Reprodução local, sem chamadas de rede ou treinamento:

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/radar-hge-venv/bin/python outputs/diagnostico-extremos-radar-20260921/diagnose.py
```

O nome histórico do ambiente não implica execução do modelo retirado. O escopo desta análise é somente Radar. A meta de 98% permanece não demonstrada.
