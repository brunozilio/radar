# Integração e limites desta execução

Resultado emitido em 21/09/2026 às 17:04:35 BRT, referência comum 17h e 12 alvos de 18h a 05h. Não houve publicação ou envio externo.

## Achado que requer atenção

A divergência máxima Radar–HGE é 7,339 m. Radar: máximo na janela de 17,835 m às 02h. HGE: 24,922 m às 05h, ainda crescente no último horizonte, sem confirmação de pico.

A previsão de defluência de 14 de Julho alcança 14.079,62 m³/s. O máximo observado na série histórica disponível em `dados-roteamento.npz` do snapshot de referência é 9.452 m³/s. Portanto, há extrapolação relevante do preditor de vazão a montante. A estreita sensibilidade de PET/chuva/correção HGE NÃO cobre essa incerteza; o cenário alto não deve ser interpretado como prognóstico comprovado. Não houve truncamento ou ajuste de parâmetros para aproximar os métodos.

## Contribuições implementadas

- `scripts/hydro_hourly_models.py`: reconstrói as instâncias Radar usando exclusivamente telemetria e chuva do snapshot original, cutoff e hiperparâmetros originais; exige reprodução de cada um dos 12 valores originalmente publicados, erro observado zero. Só depois aplica os novos preditores. As instâncias são salvas em `frozen-radar-models.pkl`.
- HGE `run.py`: opções `--parameters` e `--weather-dir`; reutiliza exatamente os três conjuntos originais de parâmetros, sem executar otimização. Atualiza estados e forçantes e mantém arquivo upstream intacto.
- `scripts/hydro_hourly_run.py`: tabela/JSON/gráfico comuns, comparação por horário-alvo, manifesto público com horários e hashes, distinção entre medição e estimativa, conferência exata das previsões anteriores e critérios de aviso.
- Coleta: 27 ANA, 100 SIGMA, três CERAN e três modelos meteorológicos. Seis timeouts ANA recuperados com tentativa anterior preservada. Oito fontes auxiliares com atraso superior a 90 minutos; nenhuma foi apresentada como nova medição. SIGMA é conferência, sem assimilação de pesos novos.

## Provas e limitações

- 12 resultados Radar reproduzidos com erro máximo 0 m; 12 previsões novas finitas e alinhadas.
- Parâmetros HGE idênticos aos originais; seis testes físicos HGE e seis testes de integração da chuva passaram.
- Erro máximo de conservação HGE: 5,68e-14 mm por passo. Isso verifica consistência numérica, não acurácia da cheia.
- Última ANA coletada: 12,70 m às 16h45. Em 16h, observação 11,64 m versus Radar original 10,354 m e HGE original 10,743 m. São comparações de previsões salvas; os arquivos antigos não têm recibo prospectivo independente.
- Emissão/ciclo meteorológico não fornecido pelos endpoints. Horário de coleta não foi convertido em emissão. Chuva futura vem de consultas novas, porém o treinamento original usava previsões do dia anterior: mudança de disponibilidade da entrada precisa de avaliação prospectiva.
- Forçante meteorológica foi consultada nas coordenadas de grade do arquivo histórico GFS nesta execução. O coletor passou a usar os centroides originais da consulta arquivada para execuções futuras; não se atribui retroativamente essa alteração aos dados brutos já coletados.
- Roteamento auxiliar recalculado usa os pesos fixos HGE. O roteamento legado emitido anteriormente é preservado separadamente; não se atribui o novo diagnóstico à instância recalibrada daquele programa.
- O pickle Radar é salvo, mas este runner ainda o reconstrói a partir da base congelada em uma execução nova. Antes de usar este runner alternativo por mais de sete dias, integrar histórico cumulativo/estados anteriores para evitar lacuna entre o snapshot original e a janela móvel da coleta ANA.

## Coordenação

A tarefa principal “Avaliar modelo MGB-IPH” informou que integrou `scripts/hydro_hourly_forecast.py` à automação, com recibos no ledger e saída em `outputs/mucum-hourly-20260921T165608-0300`. O presente runner permanece como contribuição alternativa para unificação; não foi ligado a outra automação. A coleta das 17h já havia terminado quando chegou a coordenação; não será iniciada outra coleta nesta execução. Os arquivos compartilhados e resultados da tarefa principal foram preservados.

Os resultados das 16h da outra implementação têm referência e procedimento de treinamento diferentes. Diferenças entre eles e esta execução não devem ser atribuídas exclusivamente a novas observações. A comparação principal em `mudancas.csv` usa a referência original com o mesmo treinamento congelado.

## Emissão e antecedência real

Emissão local registrada: **2026-09-21T17:04:35.229567-03:00**. Referência: **2026-09-21T17:00:00-03:00**. Primeiro alvo, 18h: antecedência real **0:55:24.770433**. Último alvo, 05h de 22/09: antecedência real **11:55:24.770433**. São 12 horizontes nominais em relação à referência; esta emissão não comprova 12h reais de antecedência. Os timestamps são locais, sem recibo externo independente neste runner alternativo.
