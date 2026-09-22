# Mistura de perfis de atraso — resultados de desenvolvimento

Cada comparação usa a mesma população de avaliação e o controle treinado no perfil correspondente. A mistura usa uma única amostra por origem, com perfil escolhido por PCG64(57) antes dos ajustes. Os dois perfis são vistas alternativas das mesmas origens, nunca eventos independentes. Todos os períodos já eram conhecidos.

Tabela: observado >=7 m, população completa de horários. Falhas permanecem no denominador. Valores de erro em metros.

| Corte | Perfil | h | Acertos controle → mistura | MAE controle → mistura | Máximo controle → mistura |
|---|---|---:|---:|---:|---:|
| test | A | 1 | 230 → 231 / 237 | 0.0837 → 0.0763 | 1.2985 → 1.1414 |
| test | A | 6 | 162 → 170 / 237 | 0.6129 → 0.6021 | 6.3832 → 6.2996 |
| test | A | 12 | 91 → 75 / 237 | 1.2469 → 1.3287 | 7.5752 → 7.7928 |
| test | B | 1 | 230 → 230 / 237 | 0.0941 → 0.1051 | 1.5101 → 1.5158 |
| test | B | 6 | 154 → 166 / 237 | 0.6423 → 0.6355 | 6.6704 → 6.5058 |
| test | B | 12 | 77 → 75 / 237 | 1.3523 → 1.3849 | 6.9600 → 7.6069 |
| validation | A | 1 | 28 → 28 / 28 | 0.0749 → 0.0550 | 0.3480 → 0.1946 |
| validation | A | 6 | 21 → 24 / 28 | 0.3032 → 0.2403 | 0.9250 → 0.7705 |
| validation | A | 12 | 8 → 8 / 28 | 0.8484 → 0.8212 | 2.0262 → 1.5442 |
| validation | B | 1 | 28 → 28 / 28 | 0.0872 → 0.1005 | 0.2763 → 0.3233 |
| validation | B | 6 | 24 → 23 / 28 | 0.2480 → 0.2344 | 0.8497 → 0.8879 |
| validation | B | 12 | 11 → 8 / 28 | 0.8868 → 0.8993 | 1.8960 → 1.7499 |

Os CSVs completos preservam todos os horizontes, recortes, ausências e também o controle treinado no outro perfil. Não selecionar o melhor perfil por horizonte. Nenhuma promoção operacional ou alegação de 98%.
