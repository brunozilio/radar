# Tendências lineares com árvores dos resíduos

Candidato aditivo: ridge de 20 tendências existentes mais árvore de resíduos com os 180 campos originais. Mesmas amostras, ordem, pesos, alvos e configurações das árvores da mistura anterior. Ridge alpha1000 fixo, mediana não ponderada e padronização ponderada ajustadas somente no treino. Períodos já conhecidos; não prova generalização nem publicação histórica. O componente linear isolado também está no placar completo.

Recorte observado >=7 m, todos os horários. Falhas no denominador. Erros em metros.

| Corte | Perfil | h | Acertos árvores → híbrido / alvos | Controle do perfil: acertos | MAE árvores → híbrido | Máximo árvores → híbrido |
|---|---|---:|---:|---:|---:|---:|
| test | A | 1 | 231 → 233 / 237 | 230 | 0.0763 → 0.0574 | 1.1414 → 0.9270 |
| test | A | 6 | 170 → 165 / 237 | 162 | 0.6021 → 0.4513 | 6.2996 → 4.0801 |
| test | A | 12 | 75 → 91 / 237 | 91 | 1.3287 → 1.1107 | 7.7928 → 8.9919 |
| test | B | 1 | 230 → 233 / 237 | 230 | 0.1051 → 0.0712 | 1.5158 → 1.0790 |
| test | B | 6 | 166 → 161 / 237 | 154 | 0.6355 → 0.4734 | 6.5058 → 4.5216 |
| test | B | 12 | 75 → 94 / 237 | 77 | 1.3849 → 1.1675 | 7.6069 → 8.9139 |
| validation | A | 1 | 28 → 28 / 28 | 28 | 0.0550 → 0.0389 | 0.1946 → 0.1728 |
| validation | A | 6 | 24 → 22 / 28 | 21 | 0.2403 → 0.4292 | 0.7705 → 1.6750 |
| validation | A | 12 | 8 → 13 / 28 | 8 | 0.8212 → 0.6530 | 1.5442 → 2.2479 |
| validation | B | 1 | 28 → 28 / 28 | 28 | 0.1005 → 0.0910 | 0.3233 → 0.3162 |
| validation | B | 6 | 23 → 20 / 28 | 24 | 0.2344 → 0.4654 | 0.8879 → 1.6787 |
| validation | B | 12 | 8 → 15 / 28 | 11 | 0.8993 → 0.6155 | 1.7499 → 1.9594 |

Comparações completas contra as árvores da mistura, contra o controle do perfil e contra o controle cruzado estão no CSV. Melhorar a mistura anterior não implica superar o controle dedicado. Não selecionar perfis ou horizontes favoráveis. Nenhuma promoção ou comprovação da meta de 98%.

## Limitações observadas

Nas cheias de test, o híbrido melhora MAE nos 12 horizontes dos dois perfis e acertos em 11, mas perde cinco acertos em 6h em cada perfil. No conjunto de todos os níveis contra a mistura, há menos acertos em sete horizontes de A e quatro de B. Na validation de cheia, perde acertos em cinco horizontes de A e seis de B. Não há ganho sustentado em todos os recortes.

Em test/12h, o pior erro aumenta de 7,7928 para 8,9919m no perfil A e de 7,6069 para 8,9139m em B. São subestimações na subida de julho, não excesso de nível gerado por extrapolação linear. No pior A, origem21/07 às16h, base3,27m e alvo14,49m: ridge acrescenta0,6689m, árvore de resíduos1,5592m e o híbrido prevê5,4981m (mistura anterior6,6972m). As cinco tendências do Carreiro estão ausentes e são imputadas por medianas só para ridge; a árvore mantém os NaNs originais. Isso descreve o cálculo, não identifica causalidade da falta. Os seis maiores casos e as120contribuições estão nos CSVs.

O acerto de 233/237 em1h (98,31%) é um resultado histórico de desenvolvimento em uma antecedência nominal, com uma falha no denominador. Não prova a meta prospectiva em1–12h nem dez cheias independentes. Sem promoção, troca de horizonte, recorte favorável ou novo ajuste após os resultados.
