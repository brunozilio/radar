# Muçum — experimento com código HGE/ARNO

Calculado em 2026-09-21T17:04:34.699484-03:00. Base dos dados: **2026-09-21T17:00:00-03:00**.
Último nível medido: **12.70 m**, em 2026-09-21T16:45:00-03:00.

Foi copiado e executado o `simple_water_balance` do grupo HGE-IPH, commit
`31a6ed4f428c491401e1c96b60457be293564f10`, com licença GPL-3.0 e arquivo original intacto.
**Este é o modelo simplificado ARNO do grupo; não é o MGB-IPH completo.**

## Cálculo e dados disponíveis

- Área incremental: **1273.38 km²**, excluindo as áreas já representadas pelas vazões de 14 de Julho e Passo Carreiro.
- Chuva observada parcial + estimativa meteorológica apenas para a fração sem cobertura.
- Solo, aquífero e três reservatórios em cascata calculados pelo código original; as cascatas representam atraso do escoamento local, não as usinas reais.
- Vazões de montante propagadas pelos pesos já calibrados; vazões futuras reaproveitadas da previsão estatística existente.
- Conversão vazão–nível pela curva local já ajustada, com ancoragem no par observado de vazão e nível em 2026-09-21T16:45:00-03:00.
- Calibração de seis parâmetros efetivos com alvos anteriores a 01/07/2026; aquecimento inicial de 60 dias. Nenhum alvo do evento de hoje foi usado na calibração.

**Evapotranspiração:** Evapotranspiração potencial constante de 1, 3 ou 5 mm/dia em toda a série, sem observações de PET.

**Hipóteses necessárias:** solo inicial a 50% da capacidade; três reservatórios;
correção do erro atual com tempos de 2, 6 ou 12h.
São hipóteses e parâmetros ajustados, não medições físicas da bacia. O valor de referência usa PET=3,
quando não há ET0 disponível, chuva média de GFS/ECMWF/ICON e correção de 6h,
definidos antes de inspecionar o resultado.

## Resultado experimental

| Horário BRT | HGE referência (m) | Previsão anterior (m) | Roteamento anterior (m) | Sensibilidade HGE (m) |
|---|---:|---:|---:|---:|
| 21/09 18h | 14.14 | 13.81 | 13.83 | 14.11–14.17 |
| 21/09 19h | 15.32 | 14.67 | 14.31 | 15.27–15.37 |
| 21/09 20h | 16.51 | 15.01 | 15.48 | 16.46–16.58 |
| 21/09 21h | 17.66 | 15.27 | 16.66 | 17.60–17.76 |
| 21/09 22h | 18.83 | 15.68 | 18.41 | 18.77–18.95 |
| 21/09 23h | 19.97 | 15.40 | 19.57 | 19.90–20.11 |
| 22/09 00h | 21.11 | 17.34 | 20.35 | 21.03–21.25 |
| 22/09 01h | 22.15 | 17.55 | 21.48 | 22.07–22.30 |
| 22/09 02h | 22.98 | 17.84 | 22.39 | 22.90–23.13 |
| 22/09 03h | 23.74 | 17.44 | 23.24 | 23.66–23.89 |
| 22/09 04h | 24.36 | 17.12 | 24.11 | 24.29–24.51 |
| 22/09 05h | 24.92 | 17.58 | 24.96 | 24.86–25.07 |

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

| PET hipotética (mm/dia) | Capacidade do solo (mm) | b | k por reservatório (h) | Saturação na referência | Próximos dos limites de ajuste |
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
Os horários de referência e observação constam acima; a coleta está auditada na pasta da execução.

Foi verificada a identidade do código copiado, a conservação de água (erro máximo
5.68e-14 mm por passo), estoques não negativos e 12 saídas horárias.
Os arquivos de entrada foram preservados e suas assinaturas estão em `resultado.json`.
Ainda falta uma validação de previsões por evento, respeitando a disponibilidade histórica de cada fonte,
para decidir se esse modelo melhora a previsão operacional. Nenhuma alteração em produção.

Fonte do código: https://github.com/HGE-IPH/simple_water_balance
