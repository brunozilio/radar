# Verificação integral independente — chuva prevista até Muçum

PASSOU: as 72 previsões baseline e as 72 previsões candidatas coincidem com os arquivos preservados dentro de 1e-8 m. Erro máximo de 7,105427357601002e-15 m em ambas as famílias; nenhuma regressão acima da tolerância.

Origens BRT, todas com horizontes 1..12 h: 01/07/2026 00:00; 02/07/2026 21:00; 22/07/2026 08:00, 09:00 e 11:00; 13/08/2026 09:00. Os 72 pares são finitos.

## Método

verify_full.py faz a reconstrução integral, sem inverter níveis salvos e sem atualizar vazão por delta:

- Recria as 53 features originais de montante a partir da telemetria congelada, acrescenta os 24 níveis/inclinações preservados e os 20 atributos de chuva já preservados. Não recalcula nem ajusta os atributos de chuva.
- Executa os modelos Julho77 e Julho97 congelados no experimento de chuva, fase test. Confirma identidade dos modelos Julho77 com o experimento anterior.
- Executa Carreiro53 congelado original e substitui apenas valores ausentes pelos valores de proxy previamente preservados em NPZ. Não ajusta ou recalibra nenhum modelo.
- Reconstrói a chuva média de Baixo Antas diretamente dos três arquivos brutos, reexecuta o HGE desde o estado inicial até a origem menos uma hora e simula separadamente origem..+12 com chuva prevista e PET 3 mm/dia.
- Faz roteamento completo de passado e previsões, ignorando somente pesos exatamente zero; reconstrói a âncora com 0,25 do instante anterior e 0,75 da origem; aplica residual com tau 6 h e offset de nível da âncora exata de 15 minutos.
- Só depois lê os níveis salvos para comparação.

O HGE executado é cópia local do run.py e hydrological_model.py vigentes, com hashes conferidos contra a proveniência preservada onde disponível. A montagem das features, inferência ridge, roteamento, âncora, residual e transformação de nível foi escrita separadamente neste verificador. Nenhum método fit foi chamado.

## Evidência numérica

| Comparação | Erro absoluto máximo |
|---|---:|
| Nível baseline versus proxy/predictions.csv | 7,1054e-15 m |
| Nível candidato versus chuva-ate-mucum/predictions.csv | 7,1054e-15 m |
| Vazão total baseline | 3,6380e-12 m³/s |
| Vazão total candidata | 5,4570e-12 m³/s |
| Resíduo numérico máximo de balanço HGE | 2,8422e-14 mm |

A comparação candidata usa explicitamente julho_levels_rain_m. A baseline usa julho_levels_m do experimento de proxy.

## Reprodução e artefatos

Comando executado:

    PYTHONDONTWRITEBYTECODE=1 /tmp/radar-hge-venv/bin/python outputs/verificacao-integral-chuva-mucum-20260921/verify_full.py --candidate-field julho_levels_rain_m

Para repetir apenas a comparação, acrescente --compare-only; isso não recalcula o HGE.

- verification.json: aprovação, tolerância e hashes dos dois CSVs comparados.
- comparison.csv: 144 comparações individuais.
- recomputed-levels.csv: 72 linhas com níveis, vazões roteadas, escoamento local, residual e offset.
- recomputed-upstream.csv: 72 conjuntos de previsões Julho77/97 e Carreiro usados.
- computation.json: parâmetros, entradas e hashes, conferências de proveniência.
- runtime.json: versões e erros em vazão total.
- code/: cópias do HGE/vendor e script original do experimento de proxy.
- artifact-hashes.json: hashes finais desta entrega.

O primeiro ambiente Python disponível não tinha threadpoolctl; a execução foi realizada no ambiente HGE já existente, sem instalações.

## Limites

Esta verificação cobre seis origens selecionadas e seus 12 horizontes, não todos os 23.538 pares nem ramos com previsão ausente ou vazão total negativa. Ela confirma a equivalência numérica da atualização por delta nesses casos, não qualidade preditiva, disponibilidade histórica comprovada ou promoção operacional. Os atributos de chuva e valores do proxy permanecem os artefatos congelados originais, identificados por hash. Nenhuma fonte, modelo, script compartilhado ou automação foi alterado.

