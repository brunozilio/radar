# Diagnóstico de entradas e pesos: Radar observado com 2023

Os 28 alvos ≥7 m da validação são horas consecutivas de **08/11/2025 08h até 09/11/2025 11h (UTC−3 presumido)**. Reaparecem nos 12 horizontes: 336 linhas de previsão, mas somente 28 alvos distintos. As origens conjuntas vão de 07/11 20h a 09/11 10h. Não atribuí um nome/certificação externa ao episódio.

**Todas as 120 entradas estão finitas nas 336 linhas de validação de cheia.** Em contraste, todas as amostras adicionadas de 2023 têm os 12 campos de Santa Tereza e Carreiro ausentes, em todos os horizontes. Portanto, o prejuízo da validação não é explicado simplesmente por entradas ausentes nessas origens; a distribuição do conjunto adicionado é diferente. Isso não prova causa ou influência particular no modelo.

No horizonte 12h, as 481 amostras novas têm ausência de algum campo em: Muçum 8; Linha José Júlio 0; Q/I de cada usina 12 (3 com os 7 campos ausentes); chuva Baixo Antas 408, Carreiro 404, Prata-Turvo 0, Alto Antas 2, Tainhas 1. Chuva P24 Baixo Antas e Carreiro é ausente em 404/481; as colunas de cobertura continuam finitas, logo chuva ausente não equivale a zero.

| Campo h12 | Validação cheia: mediana / máximo | 2023 admitido: mediana / máximo |
|---|---:|---:|
| julho:Q (m³/s) | 1735.00 / 2600.00 | 717.50 / 2105.00 |
| julho:I (m³/s) | 1710.00 / 2724.00 | 715.00 / 2170.00 |
| monte:Q (m³/s) | 1640.00 / 2525.00 | 698.50 / 2255.00 |
| monte:I (m³/s) | 1646.50 / 2525.00 | 704.50 / 2255.00 |
| castro:Q (m³/s) | 1044.50 / 1890.00 | 382.50 / 1201.00 |
| castro:I (m³/s) | 1103.50 / 2023.00 | 380.50 / 1344.00 |
| Baixo Antas:P24 (mm) | 71.10 / 74.09 | 21.16 / 65.05 |
| Carreiro:P24 (mm) | 64.24 / 68.82 | 28.80 / 69.08 |
| Prata-Turvo:P24 (mm) | 78.34 / 87.94 | 5.66 / 73.85 |
| Alto Antas:P24 (mm) | 53.21 / 62.59 | 3.57 / 53.84 |
| Tainhas:P24 (mm) | 67.65 / 80.43 | 2.26 / 67.99 |

Medianas/máximos usam apenas valores finitos, portanto chuva ausente em grande parte de 2023 torna essa comparação condicional. Os 120 campos completos, cobertura por bloco e diferenças de faixa estão nos CSVs; exceder a faixa das amostras novas não significa exceder o treino original nem um limite físico.

A cobertura P24 mediana Baixo Antas/Carreiro é 0,988/0,948 na validação contra 0,329/0,051 no conjunto adicionado. Os pesos espaciais não foram renormalizados. Q/I são entradas atrasadas dos CSVs ONS; estes números não certificam equivalência de regime operacional, datum ou disponibilidade entre 2023 e 2025.

## Peso efetivamente passado ao ajuste

Fórmula congelada: `1 + 2*(|alvo−base|≥1 m) + 2*(alvo≥9 m)`. A fronteira de cheia descritiva (7 m) não é a mesma fronteira de peso (9 m). Não houve reponderação ad hoc nesta auditoria.

| Fase | h | Linhas 2023 / total | Peso 2023 / total | Fração do peso | Alvos 2023 ≥7 / ≥9 |
|---|---:|---:|---:|---:|---:|
| validation | 1 | 503 / 4865 | 525 / 5171 | 10.153% | 56 / 5 |
| test | 1 | 503 / 11344 | 525 / 11662 | 4.502% | 56 / 5 |
| validation | 6 | 493 / 4847 | 565 / 5899 | 9.578% | 51 / 5 |
| test | 6 | 493 / 11319 | 565 / 13123 | 4.305% | 51 / 5 |
| validation | 12 | 481 / 4829 | 663 / 6667 | 9.945% | 45 / 5 |
| test | 12 | 481 / 11295 | 663 / 14475 | 4.580% | 45 / 5 |

Em h12, dos 663 pontos de peso adicionados, 101 vêm de 45 alvos ≥7 m; apenas cinco alvos são ≥9 m. O restante não representa o pico ausente de setembro de 2023. Cada linha/peso admitido está listado em added-row-weights.csv; não foi preenchido o pico. Soma de pesos mede a contribuição nominal à função de ajuste, não a influência causal de exemplos ou variáveis nas árvores.

## Escopo e integridade

Leitura local das duas matrizes congeladas, máscaras, treino e previsões; nenhum modelo foi carregado ou executado. Foram conferidos hashes publicados dos insumos disponíveis em experiment.json e membership contra training.csv. Ausências preservadas, sem coleta, alteração operacional, treino, HGE ou promoção. Datums, fuso/publicação históricos e regimes físicos permanecem não certificados. Script e manifestos permitem reprodução; fonte de entradas é a matriz congelada, não uma nova auditoria de sensores/XML.
