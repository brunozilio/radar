# Exposição controlada à ausência do Carreiro

A única alteração é tornar NaN os seis campos do Carreiro em uma seleção fixa de origens do treino, com probabilidade25% e PCG64(58). Mesmas amostras, ordem, pesos, alvos,180colunas e configurações da mistura anterior; uma linha por origem. Avaliação nos dados reais originais, sem mascaramento adicional. Não simula duração ou causa das falhas, nem demonstra causalidade. Períodos já conhecidos de desenvolvimento.

Recorte observado >=7 m, todos os horários. Falhas no denominador. Erros em metros.

| Corte | Perfil | h | Acertos mistura → com exposição / alvos | Controle do perfil: acertos | MAE original → com exposição | Máximo original → com exposição |
|---|---|---:|---:|---:|---:|---:|
| test | A | 1 | 231 → 231 / 237 | 230 | 0.0763 → 0.0763 | 1.1414 → 1.0893 |
| test | A | 6 | 170 → 158 / 237 | 162 | 0.6021 → 0.5987 | 6.2996 → 5.9690 |
| test | A | 12 | 75 → 78 / 237 | 91 | 1.3287 → 1.3028 | 7.7928 → 7.5681 |
| test | B | 1 | 230 → 230 / 237 | 230 | 0.1051 → 0.1029 | 1.5158 → 1.4594 |
| test | B | 6 | 166 → 153 / 237 | 154 | 0.6355 → 0.6288 | 6.5058 → 6.3322 |
| test | B | 12 | 75 → 81 / 237 | 77 | 1.3849 → 1.3624 | 7.6069 → 7.4350 |
| validation | A | 1 | 28 → 28 / 28 | 28 | 0.0550 → 0.0580 | 0.1946 → 0.2654 |
| validation | A | 6 | 24 → 23 / 28 | 21 | 0.2403 → 0.2607 | 0.7705 → 0.6288 |
| validation | A | 12 | 8 → 10 / 28 | 8 | 0.8212 → 0.7500 | 1.5442 → 1.6265 |
| validation | B | 1 | 28 → 28 / 28 | 28 | 0.1005 → 0.1002 | 0.3233 → 0.3323 |
| validation | B | 6 | 23 → 26 / 28 | 24 | 0.2344 → 0.2858 | 0.8879 → 0.8706 |
| validation | B | 12 | 8 → 10 / 28 | 11 | 0.8993 → 0.8561 | 1.7499 → 1.7630 |

Comparações completas contra a mistura, contra o controle do perfil e contra o controle cruzado estão no CSV. Melhorar a mistura anterior não implica superar o controle dedicado. Não selecionar perfis ou horizontes favoráveis. Nenhuma promoção ou comprovação da meta de 98%.

## Disponibilidade real do Carreiro

A partição abaixo usa os seis campos reais de entrada, sem mascarar a avaliação. É diagnóstico posterior, não critério para escolher versões. No recorte alto, alvos de verdade ausente continuam separados e não são considerados cheias.

| Perfil | h | Carreiro real | Acertos original → candidato / alvos |
|---|---:|---|---:|
| A | 6 | complete | 113 → 102 / 140 |
| A | 6 | partial | 15 → 15 / 15 |
| A | 6 | fully_missing | 42 → 41 / 82 |
| A | 12 | complete | 58 → 59 / 140 |
| A | 12 | partial | 3 → 3 / 9 |
| A | 12 | fully_missing | 14 → 16 / 88 |
| B | 6 | complete | 109 → 99 / 140 |
| B | 6 | partial | 15 → 14 / 15 |
| B | 6 | fully_missing | 42 → 40 / 82 |
| B | 12 | complete | 57 → 59 / 140 |
| B | 12 | partial | 3 → 3 / 9 |
| B | 12 | fully_missing | 15 → 19 / 88 |
