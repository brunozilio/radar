# RADAR: acréscimo de histórico de2023

Ensaio local de desenvolvimento com24 modelos novos e24 controles congelados. O candidato usa os mesmos120 campos e parâmetros da referência que aceita entradas auxiliares ausentes, acrescentando todo o intervalo de setembro/2023 permitido pelo protocolo. Nenhuma promoção ou mudança operacional.

Acerto: erro absoluto≤0,50m. Cheia: observado≥7m, recorte analítico. As fases validation/test já foram examinadas e não são holdout independente.

| Fase | Horizonte | Versão | Acertos/pares cheia | Acertos/alvos incluindo falhas | MAE(m) | Maior erro(m) |
|---|---:|---|---:|---:|---:|---:|
| validation | 1h | Referência120 | 28/28 | 28/28 | 0.0667 | 0.2537 |
| validation | 1h | +2023 | 28/28 | 28/28 | 0.0759 | 0.2845 |
| validation | 6h | Referência120 | 24/28 | 24/28 | 0.2587 | 1.0963 |
| validation | 6h | +2023 | 18/28 | 18/28 | 0.5313 | 2.1068 |
| validation | 12h | Referência120 | 7/28 | 7/28 | 0.9085 | 2.6195 |
| validation | 12h | +2023 | 3/28 | 3/28 | 1.2107 | 2.9068 |
| test | 1h | Referência120 | 230/236 | 230/237 | 0.0775 | 1.2848 |
| test | 1h | +2023 | 229/236 | 229/237 | 0.1006 | 0.7767 |
| test | 6h | Referência120 | 149/236 | 149/237 | 0.5993 | 5.7173 |
| test | 6h | +2023 | 154/236 | 154/237 | 0.5457 | 4.5135 |
| test | 12h | Referência120 | 83/236 | 83/237 | 1.3618 | 7.5900 |
| test | 12h | +2023 | 89/236 | 89/237 | 1.2567 | 7.3628 |

## Efeito em todos os horizontes de cheia

| Fase | Horizonte | Diferença de acertos | Diferença MAE(m) | Diferença maior erro(m) |
|---|---:|---:|---:|---:|
| validation | 1h | +0 | +0.0092 | +0.0308 |
| validation | 2h | +0 | +0.0105 | +0.0858 |
| validation | 3h | -1 | +0.0344 | -0.0209 |
| validation | 4h | +0 | +0.0739 | +0.2885 |
| validation | 5h | +0 | +0.0963 | +0.4800 |
| validation | 6h | -6 | +0.2726 | +1.0105 |
| validation | 7h | -5 | +0.1750 | +0.8676 |
| validation | 8h | -9 | +0.3413 | +0.7460 |
| validation | 9h | -9 | +0.4341 | +0.8690 |
| validation | 10h | -5 | +0.4212 | +1.5990 |
| validation | 11h | -4 | +0.3239 | +0.9796 |
| validation | 12h | -4 | +0.3023 | +0.2873 |
| test | 1h | -1 | +0.0231 | -0.5081 |
| test | 2h | -16 | +0.0485 | -1.3900 |
| test | 3h | +5 | -0.0026 | -0.4391 |
| test | 4h | +5 | -0.0346 | -0.6318 |
| test | 5h | -5 | +0.0130 | -0.3978 |
| test | 6h | +5 | -0.0536 | -1.2038 |
| test | 7h | -6 | -0.0159 | -1.9238 |
| test | 8h | +7 | -0.1112 | -2.2726 |
| test | 9h | +8 | -0.1117 | -1.4692 |
| test | 10h | +4 | -0.1321 | -1.6944 |
| test | 11h | +4 | -0.0491 | -0.7455 |
| test | 12h | +6 | -0.1051 | -0.2272 |

## Dados e limites

Em12h entram481 pares, dos quais45 com alvo≥7m. A maior resposta no treino passa de8.09m para12.59m. Não há seleção dos exemplos extremos: o mês inteiro elegível foi incluído.

As102.084 linhas de avaliação, os alvos, as bases e a disponibilidade de previsão são idênticos. O novo histórico nunca cruza o hiato2023–2025 no cálculo de alvos. Alvos ausentes e os últimos h exemplos permanecem inelegíveis. Carreiro e Santa Tereza continuam ausentes. O arquivo evaluation.csv contém todos os horizontes, recortes e falhas, inclusive linhas sem alvo.

Auditoria:24 modelos reproduzidos exatamente;288 linhas de métricas recalculadas;144 linhas de métricas do controle coincidem com a referência. Máscaras, cortes, parâmetros, contagens por árvore e hashes conferidos.

Não comprova98% prospectivos. Publicação histórica, revisão de fontes, fuso, datum e comparabilidade entre regimes não estão certificados. Mais dados podem ajudar alguns horizontes e piorar outros; não montar uma combinação de versões por horizonte usando este conjunto já visto. O próximo candidato exige protocolo próprio e mantém estes resultados como desenvolvimento.
