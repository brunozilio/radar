# Decisão após o experimento de junho

O candidato não será promovido. No recorte de níveis observados≥7m do período de teste, os12horizontes ganharam acertos e reduziram MAE. Porém, no período de validação anterior, sete horizontes perderam acertos e nove tiveram MAE maior. O pior erro também cresceu em três horizontes do teste e dez da validação. Ganho em um período não demonstra melhoria sustentada.

Exemplos no teste, sempre237alvos,236pares e1falha:

| Horizonte | Acertos anteriores | Acertos com junho | MAE anterior → junho |
|---|---:|---:|---:|
| 1h |230|231|0,077 →0,067m|
| 6h |149|157|0,599 →0,564m|
| 12h |83|89|1,362 →1,226m|

Mesmo1h chega somente a231/237alvos observados (97,47%); excluir a falha mudaria o denominador e não resolveria a amostra insuficiente. Esses números são desenvolvimento histórico conhecido, não acurácia prospectiva certificada. A meta exige os12horizontes e o recorte decheia, além do volume e independência deeventos definidos.

`scheduled_rows` inclui toda a agenda daquele horizonte/população. Em `all`, agenda menos observados identifica verdade desconhecida. Em `level_ge_7m`, essa diferença também contém valores conhecidos abaixo7m: não deve ser chamada de ausência. A auditoria independente salva `denominator-partition.csv` para distinguir essas situações; nenhuma falha virou acerto.

Os dados de junho ampliaram o conjunto de exemplos de subida forte, mas seu regime pós-avaria e conflitos de vazão continuam limitações. Este resultado não permite atribuir causalidade à ampliação nem selecionar apenas horizontes favoráveis. Nenhum modelo em operação foi trocado. A investigação seguinte deve explicar as regressões da validação antes de propor outra variante; qualquer evidência de promoção precisará de avaliação não usada no ajuste e dos critérios prospectivos.
