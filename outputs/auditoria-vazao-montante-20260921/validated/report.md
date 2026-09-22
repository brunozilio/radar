# Auditoria da vazão de montante

Nenhuma referência ou emissão foi substituída. Esta comparação usa períodos de desenvolvimento já examinados; não comprova ganho independente nem 98%.

| Fonte | Prazo | Ridge atual | Mistura candidata | Máximo histórico treino | Ganho |
|---|---:|---:|---:|---:|---:|
| julho | 0h | 6217.6 | 5698.4 | 9452.0 | 0.50 |
| julho | 5h | 11891.7 | 11891.7 | 9452.0 | 1.00 |
| julho | 11h | 14022.4 | 9600.9 | 9452.0 | 0.50 |
| carreiro | 0h | 796.8 | 802.5 | 1681.7 | 0.75 |
| carreiro | 5h | 1430.8 | 1430.8 | 1681.7 | 1.00 |
| carreiro | 11h | 1545.1 | 1545.1 | 1681.7 | 1.00 |

Vazões em m³/s. A mistura reduz somente a mudança prevista em relação à vazão conhecida; não impõe limite físico ao rio. Ganho escolhido antes do período de avaliação. Previsões futuras candidatas são diagnósticos locais, não novas emissões.

Os arquivos de contribuições mostram cada parcela linear, incluindo indicadores de ausência. Faixas HGE de PET/chuva não abrangem a incerteza dessas vazões estimadas.

## Resultado da tentativa

A mistura candidata não foi promovida. Em14deJulho, no prazo11h e recorte de vazões altas, o erro médio aumentou de729,88 para984,95m³/s (+34,9%;271origens correlacionadas, não271eventos independentes). No conjunto dos12prazos, esse erro aumentou de437,99 para488,04m³/s. Reduzir o valor futuro por parecer excessivo não mostrou ganho neste período.

O modelo original foi reproduzido com erro numérico máximo inferior a1e-5m³/s. As maiores parcelas positivas no prazo11h vêm de Castro Alves: inclinação6h da afluência (+3.068,81m³/s), salto1h da defluência (+2.479,17m³/s) e nível da afluência (+2.158,50m³/s). São contribuições estatísticas com compensações negativas, não volumes de água independentes nem causalidade demonstrada. O salto de afluência foi2.099,10m³/s em1h, contra máximo de693m³/s no treino.

O runner horário agora salva upstream-extrapolation.json e registra no pacote HGE a extrapolação de entradas e saídas. Não limita artificialmente a vazão, não transforma a sensibilidade PET/chuva em intervalo de confiança e não remove previsões sinalizadas da avaliação.
