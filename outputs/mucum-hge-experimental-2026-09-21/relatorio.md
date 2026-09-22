# Muçum — experimento com código HGE/ARNO

Calculado em 2026-09-21T15:48:43.286163-03:00. Base dos dados: **21/09/2026 às 15h BRT**.
Último nível medido: **9.23 m**, às 14h45.

Foi copiado e executado o `simple_water_balance` do grupo HGE-IPH, commit
`31a6ed4f428c491401e1c96b60457be293564f10`, com licença GPL-3.0 e arquivo original intacto.
**Este é o modelo simplificado ARNO do grupo; não é o MGB-IPH completo.**

## Cálculo e dados disponíveis

- Área incremental: **1273.38 km²**, excluindo as áreas já representadas pelas vazões de 14 de Julho e Passo Carreiro.
- Chuva observada parcial + estimativa meteorológica apenas para a fração sem cobertura.
- Solo, aquífero e três reservatórios em cascata calculados pelo código original; as cascatas representam atraso do escoamento local, não as usinas reais.
- Vazões de montante propagadas pelos pesos já calibrados; vazões futuras reaproveitadas da previsão estatística existente.
- Conversão vazão–nível pela curva local já ajustada, com ancoragem no par observado de vazão e nível das 14h45.
- Calibração de seis parâmetros efetivos com alvos anteriores a 01/07/2026; aquecimento inicial de 60 dias. Nenhum alvo do evento de hoje foi usado na calibração.

**Hipóteses necessárias:** evapotranspiração potencial constante de 1, 3 ou 5 mm/dia;
solo inicial a 50% da capacidade; três reservatórios; correção do erro atual com tempos de 2, 6 ou 12h.
São hipóteses e parâmetros ajustados, não medições físicas da bacia. O valor de referência usa PET=3,
chuva média de GFS/ECMWF/ICON e correção de 6h, definidos antes de inspecionar o resultado.

## Resultado experimental

| Horário BRT | HGE referência (m) | Previsão anterior (m) | Roteamento anterior (m) | Sensibilidade HGE (m) |
|---|---:|---:|---:|---:|
| 21/09 16h | 10.74 | 10.35 | 10.68 | 10.63–11.09 |
| 21/09 17h | 11.92 | 11.21 | 12.19 | 11.75–12.37 |
| 21/09 18h | 13.08 | 11.50 | 13.33 | 12.87–13.55 |
| 21/09 19h | 14.12 | 11.65 | 14.30 | 13.87–14.58 |
| 21/09 20h | 14.97 | 12.40 | 14.81 | 14.70–15.41 |
| 21/09 21h | 15.68 | 12.10 | 15.52 | 15.39–16.09 |
| 21/09 22h | 16.24 | 13.45 | 16.27 | 15.93–16.61 |
| 21/09 23h | 16.73 | 13.63 | 16.61 | 16.41–17.07 |
| 22/09 00h | 17.16 | 14.16 | 16.87 | 16.83–17.47 |
| 22/09 01h | 17.48 | 13.98 | 17.07 | 17.15–17.75 |
| 22/09 02h | 17.67 | 13.80 | 17.07 | 17.35–17.92 |
| 22/09 03h | 17.89 | 13.74 | 17.04 | 17.57–18.11 |

A amplitude é apenas a sensibilidade às hipóteses testadas. **Não é intervalo de confiança,
limite máximo de cheia ou confirmação de pico.** A referência não foi escolhida por desempenho
em previsões independentes. Os cenários dependem das mesmas vazões futuras estimadas a montante.

## Verificação histórica disponível

Teste de **reconstrução** entre 01/07 e 20/09/2026, com chuva e vazões de montante observadas.
Os dois métodos usam exatamente os mesmos horários e a mesma curva vazão–nível.
Esses erros **não medem precisão de previsão com 12h de antecedência**.
O período já foi examinado em análises anteriores do projeto: não é uma nova avaliação cega.

| Modelo | Recorte | Horas | Erro absoluto médio (m) |
|---|---|---:|---:|
| hge_pet_1 | all | 1506 | 0.407 |
| hge_pet_1 | level_ge_7m | 167 | 0.905 |
| hge_pet_3 | all | 1506 | 0.411 |
| hge_pet_3 | level_ge_7m | 167 | 0.888 |
| hge_pet_5 | all | 1506 | 0.415 |
| hge_pet_5 | level_ge_7m | 167 | 0.877 |
| existing_linear_routing | all | 1506 | 0.426 |
| existing_linear_routing | level_ge_7m | 167 | 0.849 |

No cenário de referência, o erro geral mudou de **0.426 para 0.411 m**,
mas acima de 7 m mudou de **0.849 para 0.888 m**. Nesta comparação,
o novo componente não demonstrou melhora para cheias. Não há base para substituir
a previsão atual por ele. A proximidade ao roteamento anterior não é confirmação
independente: os dois reutilizam as mesmas estimativas de vazões futuras a montante.

## Parâmetros e sensibilidade

| PET hipotética (mm/dia) | Capacidade do solo (mm) | b | k por reservatório (h) | Saturação simulada às 15h | Próximos dos limites de ajuste |
|---|---:|---:|---:|---:|---|
| 1 | 41.0 | 0.010 | 5.36 | 98.9% | b, kbas, Ws |
| 3 | 39.3 | 0.010 | 5.35 | 98.6% | b, kbas, Ws |
| 5 | 36.4 | 0.037 | 5.36 | 98.3% | kbas, Ws |

Os parâmetros completos, a convergência do otimizador e as condições de contorno estão em
`parametros.json`. Ajuste junto aos limites e diferenças entre hipóteses são sinais de identificação
limitada. A saturação é estado do modelo, não um sensor de umidade.

## Limites e verificações

Não há geometria de canal, remanso, planícies de inundação, discretização completa em minibacias/URHs
nem evapotranspiração observada. A chuva prevista representa um ponto do Baixo Antas, não toda a área.
O cálculo usa o conjunto salvo das 15h, sem atualização de telemetria.

Foi verificada a identidade do código copiado, a conservação de água (erro máximo
5.68e-14 mm por passo), estoques não negativos e 12 saídas horárias.
Os arquivos de entrada foram preservados e suas assinaturas estão em `resultado.json`.
Ainda falta uma validação de previsões por evento, respeitando a disponibilidade histórica de cada fonte,
para decidir se esse modelo melhora a previsão operacional. Nenhuma alteração em produção.

Fonte do código: https://github.com/HGE-IPH/simple_water_balance
