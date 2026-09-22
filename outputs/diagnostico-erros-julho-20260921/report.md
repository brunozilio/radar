# Origem das maiores oscilações históricas

A decomposição reproduziu as vazões congeladas do candidato para os três maiores erros absolutos de nível em 12 h nas cheias. Não houve ajuste nem mudança de previsão. As contribuições abaixo são parcelas matemáticas do modelo estatístico; não são vazões físicas atribuídas a cada usina.

| Origem em 22/07/2026 BRT | Erro do nível em 12 h | Parcela das variáveis Monte Claro | Vazão de Julho propagada prevista | Comparação com vazão futura observada propagada |
|---|---:|---:|---:|---:|
| 09:00 | -9.038 m | -5821.3 m³/s | 1959.1 m³/s | 8211.9 m³/s |
| 08:00 | -9.026 m | -5455.5 m³/s | 2104.8 m³/s | 8419.7 m³/s |
| 11:00 | +8.454 m | +5780.7 m³/s | 13690.7 m³/s | 7616.7 m³/s |

O arquivo ONS preservado registra Monte Claro com vazão defluente de 9.907 m³/s às 06h, zero às 07h–09h e novamente 9.907 m³/s às 10h. A afluente também aparece zerada às 07h–08h. Esses registros já haviam sido apontados na auditoria de qualidade; agora foi quantificado seu efeito no erro do nível, através das diferenças de 1, 3 e 6 horas.

Nas origens de 08h–09h, as parcelas das variáveis Monte Claro retiram cerca de 5,5–5,8 mil m³/s da previsão propagada. Às 11h, adicionam cerca de 5,8 mil m³/s. Isso explica matematicamente boa parte da oscilação do preditor de vazão de Julho; não comprova qual seria o nível correto após consertar a entrada, nem autoriza preencher o dado bruto.

O contexto bruto está preservado com números de linha em `monte-claro-source-context.csv`. O valor zero continua intacto na fonte. A comparação com a vazão futura observada é exclusivamente retrospectiva para diagnóstico: não se trata de entrada disponível na emissão nem de uma nova previsão válida.

Próximo teste justificável: um tratamento causal e geral de entradas inconsistentes, validado antes deste episódio e avaliado no conjunto completo. O experimento anterior que marcou este evento específico não pode ser usado como prova independente. Evitar corrigir somente estes três erros ou contar a seleção por erro como ganho de modelo.

Os erros de nível originais permanecem no placar. Nenhum modelo foi promovido e a meta de 98% não foi atingida.
