# Níveis dos reservatórios como preditores de vazão

Comparação local pré-especificada com os mesmos alvos, parâmetros e cortes temporais. Níveis e variações foram acrescentados aos53preditores originais. Não houve conversão para armazenamento, ajuste de volume, máscaras de anomalias ou promoção. A disponibilidade histórica dos níveis usa atraso presumido60min e expiração90min; publicações/revisões passadas não estão verificadas.

| Fonte | Família | Validação geral | Validação vazões altas | Desenvolvimento posterior geral | Desenvolvimento posterior vazões altas |
|---|---|---:|---:|---:|---:|
| julho | reference | 81.98 | 285.24 | 169.23 | 437.99 |
| julho | level_and_slopes | 70.50 | 266.58 | 142.36 | 396.03 |
| julho | slopes_only | 69.77 | 271.51 | 144.39 | 406.49 |
| carreiro | reference | 13.53 | 77.69 | 29.68 | 78.21 |
| carreiro | level_and_slopes | 12.88 | 79.18 | 29.49 | 77.33 |
| carreiro | slopes_only | 13.69 | 78.91 | 30.40 | 78.08 |

Valores são MAE em m³/s, ponderados pelo número de pares de cada horizonte. Não são erros em metros do nível de Muçum. Vazões altas usam percentil95da fonte antes da validação, não a cota analítica7m de Muçum.

Em14deJulho, nível+variações melhora o erro de vazões altas em todas as12antecedências nominais testadas, de0a11h. A média cai285,24→266,58m³/s na validação e437,99→396,03no desenvolvimento posterior. Em11h, o erro ainda é601,77m³/s na validação e687,95no período posterior. Esse ganho não demonstra precisão suficiente do nível final, nem resolve sozinho extrapolações futuras.

Carreiro piora no recorte de vazões altas da validação com ambos os grupos adicionais. Seu uso não é justificado por esta comparação, mesmo que uma pontuação agregada beneficie erros de níveis baixos.

A auditoria separada encontrou nível jusante de14deJulho168,74m em03/05/2025 às14h, entre68,74e68,75m. Esse valor foi mantido, inclusive sua propagação nas variações e no treinamento. Está documentado em outputs/auditoria-niveis-reservatorios-ceran/. Não se limpou a série após observar resultados favoráveis.

Verificação: 197206 pares idênticos por família; referência anterior reproduzida em contagens/MAE/viés/P90 com diferença máxima0.00e+00; todos os hashes de entrada conferidos. Foram preservados144modelos de fase/antecedência/fonte/família, entradas adicionais, rastreio de horários e previsões pareadas.

Os períodos de2025–2026 já foram inspecionados em estudos anteriores e continuam sendo desenvolvimento. Próximo passo: avaliar a propagação do candidato até Muçum e sua robustez por eventos, sem reutilizar o evento de avaliação no ajuste. Os modelos horários permanecem intactos; meta98%não comprovada.
