# Efeito dos níveis dos reservatórios na previsão de Muçum

O candidato troca somente a previsão de vazão de14deJulho. Carreiro, parâmetros HGE/ARNO, chuva, roteamento, curva de nível e correção residual são comuns. Não houve ajuste neste experimento nem alteração das emissões horárias.

## Resultado comparável

| Prazo nominal | Recorte | Pares | Cobertura¹ | MAE referência → candidato (m) | Acertos±0,50m referência → candidato |
|---|---|---:|---:|---:|---:|
| 1h | Geral | 1598 | 82.2% | 0.140 → 0.142 | 97.5% → 97.3% |
| 1h | Nível≥7m | 165 | 69.6% | 0.258 → 0.257 | 90.9% → 89.7% |
| 6h | Geral | 1582 | 81.6% | 0.370 → 0.385 | 76.9% → 73.5% |
| 6h | Nível≥7m | 171 | 72.2% | 0.980 → 0.950 | 35.1% → 31.0% |
| 12h | Geral | 1570 | 81.2% | 0.700 → 0.590 | 49.2% → 59.2% |
| 12h | Nível≥7m | 183 | 77.2% | 1.746 → 1.663 | 14.8% → 18.0% |

¹Cobertura entre alvos observados: os erros/acertos usam apenas pares calculáveis de ambos os modelos. Falhas e alvos sem medição permanecem registrados. Esses prazos são nominais de hindcast, não antecedências reais de emissões prospectivas.

Em12h, o ganho aparece no nível final, mas a taxa de acerto nas cheias continua18,0%, com MAE1,663m. Em6h, o erro geral e a taxa de acerto pioram; mesmo a pequena redução deMAEnas cheias vem acompanhada de menor taxa dentro de±0,50m. Não se selecionou um horizonte favorável para declarar melhoria global.

## Cobertura e causalidade do cálculo

Foram examinadas1968origens e23538alvos nominais anteriores a21/09. Estados: missing_or_invalid_forecast_input=4122, paired=18981, missing_exact_target=147, missing_exact_anchor=288.

As vazões são inferidas em todas as origens, sem exigir observação futura de vazão. Os modelos congelados pré-julho reproduziram os valores da avaliação anterior; dados ausentes no alvo deMuçum são registrados, não interpolados. Cada âncora exige H/Q exatos em origem−15min. Estado de chuva observada termina em origem−1h; origem e futuro usam previsões meteorológicas arquivadas, nunca chuva futura observada. Os dois modelos recebem a mesma correção inicial.

A inferência usa os valores históricos finais disponíveis no acervo. Os atrasos de15min/60min e a disponibilidade dos arquivos previous_day1 não foram comprovados por recibos históricos. A comparação é de desenvolvimento, com períodos já examinados, e não demonstra o desempenho prospectivo do runner atual nem certifica dados históricos. A âncora é uma hipótese fixa, não observação de latência passada.

## Decisão

Não promover. O ganho de vazão não se traduz em ganho uniforme do nível. Manter o candidato para investigar erros por fase da cheia, lacunas e sensibilidade às anomalias documentadas, sem ajustar diretamente nos eventos usados para medir desempenho. A meta98%permanece não atingida; zero exemplos prospectivos ou cheias independentes foram adicionados ao placar por este experimento.

Preservados protocolo, código, hashes e todos os pares. Erro máximo na reprodução das vazões congeladas: 0.00e+00m³/s. Erro numérico máximo do balanço: 4.26e-14mm. Esses controles verificam implementação, não precisão hidrológica. Não foi produzido intervalo de confiança a partir dos pares sobrepostos.
