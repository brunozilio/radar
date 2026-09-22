# Cobertura meteorológica antiga — somente Radar

**Março–maio/2024 tem amostras utilizáveis dos três campos exatos. Junho/julho/2020 e setembro/2023 não têm valores nas consultas delimitadas e estão fora da cobertura de precipitação documentada para Previous Runs.** Não coletamos meses completos nem treinamos modelos.

Foram feitas seis requisições públicas, um dia cada, para o mesmo ponto Baixo Antas usado no Radar (latitude −29.10130785468805, longitude −51.61242071623862), timezone America/Sao_Paulo, hourly=precipitation_previous_day1, modelos explícitos gfs_seamless, ecmwf_ifs025 e icon_global. Cada requisição inclui os três modelos; não utiliza best_match. Valores em mm, offset −10800 s, resolução de saída horária.

| Dia consultado | GFS finitos/24 | ECMWF finitos/24 | ICON finitos/24 |
|---|---:|---:|---:|
| 30/06/2020 | 0 | 0 | 0 |
| 07/07/2020 | 0 | 0 | 0 |
| 04/09/2023 | 0 | 0 | 0 |
| 15/03/2024 | 24 | 24 | 24 |
| 30/04/2024 | 24 | 24 | 24 |
| 02/05/2024 | 24 | 24 | 24 |

Todas as respostas foram HTTP200. Nas três primeiras datas o conteúdo é null, não chuva zero. Nas amostras de 2024 há 216 valores finitos no total; nas antigas há 216 ausentes. Máximos horários em 02/05/2024: GFS 9,0 mm, ECMWF 11,3 mm, ICON 14,2 mm. Não inferir cobertura de meses inteiros, dos cinco pontos ou dos picos apenas desses testes.

## Distinção necessária de produto e vintage

A [Previous Runs API](https://open-meteo.com/en/docs/previous-runs-api) documenta arquivo geral desde janeiro/2024; a extensão GFS até 2021 refere-se a temperatura, não precipitação. Os três dias nulos são coerentes com essa limitação, sem provar inexistência mundial de previsões antigas dos provedores.

O [Historical Forecast](https://open-meteo.com/en/docs/historical-forecast-api) pode oferecer GFS/ICON em 2023, mas concatena primeiras horas de rodadas. Não é substituto dos acumulados futuros de lead fixo24h. Além disso, ecmwf_ifs025 é listado desde03/02/2024; IFS0,4° é modelo diferente. Reanálise pode representar chuva histórica observada/estimada, mas não deve preencher o campo previsto futuro como se já existisse na origem.

A [Single Runs API](https://open-meteo.com/en/docs/single-runs-api) não resolve essas datas para os mesmos três modelos: maioria desde abril/2026; a exceção IFS HRES9km desde março/2024 inclui hindcasts de outro ciclo. Hindcast reconstruído e reanálise precisam de rótulos próprios e não demonstram emissão operacional antiga.

O campo previous_day1 representa previsão nominal24h antes do tempo válido. Para alvos O+1..O+12, a referência nominal precede O em23..12h. Isso favorece desenvolvimento retrospectivo sob disponibilidade presumida, mas as respostas consultadas não contêm run, issued_at, hora de publicação ou versão operacional. A documentação não permite certificar que cada valor disponibilizado hoje estava publicado na origem histórica. Os arquivos também não comprovam imutabilidade nem ausência de reconstrução posterior. A API ao vivo usa rodadas mais recentes, portanto permanece diferença de distribuição.

## Próximo lote concreto, ainda não executado

Priorizar março–maio/2024, três modelos explícitos, cinco coordenadas originais, no mesmo timezone. Coletar por mês com cache e hashes, iniciando/terminando com margens que cubram todos os tempos válidos dos acumulados +12h. Auditar nulls por modelo/ponto/hora e janelas completas antes de definir admissão. Não preencher ausências com ERA5, Historical Forecast ou IFS9km. Este relatório não autoriza treino/promoção nem modifica o pipeline.

Para 2020/2023, registrar insumo indisponível neste produto. Uma investigação posterior de arquivos originais NOAA/DWD/ECMWF exigiria vintage, inicialização, horizonte, variável, grade e disponibilidade documentados; não foi executada nesta rodada e não há promessa de reconstrução equivalente.

## Artefatos

- probe.py: coleta reproduzível restrita às seis requisições; não importar no pipeline.
- responses/: respostas completas, inclusive nulls.
- source-manifest.json: URLs/parâmetros, coleta UTC, headers, hashes, unidades e contagens.
- documentary-evidence.md: fontes oficiais, trechos curtos e distinção entre evidência e interpretação.
- artifact-hashes.json: integridade dos artefatos; prior-input-hashes.json identifica o acervo reaproveitado.

Nenhum script compartilhado, modelo, dado prévio ou critério de elegibilidade foi alterado. Nenhuma execução HGE ou ajuste de modelo ocorreu.
