# Insumos meteorológicos Radar — 29/03 a 02/05/2024

Lote de pesquisa separado, coletado em 22/09/2026 às 01h12 UTC (21/09 às 22h12 UTC−3). Foram feitas exatamente três requisições públicas, uma por modelo com as cinco coordenadas originais. Nenhum treino, inferência hidrológica, alteração operacional ou execução HGE foi realizado.

**Resultado: 12.600 valores horários finitos, nenhum null, negativo ou horário duplicado; 44.640 janelas completas.**

| Modelo explícito | Localizações | Horários por localização | Finitos | Janelas completas/total |
|---|---:|---:|---:|---:|
| gfs_seamless | 5 | 840 | 4.200 | 14.880/14.880 |
| ecmwf_ifs025 | 5 | 840 | 4.200 | 14.880/14.880 |
| icon_global | 5 | 840 | 4.200 | 14.880/14.880 |

Parâmetros: endpoint público previous-runs-api.open-meteo.com/v1/forecast; hourly=precipitation_previous_day1; start_date=2024-03-29; end_date=2024-05-02; timezone=America/Sao_Paulo; models explícito. Todas as respostas são HTTP200, com precipitação em mm e utc_offset_seconds=−10800. A série de cada localização coincide exatamente com 29/03/2024 00h até 02/05/2024 23h, resolução de saída horária.

Coordenadas e ordem dos grupos foram extraídas de outputs/mucum-propagacao-2026-09-21/raw/chuva-prevista-query.json, preservadas em coordinate-provenance.json com hash. Somente as coordenadas e nomes foram reaproveitados: a URL original daquele arquivo refere-se a outro produto ensemble, não à consulta deste lote. Não foi utilizado best_match.

## Grades retornadas

| Grupo | GFS latitude,longitude | ECMWF latitude,longitude | ICON latitude,longitude |
|---|---|---|---|
| Baixo Antas | −29.11161, −51.5625 | −29.0, −51.5 | −29.125, −51.625 |
| Carreiro | −28.643013, −51.796875 | −28.5, −51.75 | −28.625, −51.75 |
| Prata-Turvo | −28.525864, −51.328125 | −28.5, −51.25 | −28.5, −51.375 |
| Alto Antas | −28.877312, −50.742188 | −29.0, −50.75 | −28.875, −50.75 |
| Tainhas | −29.11161, −50.390625 | −29.0, −50.5 | −29.125, −50.375 |

Os 15 pares de coordenadas retornadas são idênticos aos registrados no inventário local dos insumos de abril/2025–setembro/2026, conforme grid-comparison.json. Isso não demonstra versão de modelo, interpolação ou vintage invariantes. São amostras pontuais dos centroides, não precipitação média espacial das sub-bacias.

## Janelas auditadas

744 origens horárias, de 01/04/2024 00h até 01/05/2024 23h, com fuso UTC−3. Para cada origem O e janela W=3,6,9,12h, foram verificados exatamente os W timestamps O+1,...,O+W, excluindo O. As 44.640 combinações modelo/localização/origem/janela têm todos os valores finitos. O último tempo necessário é 02/05 às11h, dentro da margem coletada.

window-coverage.jsonl contém contagens e soma em mm para cada combinação; são derivados de auditoria, não entradas já incorporadas ao treino. Ausências seriam mantidas como indisponibilidade, sem interpolação ou troca de produto. coverage-audit.json preserva mínimos/máximos, contagens, unidades, verificação dos hashes e metadados de cada localização.

## Limite de interpretação temporal

O [Previous Runs](https://open-meteo.com/en/docs/previous-runs-api) usa lead nominal24h relativo ao tempo válido. Para valores O+1..O+12, a referência nominal está em O−23..O−12h. As respostas não informam rodada, versão operacional ou publicação por valor; generationtime_ms é duração de processamento da consulta. Portanto, este lote permite desenvolvimento retrospectivo sob disponibilidade histórica presumida, não certificação de previsão emitida naquela época.

Não substituir por Historical Forecast, reanálise ou hindcast. A diferença de distribuição entre lead fixo histórico e rodadas mais recentes usadas ao vivo permanece. Documentação e distinções foram preservadas em outputs/pesquisa-cobertura-meteorologica-antiga-20260921; nenhum critério de elegibilidade ou promoção foi alterado.

## Integridade e reprodução

- raw/*.json: respostas completas e respectivos *.source.json com URL, parâmetros, headers, timestamps UTC, bytes e SHA256.
- collect.py: três requisições limitadas; sidecar existente impede repetição automática, inclusive após interrupção.
- audit.py: auditoria somente local, sem chamadas de rede ou ajuste de modelos.
- coordinate-provenance.json: identidade das cinco coordenadas solicitadas e hash da origem.
- grid-comparison.json: comparação contra inventário anterior, com hash desse documento.
- artifact-hashes.json: hashes de todos os demais artefatos deste diretório.

SHA256 das respostas:

- GFS: 01f0b358aa59e71a4491c6f4bc19d097d59fa8a0f5274da9a3ecf7e6829dd405
- ECMWF: 6d6e729be177aa3bc121076d1bd31f1505b519474731cba7859a530490c69c49
- ICON: 123c322e2ee53d2e7dcc42a73503a68894a40cd63145c9e975988c076f7882aa
