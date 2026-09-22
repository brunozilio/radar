# Muçum — execução experimental

Referência comum: **2026-09-21T17:00:00-03:00**, America/Sao_Paulo. Emissão: 2026-09-21T17:04:35.229567-03:00.
Última observação coletada: **12.70 m em 2026-09-21T16:45:00-03:00**.
Assimilação limitada à referência: 12.70 m em 2026-09-21T16:45:00-03:00.

Radar: família `arvores_previsao_chuva` selecionada na validação histórica original; hiperparâmetros e treinamento anteriores a 21/09 preservados. Reprodução dos 12 resultados originais verificada antes da inferência.
HGE: **modelo simplificado da equipe HGE-IPH (ARNO), não MGB-IPH completo**. Parâmetros originais reutilizados, sem otimização; estados recalculados com observações novas. Candidato ET0 não promovido.

| Horário BRT | Radar (m) | HGE (m) | Sensibilidade HGE (m) |
|---|---:|---:|---:|
| 21/09 18h | 13.81 | 14.14 | 14.11–14.17 |
| 21/09 19h | 14.67 | 15.32 | 15.27–15.37 |
| 21/09 20h | 15.01 | 16.51 | 16.46–16.58 |
| 21/09 21h | 15.27 | 17.66 | 17.60–17.76 |
| 21/09 22h | 15.68 | 18.83 | 18.77–18.95 |
| 21/09 23h | 15.40 | 19.97 | 19.90–20.11 |
| 22/09 00h | 17.34 | 21.11 | 21.03–21.25 |
| 22/09 01h | 17.55 | 22.15 | 22.07–22.30 |
| 22/09 02h | 17.84 | 22.98 | 22.90–23.13 |
| 22/09 03h | 17.44 | 23.74 | 23.66–23.89 |
| 22/09 04h | 17.12 | 24.36 | 24.29–24.51 |
| 22/09 05h | 17.58 | 24.92 | 24.86–25.07 |

Divergência máxima entre métodos: **7.34 m**. Máximos da janela: Radar 17.84 m em 2026-09-22T02:00:00-03:00; HGE 24.92 m em 2026-09-22T05:00:00-03:00. Não são confirmação de pico da cheia.

Comparação anterior: `outputs/mucum-hge-experimental-2026-09-21/resultado.json`. Diferenças para horários coincidentes estão em `mudancas.csv`; não se comparam deslocamentos de horizontes como se fossem o mesmo alvo.

## Conferência de previsões já salvas
- forecast_m em 2026-09-21T16:00:00-03:00: previsto 10.35 m, medido 11.64 m; erro -1.29 m. saved forecast comparison; historical imports lack independent prospective receipt.
- hge_reference_m em 2026-09-21T16:00:00-03:00: previsto 10.74 m, medido 11.64 m; erro -0.90 m. saved forecast comparison; historical imports lack independent prospective receipt.
Reconstruções históricas não foram contadas como validação prospectiva; importações anteriores não têm recibo prospectivo independente.

## Dados e limites

Coleta bruta e horários de observação, coleta e emissão disponível constam no manifesto. **Os endpoints meteorológicos não informaram emissão/ciclo: coleta nova não comprova ciclo novo.** Não substituí emissão por horário de coleta.
Há 8 avisos de fontes antigas/incompletas, detalhados em `source-issues.json`. Chuva SIGMA serve de conferência; ANA mantém pesos calibrados. Cobertura incremental e chuva parcialmente completada estão em `hge/chuva-estados-recentes.csv`.
Chuva incremental exclui áreas já representadas pelas vazões de montante. Vazões futuras são **estimadas**, não observadas. PET 1/3/5 mm/dia é hipótese. Faixa HGE é sensibilidade, **não intervalo de confiança**.
Conservação de água: erro máximo 5.68e-14 mm/passo; 12 saídas finitas, estoques não negativos e identidade do código HGE verificados. Roteamento auxiliar usa os pesos fixos compartilhados com HGE; o roteamento anteriormente emitido foi preservado em `roteamento-anterior-emitido.csv`.

Motivos de aviso: First hourly run; compared with initial saved forecasts; Common-target change >=0.5 m; Methods divergence crossed 1 m or changed >=0.5 m; radar_m: maximum within forecast window shifts >=2h; hge_reference_m: maximum within forecast window shifts >=2h; New incomplete or stale auxiliary sources recorded.
