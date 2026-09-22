# Auditoria local — 21/09/2026, 17h43–17h44 BRT

O comando autorizado `scripts/hydro_hourly_forecast.py` terminou com código 0 e suprimiu a repetição: ambas as emissões de referência 17h já estavam no ledger. Não ocorreu nova previsão nem nova coleta completa das quatro fontes neste disparo. O ciclo auditado é `outputs/mucum-hourly-20260921T172707-retry`, com emissões reais Radar 17:31:09.277372 BRT e HGE 17:31:09.338342 BRT. Nenhum horário foi reescrito.

## Integridade e fontes

Lidos run-result.json, run.json, pipeline.log, manifesto, idades-fontes.csv e upstream-extrapolation.json. Os 189 arquivos únicos de fontes/artefatos auditados conferem com os hashes. A coleta original preserva 133 respostas, sem erro final ou retry nesta coleta. Pipeline sem traceback. Isso comprova execução e integridade, não precisão.

Na referência 17h: Muçum e três usinas CERAN tinham dados das 17h; Passo Carreiro, das 16h30. Quatro estações auxiliares tinham atraso superior a 120 minutos: 86060010 540min, 86102000 420min, 86125000 301min e 86200900 300min. Esse limiar é apenas seleção descritiva nesta auditoria; não é uma nova regra de validade. Os atrasos são relativos à origem do cálculo e não ao instante desta auditoria. Nenhum desses dados foi apresentado como medição nova.

O índice cumulativo continua apontando para o snapshot history do ciclo auditado. Não houve retorno ao histórico estático nem repetição da migração meteorológica.

## Observação e verificação novas

capture_ana coletou às17:43:45 BRT 166 registros; um instante novo, sem revisão dos valores/qualidades previamente recebidos neste lote. Último dado aprovado pela ANA: 13,22m às17h15, preservado em recibo imutável 6c7aea09b491ebd6893c9171db59f7959bc926d75501c901f614c8f7617b140d. UTC−03 segue hipótese documentalmente incompleta; referência vertical também segue não verificada.

Relatório prospectivo atualizado em outputs/monitoramento-prospectivo/reports/20260921T204345190605Z. Quatro pares são apenas diagnósticos de importações antigas; 74 pontos ainda não venceram. Zero pares elegíveis à meta; não há novo alvo horário vencido verificado. Cada pacote contém as bandas reais 1–12h. O alvo18h tem somente cerca de28min51s e não conta como1h; o alvo06h cobre12h28min51s.

A política de cobertura começa às18h BRT. Nenhuma janela encerrada ou esperada sem início existe ainda no período vigente: percentual nulo, não100%. Permanecem visíveis a falha17:27 e a recuperação iniciada17:29 e concluída17:31, ambas anteriores à vigência. Duas emissões antigas sem vínculo a ciclo permanecem identificadas.

## Diagnóstico de extrapolação — não intervalo de confiança

12 de28 estimativas de vazão ultrapassam o máximo de seu treino; todos os28 modelos apresentam alguma entrada fora de faixa. Em14deJulho, máximo previsto13.485,62m³/s em10h nominais versus máximo de treino9.452m³/s. EmCarreiro, máximo1.748,64m³/s em13h versus1.681,70m³/s. Nenhuma previsão foi excluída ou limitada.

No pico estimado de14deJulho, os maiores termos lineares positivos são deCastroAlves: tendência3h da afluência +2.531,40m³/s, afluência +2.231,76m³/s, tendência6h da afluência +2.040,10m³/s e incremento1h da defluência +1.951,89m³/s. São contribuições da regressão padronizada, correlacionadas e parcialmente compensadas por termos negativos, não decomposição causal ou vazões físicas adicionais. A tendência3h da afluência está56,81 desvios-padrão de treino acima da média usada nesse ajuste. O pacote preserva todos os detalhes originais.

Divergência máxima Radar–HGE 7,911m no alvo07h; ambos seguem experimentais. PET3mm/dia, tau6h e corte21/09/2026 00h BRT preservados. Não houve ajuste, promoção, deploy ou publicação. A pesquisa independente sobreCastroAlves está separada dos insumos de treino.

Pesquisa concluída em `outputs/pesquisa-castro-20260921T204404Z/README.md`: três fontes primárias novas com hashes verificados. Nota CERAN de julho atualiza avanço das obras para mais de80%; licença documenta deplecionamento temporário autorizado de até3m. Não demonstra operação executada, curva vigente ou causa da subida atual. Sem novas séries ou alterações de treino.
