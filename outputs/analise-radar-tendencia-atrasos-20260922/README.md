# Tendência e amplitude dos erros de 6–12 horas

Análise exploratória posterior de períodos conhecidos, sem novos ajustes. Os perfis A e B representam duas reconstruções dos mesmos horários, não observações independentes.

Na tabela, candidato com idade; recorte observado >=7m. Erro = previsão menos observado. Tendência conhecida é dH1 por hora nominal; resposta futura é observado menos base, usada somente como rótulo diagnóstico.

| Perfil | h | Partição | Grupo | Acertos / alvos | Pares | MAE m | Viés m |
|---|---:|---|---|---:|---:|---:|---:|
| A | 6 | known_trend | rising | 40 / 81 | 81 | 1.0000 | -0.5689 |
| A | 6 | known_trend | falling | 59 / 80 | 80 | 0.4050 | 0.1253 |
| A | 6 | known_trend | stable | 66 / 74 | 74 | 0.3989 | -0.0885 |
| A | 6 | known_trend | unknown | 0 / 2 | 1 | 0.6176 | 0.6176 |
| A | 6 | future_response | rising | 38 / 76 | 76 | 1.1464 | -0.8695 |
| A | 6 | future_response | falling | 80 / 102 | 102 | 0.3435 | 0.2013 |
| A | 6 | future_response | stable | 47 / 58 | 58 | 0.3684 | 0.0613 |
| A | 6 | future_response | unknown | 0 / 1 | 0 | — | — |
| A | 6 | training_response_support | below | 8 / 27 | 27 | 0.7429 | 0.7429 |
| A | 6 | training_response_support | within | 157 / 202 | 202 | 0.4317 | -0.1276 |
| A | 6 | training_response_support | above | 0 / 7 | 7 | 5.1822 | -5.1822 |
| A | 6 | training_response_support | unknown | 0 / 1 | 0 | — | — |
| A | 12 | known_trend | rising | 27 / 96 | 96 | 1.4133 | -0.5518 |
| A | 12 | known_trend | falling | 23 / 66 | 66 | 1.1904 | 0.2658 |
| A | 12 | known_trend | stable | 25 / 73 | 73 | 1.3221 | -0.8466 |
| A | 12 | known_trend | unknown | 0 / 2 | 1 | 2.8043 | 2.8043 |
| A | 12 | future_response | rising | 26 / 105 | 105 | 1.9055 | -1.3622 |
| A | 12 | future_response | falling | 37 / 110 | 110 | 0.9229 | 0.4075 |
| A | 12 | future_response | stable | 12 / 21 | 21 | 0.5701 | 0.1801 |
| A | 12 | future_response | unknown | 0 / 1 | 0 | — | — |
| A | 12 | training_response_support | below | 3 / 26 | 26 | 1.8143 | 1.8143 |
| A | 12 | training_response_support | within | 72 / 198 | 198 | 0.9833 | -0.3530 |
| A | 12 | training_response_support | above | 0 / 12 | 12 | 5.9753 | -5.9753 |
| A | 12 | training_response_support | unknown | 0 / 1 | 0 | — | — |
| B | 6 | known_trend | rising | 40 / 85 | 85 | 1.0275 | -0.5775 |
| B | 6 | known_trend | falling | 58 / 80 | 80 | 0.4389 | 0.1743 |
| B | 6 | known_trend | stable | 61 / 70 | 70 | 0.3991 | -0.0948 |
| B | 6 | known_trend | unknown | 0 / 2 | 1 | 0.6768 | 0.6768 |
| B | 6 | future_response | rising | 38 / 78 | 78 | 1.1904 | -0.9092 |
| B | 6 | future_response | falling | 81 / 103 | 103 | 0.3717 | 0.2486 |
| B | 6 | future_response | stable | 40 / 55 | 55 | 0.3622 | 0.0765 |
| B | 6 | future_response | unknown | 0 / 1 | 0 | — | — |
| B | 6 | training_response_support | below | 11 / 30 | 30 | 0.7697 | 0.7697 |
| B | 6 | training_response_support | within | 148 / 198 | 198 | 0.4402 | -0.1182 |
| B | 6 | training_response_support | above | 0 / 8 | 8 | 5.1004 | -5.1004 |
| B | 6 | training_response_support | unknown | 0 / 1 | 0 | — | — |
| B | 12 | known_trend | rising | 28 / 98 | 98 | 1.4282 | -0.5435 |
| B | 12 | known_trend | falling | 25 / 66 | 66 | 1.2236 | 0.3256 |
| B | 12 | known_trend | stable | 22 / 71 | 71 | 1.4504 | -1.0066 |
| B | 12 | known_trend | unknown | 0 / 2 | 1 | 3.1472 | 3.1472 |
| B | 12 | future_response | rising | 24 / 105 | 105 | 1.9847 | -1.4653 |
| B | 12 | future_response | falling | 39 / 109 | 109 | 0.9504 | 0.4280 |
| B | 12 | future_response | stable | 12 / 22 | 22 | 0.6749 | 0.3236 |
| B | 12 | future_response | unknown | 0 / 1 | 0 | — | — |
| B | 12 | training_response_support | below | 2 / 27 | 27 | 1.8753 | 1.8753 |
| B | 12 | training_response_support | within | 73 / 197 | 197 | 1.0203 | -0.3833 |
| B | 12 | training_response_support | above | 0 / 12 | 12 | 6.2669 | -6.2669 |
| B | 12 | training_response_support | unknown | 0 / 1 | 0 | — | — |

Em 12h, as 12 respostas acima do máximo de treino em cada perfil têm zero acertos e subestimação média de 5,9753m (A) e 6,2669m (B). Porém, dentro da faixa de respostas treinadas, há apenas 72/198 e 73/197 acertos. Suporte univariado não prova similaridade de todos os inputs e ampliar extremos sozinho não resolveria o problema.

Na ablação da idade em 6h, perfil A: a tendência de subida conhecida ganha um acerto e perde um; a descida perde três e a estabilidade perde dois. Perfil B: subida ganha um e perde quatro; descida e estabilidade perdem dois cada. Não há justificativa para uma correção constante positiva: existem erros nas duas direções.

As 4.608 métricas cobrem os 12 horizontes, quatro famílias e ambos os cortes/perfis; reconciliam 9.216 contagens/médias com o placar congelado. Falhas de previsão continuam no denominador observado. No recorte >=7m, unknown_truth é mantido separadamente e não é considerado alvo alto ou acerto. Todos os dias permanecem na avaliação.

O diagnóstico orienta testar uma componente linear das tendências com árvores de resíduos, mantendo máscaras e pesos. Isso é uma nova hipótese de desenvolvimento, não demonstração de causalidade, promessa de melhora ou promoção.
