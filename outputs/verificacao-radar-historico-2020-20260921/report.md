# RADAR: acréscimo de histórico de2020

Ensaio local de desenvolvimento com24 modelos novos e24 controles congelados. O candidato usa os mesmos120 campos e parâmetros da referência que aceita entradas auxiliares ausentes, acrescentando todo o intervalo de 01–20/07/2020 permitido pelo protocolo. Nenhuma promoção ou mudança operacional.

Acerto: erro absoluto≤0,50m. Cheia: observado≥7m, recorte analítico. As fases validation/test já foram examinadas e não são holdout independente.

| Fase | Horizonte | Versão | Acertos/pares cheia | Acertos/alvos incluindo falhas | MAE(m) | Maior erro(m) |
|---|---:|---|---:|---:|---:|---:|
| validation | 1h | Referência120 | 28/28 | 28/28 | 0.0667 | 0.2537 |
| validation | 1h | +2020 | 28/28 | 28/28 | 0.0633 | 0.2494 |
| validation | 6h | Referência120 | 24/28 | 24/28 | 0.2587 | 1.0963 |
| validation | 6h | +2020 | 21/28 | 21/28 | 0.3551 | 1.3860 |
| validation | 12h | Referência120 | 7/28 | 7/28 | 0.9085 | 2.6195 |
| validation | 12h | +2020 | 7/28 | 7/28 | 0.8928 | 2.6270 |
| test | 1h | Referência120 | 230/236 | 230/237 | 0.0775 | 1.2848 |
| test | 1h | +2020 | 231/236 | 231/237 | 0.0648 | 0.9375 |
| test | 6h | Referência120 | 149/236 | 149/237 | 0.5993 | 5.7173 |
| test | 6h | +2020 | 163/236 | 163/237 | 0.5361 | 4.7045 |
| test | 12h | Referência120 | 83/236 | 83/237 | 1.3618 | 7.5900 |
| test | 12h | +2020 | 87/236 | 87/237 | 1.2303 | 7.9746 |

## Efeito em todos os horizontes de cheia

| Fase | Horizonte | Diferença de acertos | Diferença MAE(m) | Diferença maior erro(m) |
|---|---:|---:|---:|---:|
| validation | 1h | +0 | -0.0033 | -0.0042 |
| validation | 2h | +0 | -0.0020 | +0.0109 |
| validation | 3h | +0 | -0.0193 | -0.0634 |
| validation | 4h | -3 | +0.1257 | +0.1492 |
| validation | 5h | +0 | +0.0064 | +0.1401 |
| validation | 6h | -3 | +0.0964 | +0.2897 |
| validation | 7h | +4 | -0.0615 | -1.0452 |
| validation | 8h | +1 | -0.1124 | -1.7449 |
| validation | 9h | -2 | -0.1051 | -1.1570 |
| validation | 10h | -1 | -0.0281 | +0.0070 |
| validation | 11h | +2 | -0.1429 | -0.4357 |
| validation | 12h | +0 | -0.0157 | +0.0075 |
| test | 1h | +1 | -0.0127 | -0.3473 |
| test | 2h | +0 | -0.0123 | -0.7455 |
| test | 3h | +12 | -0.0353 | -0.4719 |
| test | 4h | +6 | -0.0357 | -0.3700 |
| test | 5h | +6 | -0.0353 | -0.5348 |
| test | 6h | +14 | -0.0632 | -1.0128 |
| test | 7h | +32 | -0.1881 | -0.9734 |
| test | 8h | +15 | -0.1660 | -0.7398 |
| test | 9h | +11 | -0.1598 | +0.1688 |
| test | 10h | +16 | -0.1218 | -0.0164 |
| test | 11h | +16 | -0.0864 | +0.9600 |
| test | 12h | +4 | -0.1315 | +0.3846 |

## Dados e limites

Em12h entram426 pares, dos quais167 com alvo≥7m. A maior resposta no treino passa de8.09m para11.53m. Não há seleção dos exemplos extremos: todo o intervalo elegível de01–20/07 foi incluído.

As102.084 linhas de avaliação, os alvos, as bases e a disponibilidade de previsão são idênticos. O novo histórico nunca cruza o hiato2020–2025 no cálculo de alvos. Alvos ausentes e os últimos h exemplos permanecem inelegíveis. Carreiro e Santa Tereza continuam ausentes. O arquivo evaluation.csv contém todos os horizontes, recortes e falhas, inclusive linhas sem alvo.

Auditoria:24 modelos reproduzidos exatamente;288 linhas de métricas recalculadas;144 linhas de métricas do controle coincidem com a referência. Máscaras, cortes, parâmetros, contagens por árvore e hashes conferidos.

Não comprova98% prospectivos. Publicação histórica, revisão de fontes, fuso, datum e comparabilidade entre regimes não estão certificados. Mais dados podem ajudar alguns horizontes e piorar outros; não montar uma combinação de versões por horizonte usando este conjunto já visto. O próximo candidato exige protocolo próprio e mantém estes resultados como desenvolvimento.
