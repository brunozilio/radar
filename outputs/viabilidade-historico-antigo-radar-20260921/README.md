# Viabilidade de acrescentar cheias antigas ao Radar

**Há trechos com respostas maiores que as vistas no treino atual, mas ainda não há uma matriz equivalente de 204 entradas pronta para treinamento.** Esta auditoria quantifica os trechos; não incorpora dados, não aloca treino/teste e não altera o modelo operacional.

Foram examinadas 49.302 combinações de origem/horizonte em junho–julho/2020, setembro/2023 e março–maio/2024. Para cada origem horária O, a base é o nível aprovado exato em O−15min e o alvo é o nível aprovado exato em O+h. Não houve interpolação, substituição de suspeitos ou preenchimento com níveis antigos. Fuso UTC−3 é assumido. A continuidade do datum permanece pendente.

## Potencial em 12h

| Janela | Origens previstas na janela | Pares base/alvo aprovados | Respostas acima de 8,09 m | Maior resposta alvo−base |
|---|---:|---:|---:|---:|
| Jun–jul/2020 | 1.188 | 1.141 | 9 | 11,53 m |
| Set/2023 | 708 | 480 | 3 | 12,59 m |
| Mar–mai/2024 | 2.196 | 2.195 | 7 | 9,35 m |

8,09 m é o máximo de resposta no treino histórico da fase test do Radar em 12h, tanto no membership completo quanto no ampliado com faltas. A base é atrasada em 15min: essas respostas não são diferenças entre duas medições separadas por exatamente 12h. Comparar respostas reduz a dependência de um deslocamento vertical constante, mas não certifica estabilidade de datum durante o par, geometria, sensor ou regime hidrológico entre anos.

As 19 respostas acima desse máximo têm Q/I e níveis de montante/jusante presentes nas três usinas no instante usado como entrada. Isso é **cobertura parcial de entradas correntes**, não cobertura de todos os seus atrasos/derivadas, estações auxiliares, chuva regional ou meteorologia. A fonte mais recente é escolhida até O−60min, com expiração após 90min adicionais; 23h59 permanece literal. Registros ausentes e zeros originais permanecem distintos.

Na janela 2024, as sete origens são **1º de maio, 04h–10h**, com alvos no mesmo dia entre 16h e 22h. A maior resposta usa base 14,38 m às 07h45 e alvo 23,73 m às 20h. Isso identifica um trecho anterior à avaria reportada para 02/05, sem certificar equivalência de regime com 2026. O apagão posterior não torna automaticamente todos os trechos anteriores inutilizáveis; também não permite reconstruir seus dados faltantes.

## Qualidade e cobertura continuam explícitas

- 2020: valores suspeitos e lacunas de nível continuam excluídos dos pares aprovados. Os zeros suspeitos das vazões ONS no pico não foram corrigidos. O teste limitado de defluência zero com componentes positivos não sinalizou as origens dos 19 pares extremos; isso não valida todas as vazões nem seus antecedentes.
- 2023: falta nível aprovado no pico de Muçum. Os três pares extremos são da subida anterior à interrupção. A marca retrospectiva SGB não foi inserida como alvo horário.
- 2024: o arquivo ANA tem níveis aprovados, mas isso não resolve a diferença documentada entre pico de sensor e marca manual, nem a continuidade de referência. As usinas têm falhas longas durante a cheia e mudanças operacionais documentadas.
- Os acervos já foram inspecionados; nenhum passou a ser um holdout novo ou cego. Todos continuam como dados de pesquisa até a montagem e revisão dos insumos.

## Meteorologia: 2024 é a prioridade compatível com o produto atual

O agente verificou seis consultas pequenas ao produto exato `precipitation_previous_day1`, para um ponto Baixo Antas e os três modelos do Radar. Em 30/06 e 07/07/2020 e 04/09/2023, cada modelo retornou 24 valores nulos apesar de HTTP200. Em 15/03, 30/04 e 02/05/2024, cada modelo retornou 24 valores finitos em mm e UTC−3. Isso não certifica meses completos ou os outros quatro pontos.

A [documentação Previous Runs](https://open-meteo.com/en/docs/previous-runs-api) situa o arquivo geral a partir de janeiro/2024; a extensão GFS anterior refere-se a temperatura. Historical Forecast, hindcasts e reanálise não foram usados como substitutos de previsões futuras arquivadas. Detalhes, respostas completas, URLs e hashes estão em `../pesquisa-cobertura-meteorologica-antiga-20260921/`. O horário histórico de publicação de cada valor continua não comprovado.

## Próximo lote delimitado

Priorizar a montagem de entradas para **origens de abril/2024 até 1º de maio**, com margens anteriores para janelas de chuva/variação e todos os tempos-alvo encerrados antes de 02/05. A delimitação separa uma mudança operacional documentada; não é seleção posterior pelos erros do Radar nesse lote, que ainda não foi inferido.

Reutilizar Muçum e ONS de maio já preservados; obter as outras três séries de nível, estações regionais de chuva, ONS de março/abril para aquecimento e meteorologia dos cinco pontos/modelos exatos. Auditar a matriz completa, QC, referências, intervalos, revisões e ausências antes de desenhar um experimento de acréscimo. Não preencher NWP ausente com chuva observada/reanálise. Um eventual ensaio permanece histórico e condicional às referências; promoção exige a validação independente prevista na meta.

## Verificação e artefatos

13.518 níveis aprovados de 2020/2024 foram reconstruídos dos cinco XMLs com hashes conferidos e comparados exatamente aos CSVs usados. Quatro artefatos derivados ONS/ANA de 2020/2023/2024 conferem com seus manifestos originais. `source-verification.json` registra essa checagem. `audit.json` registra hashes e limites da análise; `summary.csv` inclui todos os 12 horizontes; `potential-pairs.csv` mantém inclusive origens sem base/alvo; `reservoir-source-trace.csv` registra 49.536 seleções de campos com arquivo/linha/idade.

Reprodução offline: `python3 outputs/viabilidade-historico-antigo-radar-20260921/audit.py`.

**Nenhum treinamento ou promoção foi realizado. Os dados adicionais ainda não demonstram os 98%.**
