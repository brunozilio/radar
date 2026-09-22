# Chuva em milímetros e tempo de resposta em Muçum

Análise de observações até 21/09/2026, 15h BRT. Não é nova previsão do nível.

## Sequência observada hoje

A chuva média espacial estimada no Baixo Antas foi 24,1 mm entre 06h e 07h; 35,8 mm entre 07h e 08h; 24,0 mm entre 08h e 09h. Muçum estava em 3,95 m às 07h, 4,17 m às 08h, 4,93 m às 09h, 5,82 m às 10h e 9,69 m às 15h. Há uma resposta já observável durante e após a chuva; a diferença de 2h entre o final do pulso de 07–08h e a leitura das 10h não é o tempo de viagem de toda essa água. A subida tem contribuições simultâneas de outros trechos e chuva anterior. O evento ainda não tem pico completo.

## Defasagens exploratórias no histórico

Foi comparada a chuva acumulada em 3h com a taxa de subida de Muçum em 3h, deslocando a chuva de 0 a 48h para trás. Dados medidos em seus horários reais, sem aplicar atrasos de transmissão do modelo de previsão. Chuva regional: pesos espaciais existentes sobre 27 séries ANA e integração dos intervalos de medição, sem repetir incrementos; exigência de 85% de cobertura ponderada, com normalização pela fração coberta. Os cinco agregados usam vizinhos além da fronteira regional quando são os mais próximos. Guaporé usa somente a chuva da estação Linha Colombo, não a chuva média de toda sua bacia.

Foram selecionados 10 eventos de nível de Muçum ≥7m, proeminência ≥1,5m, distância entre picos ≥96h, com cobertura de nível ≥85% na janela. Para cada evento, o alinhamento compara a janela de 24h antes a 12h depois do pico do rio. Exige 28 pares horários e algum pulso de pelo menos 10mm/3h; o resumo de dispersão inclui apenas eventos com correlação ≥0,35. Esses filtros e a maximização da correlação favorecem associações: as faixas não são probabilidades de chegada nem intervalos de confiança.

| Região | Maior correlação histórica no atraso | Correlação | P10–P90 dos atrasos em eventos selecionados | Eventos selecionados/avaliados |
|---|---:|---:|---:|---:|
| Baixo Antas | 12h | 0.30 | 7,0–25,1h | 8/9 |
| Carreiro | 12h | 0.29 | 7,6–15,4h | 7/8 |
| Prata-Turvo | 10h | 0.27 | 6,0–11,6h | 3/5 |
| Alto Antas | 11h | 0.13 | 5,2–26,6h | 7/9 |
| Tainhas | 9h | 0.28 | 4,8–14,4h | 9/10 |
| Guaporé: Linha Colombo | 11h | 0.20 | 4,0–28,0h | 6/6 |

**As correlações globais são fracas (0,13–0,30). Não há sustentação para converter essa tabela em tempo físico de chegada por sub-bacia.** Chuvas simultâneas entre regiões, armazenamento, operação dos reservatórios e contribuições sobrepostas impedem isolar a causa. Exemplo: o atraso de Linha Colombo muda de 18h no primeiro período histórico para 11h no segundo; não representa duração de remanso. Horas consecutivas são dependentes, não amostras independentes.

Alto Antas e Tainhas têm lacunas de cobertura após 08h no recorte atual. As lacunas aparecem em cinza e não foram convertidas em chuva zero. Os acumulados das regiões com lacunas não devem ser comparados como totais completos do dia.

## Onda já no rio: outra medida

A análise anterior alinhou ondas inteiras nas réguas/usinas com a resposta em Muçum. Estes tempos começam no sinal do rio naquele ponto, não na chuva sobre o solo:

| Ponto a montante | Mediana observada | P10–P90 dos eventos | Eventos |
|---|---:|---:|---:|
| Linha José Júlio | 3,0h | 2,0–3,0h | 9 |
| Santa Tereza | 1,5h | 1,0–2,0h | 8 |
| 14 de Julho | 4,0h | 1,8–5,0h | 9 |
| Passo Carreiro | 8,5h | 5,0–17,5h | 6 |

A estimativa do Carreiro é particularmente fraca pela mistura de contribuições. Não aplicar esses tempos diretamente a todo pluviômetro de uma sub-bacia. A água de uma chuva se distribui no tempo por infiltração, escoamento nas encostas, canais, armazenamento e remanso; a mesma quantidade de mm pode produzir respostas diferentes em solo seco ou saturado.

## Arquivos

- `chuva-resposta-exemplo-hoje.png`: comparação principal com valores e horários.
- `chuva-versus-mucum-hoje.png`: seis painéis, incluindo Linha Colombo.
- `atrasos-chuva-mucum.png`: correlação para todos os atrasos de 0–48h.
- `chuva-hoje-hora-a-hora.csv`: chuva por região e nível observado, sem preenchimento de lacunas.
- `atrasos-por-evento.csv`, `correlacoes-por-atraso.csv`: resultados auditáveis.
- `raw/manifest-guapore.json`: coleta adicional da ANA para Linha Colombo desde abril/2025.

As séries ANA históricas vêm da coleta anterior em `../mucum-propagacao-2026-09-21/raw/`; atualizações das 27 estações foram copiadas da coleta das 15h13, com Muçum atualizado pela consulta das 15h24. A estação Linha Colombo foi consultada nesta análise, com respostas e horários preservados. Nenhuma alteração em produção.

Referências: [ANA — telemetria](https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx); [USGS — chuva e escoamento](https://www.usgs.gov/water-science-school/science/runoff-surface-and-overland-water-runoff); [HEC-HMS — transformação chuva–vazão](https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/transform/unit-hydrograph-basic-concepts). O atraso hidrológico até o pico do escoamento, definido a partir da chuva excedente, não é a mesma grandeza que a defasagem de correlação exploratória apresentada aqui.
