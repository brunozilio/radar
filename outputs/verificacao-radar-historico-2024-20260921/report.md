# RADAR: acréscimo de histórico de2024

Ensaio local de desenvolvimento com24 modelos novos e24 controles congelados. O candidato usa os mesmos180 campos e parâmetros da referência que aceita entradas auxiliares ausentes, acrescentando todo o intervalo de abril a01/05/2024 permitido pelo protocolo. Nenhuma promoção ou mudança operacional.

Acerto: erro absoluto≤0,50m. Cheia: observado≥7m, recorte analítico. As fases validation/test já foram examinadas e não são holdout independente.

| Fase | Horizonte | Versão | Acertos/pares cheia | Acertos/alvos incluindo falhas | MAE(m) | Maior erro(m) |
|---|---:|---|---:|---:|---:|---:|
| validation | 1h | Referência180 | 28/28 | 28/28 | 0.0670 | 0.2440 |
| validation | 1h | +2024 | 28/28 | 28/28 | 0.0677 | 0.2231 |
| validation | 6h | Referência180 | 24/28 | 24/28 | 0.2594 | 1.3088 |
| validation | 6h | +2024 | 24/28 | 24/28 | 0.2936 | 1.3634 |
| validation | 12h | Referência180 | 8/28 | 8/28 | 0.9251 | 2.6072 |
| validation | 12h | +2024 | 10/28 | 10/28 | 0.8939 | 2.1863 |
| test | 1h | Referência180 | 230/236 | 230/237 | 0.0775 | 1.2760 |
| test | 1h | +2024 | 231/236 | 231/237 | 0.0687 | 1.0015 |
| test | 6h | Referência180 | 147/236 | 147/237 | 0.6010 | 5.6437 |
| test | 6h | +2024 | 155/236 | 155/237 | 0.5434 | 5.2704 |
| test | 12h | Referência180 | 86/236 | 86/237 | 1.3408 | 7.9215 |
| test | 12h | +2024 | 88/236 | 88/237 | 1.2839 | 8.0881 |

## Efeito em todos os horizontes de cheia

| Fase | Horizonte | Diferença de acertos | Diferença MAE(m) | Diferença maior erro(m) |
|---|---:|---:|---:|---:|
| validation | 1h | +0 | +0.0007 | -0.0209 |
| validation | 2h | -1 | +0.0047 | +0.1422 |
| validation | 3h | -1 | +0.0178 | +0.0631 |
| validation | 4h | -1 | +0.0597 | +0.1612 |
| validation | 5h | -2 | +0.1173 | +0.4749 |
| validation | 6h | +0 | +0.0342 | +0.0546 |
| validation | 7h | +4 | -0.0716 | -0.3944 |
| validation | 8h | -4 | +0.1323 | +0.3092 |
| validation | 9h | -1 | +0.0182 | +0.2170 |
| validation | 10h | -2 | +0.0593 | +0.0028 |
| validation | 11h | +4 | -0.1676 | -0.4445 |
| validation | 12h | +2 | -0.0312 | -0.4210 |
| test | 1h | +1 | -0.0088 | -0.2745 |
| test | 2h | +3 | -0.0203 | -0.5829 |
| test | 3h | +7 | -0.0152 | -0.2017 |
| test | 4h | +7 | -0.0364 | -0.3801 |
| test | 5h | +4 | -0.0230 | -0.4150 |
| test | 6h | +8 | -0.0575 | -0.3732 |
| test | 7h | +19 | -0.0926 | -1.1602 |
| test | 8h | -14 | +0.0148 | -1.5013 |
| test | 9h | -8 | -0.0025 | -0.2686 |
| test | 10h | +10 | -0.1115 | -0.7071 |
| test | 11h | +18 | -0.1301 | +0.2448 |
| test | 12h | +2 | -0.0569 | +0.1665 |

## Dados e limites

Em12h entram732 pares, dos quais41 com alvo≥7m. A maior resposta no treino passa de8.09m para9.35m. Não há seleção dos exemplos extremos: o mês inteiro elegível foi incluído.

As102.084 linhas de avaliação, os alvos, as bases e a disponibilidade de previsão são idênticos. O novo histórico nunca cruza o hiato2024–2025 no cálculo de alvos. Os últimos h exemplos do arquivo2024 permanecem inelegíveis. Carreiro continua ausente. O arquivo evaluation.csv contém todos os horizontes, recortes e falhas, inclusive linhas sem alvo.

Auditoria:24 modelos reproduzidos exatamente;288 linhas de métricas recalculadas;144 linhas de métricas do controle coincidem com a referência. Máscaras, cortes, parâmetros, contagens por árvore e hashes conferidos.

Não comprova98% prospectivos. Publicação histórica, revisão de fontes, fuso, datum e comparabilidade entre regimes não estão certificados. Mais dados podem ajudar alguns horizontes e piorar outros; não montar uma combinação de versões por horizonte usando este conjunto já visto. O próximo candidato exige protocolo próprio e mantém estes resultados como desenvolvimento.
