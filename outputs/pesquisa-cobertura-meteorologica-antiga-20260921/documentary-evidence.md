# Evidência documental pública

Consulta web em 22/09/2026 UTC (noite de 21/09 em UTC−3). Extrações da ferramenta web, não respostas HTML brutas. O horário interno exato da requisição web não é exposto. Respostas da API têm horários UTC próprios em source-manifest.json.

## Previous Runs

URL: https://open-meteo.com/en/docs/previous-runs-api

Trecho curto, seção Data Availability: “Most models are archived from January 2024.”

Paráfrase da seção: alguns modelos começam mais tarde. A exceção GFS anterior a 2024 se refere especificamente à temperatura a 2 m, desde março de 2021; não estende automaticamente precipitação. A documentação menciona reconstrução adicional sob demanda sujeita ao arquivo do provedor, sem garantir disponibilidade. Nenhuma solicitação a terceiros foi enviada.

Contrato: previous_day1 é lead nominal de 24 horas relativo ao tempo válido. A resposta não identifica a rodada nem a publicação de cada valor. Acumulados podem combinar rodadas. O endpoint é diferente do produto histórico contínuo das primeiras horas das rodadas.

## Historical Forecast

URL: https://open-meteo.com/en/docs/historical-forecast-api

Trecho curto, tabela de fontes: “IFS 0.25°” / “2024-02-03”.

Paráfrase: o produto concatena horas iniciais das rodadas em série contínua, sem preservar uma previsão de 24 horas para cada tempo válido. A tabela informa GFS desde 23/03/2021, ICON global desde 24/11/2022 e IFS 0,25° desde 03/02/2024. O IFS 0,4° listado desde 2022 é outro produto. Estes inícios não comprovam cobertura do campo previous_day1 nem equivalência de vintage. O texto também descreve resoluções temporais nativas diferentes; saída horária não implica modelo nativamente horário.

## Single Runs

URL: https://open-meteo.com/en/docs/single-runs-api

Trecho curto, seção de arquivo: “IFS Cycle 49R1 hindcasts”.

Paráfrase: maioria dos modelos tem arquivo individual desde 02/04/2026. ECMWF IFS HRES 9 km tem exceção desde 14/03/2024, explicitamente com hindcasts 49R1; muda para 50R1 em 12/05/2026 às 06 UTC. Isto não comprova o vintage operacional de ecmwf_ifs025 em 2024. O parâmetro run identifica inicialização UTC, não disponibilidade pública; a documentação cita demora típica adicional de 4–6 horas para modelos globais.

## Acervo anterior consultado

- outputs/pesquisa-contrato-chuva-prevista-20260921/README.md
- outputs/pesquisa-contrato-chuva-prevista-20260921/source-manifest.json
- outputs/pesquisa-contrato-chuva-prevista-20260921/local-input-audit.json
- outputs/pesquisa-contrato-chuva-prevista-20260921/sources/open-meteo-web-extract.txt

O acervo anterior já explica disponibilidade presumida e diferença entre live e lead fixo. Arquivos Radar inspecionados nessa auditoria anterior cobrem abril/2025–setembro/2026. Busca de nomes de arquivos meteorológicos associados a 2020/2023/2024 não encontrou coleta equivalente anterior nesta revisão limitada; isso não é inventário semântico exaustivo de todo o workspace.
