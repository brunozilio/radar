# Decisão: candidato ET0 não promovido

A série ERA5 acrescentou 12.792 horas válidas de ET0 estimada, com atraso no fim da série.
O treino usou dados anteriores a 01/07/2026. A comparação usa o mesmo recorte retrospectivo
já examinado, portanto não é nova validação independente nem prova de precisão futura.

| Medida | HGE anterior | Candidato ET0 |
|---|---:|---:|
| MAE geral | 0,411 m | 0,412 m |
| MAE acima de 7 m | 0,888 m | 0,903 m |

O candidato não melhorou as cheias e não substitui a referência. A fonte continua disponível
para pesquisas posteriores. O próximo lote prioriza eventos extremos e qualidade das entradas,
sem retunar repetidamente o mesmo teste até conseguir um resultado favorável.

Seis testes de física/ET0 e três do placar passaram. As assinaturas do código, fontes e
resultados estão no registro de decisão em experiments/hge-water-balance/decisions/.
