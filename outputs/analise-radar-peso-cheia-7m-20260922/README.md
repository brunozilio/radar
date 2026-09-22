# Peso de treino alinhado ao recorte analítico de 7m

A única mudança é o limiar do peso adicional por nível alvo, de9m para7m. Cada amostra de treino em[7,9) ganha2; as demais ficam iguais. Mesmos180campos, amostras, ordem, alvos, bases e configurações.7m continua recorte analítico, não cota oficial. Períodos já conhecidos; não é nova validação independente.

Recorte observado >=7 m, todos os horários. Falhas no denominador. Erros em metros.

| Corte | Perfil | h | Acertos mistura → peso7m / alvos | Controle do perfil: acertos | MAE mistura → peso7m | Máximo mistura → peso7m |
|---|---|---:|---:|---:|---:|---:|
| test | A | 1 | 231 → 231 / 237 | 230 | 0.0763 → 0.0775 | 1.1414 → 1.1736 |
| test | A | 6 | 170 → 166 / 237 | 162 | 0.6021 → 0.6065 | 6.2996 → 6.3078 |
| test | A | 12 | 75 → 67 / 237 | 91 | 1.3287 → 1.3413 | 7.7928 → 7.5320 |
| test | B | 1 | 230 → 230 / 237 | 230 | 0.1051 → 0.1026 | 1.5158 → 1.5507 |
| test | B | 6 | 166 → 169 / 237 | 154 | 0.6355 → 0.6406 | 6.5058 → 6.4804 |
| test | B | 12 | 75 → 68 / 237 | 77 | 1.3849 → 1.3923 | 7.6069 → 7.6053 |
| validation | A | 1 | 28 → 28 / 28 | 28 | 0.0550 → 0.0527 | 0.1946 → 0.1961 |
| validation | A | 6 | 24 → 24 / 28 | 21 | 0.2403 → 0.2488 | 0.7705 → 0.6734 |
| validation | A | 12 | 8 → 6 / 28 | 8 | 0.8212 → 0.7612 | 1.5442 → 1.5128 |
| validation | B | 1 | 28 → 28 / 28 | 28 | 0.1005 → 0.1025 | 0.3233 → 0.3596 |
| validation | B | 6 | 23 → 22 / 28 | 24 | 0.2344 → 0.2633 | 0.8879 → 0.8568 |
| validation | B | 12 | 8 → 8 / 28 | 11 | 0.8993 → 0.8435 | 1.7499 → 1.5407 |

Comparações completas contra a mistura, contra o controle do perfil e contra o controle cruzado estão no CSV. Melhorar a mistura anterior não implica superar o controle dedicado. Não selecionar perfis ou horizontes favoráveis. Nenhuma promoção ou comprovação da meta de 98%.

## Faixas de nível observado

As fronteiras são as mesmas do protocolo de pesos. Alvos desconhecidos ficam em grupo próprio. As768métricas e192transições mantêm todos os horizontes e recompõem os totais original/all e>=7m. Não são uma seleção de modelo por nível futuro.

| Perfil | h | Faixa | Acertos peso9 → peso7 / observados | MAE peso9 → peso7 |
|---|---:|---|---:|---:|
| A | 1 | below_7m | 1702 → 1703 / 1707 | 0.0439 → 0.0426 |
| A | 1 | 7_to_9m | 119 → 119 / 120 | 0.0434 → 0.0458 |
| A | 1 | ge_9m | 112 → 112 / 117 | 0.1103 → 0.1103 |
| A | 6 | below_7m | 1610 → 1607 / 1702 | 0.1529 → 0.1571 |
| A | 6 | 7_to_9m | 111 → 107 / 120 | 0.2920 → 0.2785 |
| A | 6 | ge_9m | 59 → 59 / 117 | 0.9229 → 0.9458 |
| A | 12 | below_7m | 1229 → 1224 / 1696 | 0.3806 → 0.3816 |
| A | 12 | 7_to_9m | 44 → 39 / 120 | 0.7660 → 0.8015 |
| A | 12 | ge_9m | 31 → 28 / 117 | 1.9107 → 1.8999 |
| B | 1 | below_7m | 1701 → 1701 / 1707 | 0.0381 → 0.0376 |
| B | 1 | 7_to_9m | 119 → 119 / 120 | 0.0632 → 0.0606 |
| B | 1 | ge_9m | 111 → 111 / 117 | 0.1484 → 0.1460 |
| B | 6 | below_7m | 1607 → 1611 / 1702 | 0.1545 → 0.1576 |
| B | 6 | 7_to_9m | 108 → 112 / 120 | 0.2951 → 0.2785 |
| B | 6 | ge_9m | 58 → 57 / 117 | 0.9878 → 1.0152 |
| B | 12 | below_7m | 1242 → 1248 / 1696 | 0.3753 → 0.3756 |
| B | 12 | 7_to_9m | 49 → 40 / 120 | 0.7815 → 0.8255 |
| B | 12 | ge_9m | 26 → 28 / 117 | 2.0092 → 1.9786 |
