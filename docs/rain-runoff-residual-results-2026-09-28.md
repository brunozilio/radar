# Candidato de resposta à chuva para Muçum (1–6 horas)

O protocolo de `rain-runoff-residual-v1` foi gravado antes de executar o backtest. O código está em `scripts/hydro_rain_runoff_residual.py`; os dados, parâmetros e previsões pareadas resultantes estão em `outputs/experimento-chuva-residual-20260928-revisado/`.

O candidato conserva o modelo hidrométrico e acrescenta uma resposta estimada por precipitação observada nas cinco regiões, separando chuva com idades de 0–3, 3–6, 6–12 e 12–24 horas. A entrada termina uma hora antes da origem; a correção é não negativa e limitada a 0,35 m. As duas alternativas usam exatamente os mesmos horários completos. Essa limitação elimina a extrapolação de vários metros vista na inclusão linear anterior, mas também restringe a capacidade de antecipar uma cheia intensa.

| Conjunto H+6 | Horas pareadas | MAE hidrometria | MAE com chuva | Acerto ±0,50 m hidrometria | Acerto ±0,50 m com chuva |
| --- | ---: | ---: | ---: | ---: | ---: |
| Validação inteira | 3.104 | 0,1308 m | 0,1325 m | 98,32% | 98,29% |
| Validação, chuva regional ≥50 mm/6h | 69 (3 episódios) | 0,1144 m | 0,1189 m | 97,10% | 97,10% |
| Validação, chuva regional ≥100 mm/6h | 8 (1 episódio) | 0,0357 m | 0,0606 m | 100% | 100% |
| Teste rotulado | 768 | 0,2115 m | 0,2102 m | 89,97% | 90,23% |
| Teste, nível observado ≥7 m | 77 (4 episódios) | 0,5331 m | 0,5232 m | 58,44% | 59,74% |
| Teste, chuva regional ≥50 mm/6h | 1 | 1,5574 m | 1,3609 m | 0% | 0% |
| Cheia posterior de setembro | 4 | 1,6326 m | 1,4704 m | 25% | 25% |

Na validação H+6, as 69 horas de chuva ≥50 mm não geraram falsos aumentos previstos de ≥1 m por nenhum dos braços. A maior correção do candidato nessa fase foi 0,128 m. Na cheia posterior, chegou a 0,325 m, mas o erro médio continuou 1,47 m. Em H+1–H+5, os resultados também são pequenos e mistos; o relatório JSON registra cada horizonte e estrato. Horas próximas são dependentes; três episódios chuvosos não são evidência de acurácia em cheias futuras.

O episódio de 12/03/2026 ilustra a diferença espacial: por volta de 21h UTC, a chuva acumulada em seis horas era 102,1 mm no **Alto Antas**, mas apenas 0,1 mm no Baixo Antas, 1,0 mm no Carreiro e 2,7 mm no Prata-Turvo. O nível em Muçum ficou perto de 0,92–0,94 m nas seis horas seguintes e chegou a 1,09 m após 24 horas. O máximo de chuva regional, sem origem e propagação, foi um sinal inadequado de subida imediata nesse caso.

**Decisão: não promover.** O candidato reduz um pouco alguns erros no teste e na cheia de setembro, mas piora a validação H+6 e ainda falha nos horários críticos. Ele não fornece a precisão solicitada para o nível das próximas seis horas.

Limitações adicionais: a hora em que a chuva histórica chegou ao sistema não foi reconstruída; nenhuma previsão meteorológica emitida anteriormente entra no modelo, portanto uma tempestade futura ainda não é visível; chuva acima de 40 mm em uma faixa de idade é comprimida e sinalizada como fora do suporte numérico. O arquivo de 2024 contém Muçum até 23,81 m, mas `raw:86500000:H` está ausente em todos os 3.264 registros. O modelo público de dez entradas não pode ser reavaliado nesse evento sem uma política de ausência ou proxy previamente definida. Os períodos de teste de 2026 também já foram inspecionados por pesquisas anteriores e não são uma confirmação independente.
