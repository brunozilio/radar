# Auditoria dos blocos de entradas Radar: 45 e108 campos

Os índices do protocolo foram conferidos contra a função de features congelada, idêntica nas duas matrizes. **45=0..44** conserva os24 campos dos quatro postos de nível e21 campos Q/I das três usinas; remove45..119. **108=0..11+24..119** conserva core33 e chuva; remove12..23 (SantaTereza e Carreiro). A interseção dos conjuntos é core33 e a união é120, sem duplicação de colunas.

O bloco de chuva contém **75 campos:45 de acumulados/defasagens e30 de cobertura**. Remover chuva retira ambos, inclusive a informação de disponibilidade. O CSV columns.csv lista cada posição e participação. A designação levels45 também inclui Q/I, não apenas níveis.

Confirmação2023: as12 colunas auxiliares são NaN em **720/720 origens e8.640/8.640 células**, antes de qualquer máscara. Essa ausência permanece em todos os conjuntos admitidos por horizonte. O corte108 remove esses campos, mas não preenche medições.

## Cobertura h12 nas mesmas máscaras

| Fase/população | Linhas | Linhas com auxiliares faltantes | Linhas com chuva acumulada faltante | Células chuva ausentes | Células cobertura ausentes |
|---|---:|---:|---:|---:|---:|
| validation/original_training | 4348 | 690 | 285 | 658 | 0 |
| validation/added2023_training | 481 | 481 | 408 | 7279 | 0 |
| validation/combined_training | 4829 | 1171 | 693 | 7937 | 0 |
| validation/evaluation_high_full_schedule | 28 | 0 | 0 | 0 | 0 |
| test/original_training | 10814 | 1116 | 1079 | 5407 | 0 |
| test/added2023_training | 481 | 481 | 408 | 7279 | 0 |
| test/combined_training | 11295 | 1597 | 1487 | 12686 | 0 |
| test/evaluation_high_full_schedule | 237 | 97 | 1 | 1 | 0 |

No treino2023 h12, há14.366 células de chuva acumulada finitas, das quais5.377 são zeros;7.279 estão ausentes. Apenas73/481 linhas têm todos45 acumulados finitos. As14.430 células de cobertura são finitas; isso não significa que exista chuva medida para todas as regiões e janelas. Não tratar NaN como zero. As contagens para todos12horizontes, duas fases, treino original/adicionado/combinado e avaliação estão nos CSVs.

Os28 alvos de cheia da validação têm ambos os blocos completos em todos os horizontes. No teste h12 há97/237 origens com alguma falta auxiliar e1/237 com chuva acumulada ausente. O denominador237 preserva o alvo de cheia com base Muçum ausente; não foi filtrado pelo sucesso da previsão.

## Limites da comparação

O experimento45/108 mantém parâmetros e máscaras do algoritmo congelado. Isso mede o efeito de remover grupos de entradas nesse procedimento específico, sem novo ajuste de hiperparâmetros; não estabelece a relevância causal hidrológica de chuva ou estações, nem o melhor modelo possível para cada conjunto.

Disponibilidade nesta auditoria significa campo derivado finito da matriz preservada. Não é uma nova validação de sensores, publicação histórica, datum, fuso ou regime das usinas. A remoção de75 campos também remove30 indicadores de cobertura e pode mudar o comportamento do algoritmo por esse motivo. Não presumir equivalência física entre2023 e2025/26.

Nenhuma máscara mudou e nenhum requisito de completude foi acrescentado; faltas remanescentes continuam NaN. Nenhum modelo foi lido, treinado ou executado, nenhuma consulta externa ou alteração operacional. Script, índices, distribuição por região e rastros das origens de avaliação estão preservados com hashes.
