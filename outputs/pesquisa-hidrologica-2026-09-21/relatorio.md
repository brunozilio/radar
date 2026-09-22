# Pesquisa inicial de dados para previsão de nível em Muçum

Consulta realizada em 21/09/2026. Escopo: leitura do acervo, pesquisa pública e amostras pequenas, mais uma coleta ET0 completa autorizada para experimento local não comercial. Nenhum modelo, produto ou agendamento foi alterado.

## Resultado acionável

A fonte ET0 já está disponível para o primeiro candidato: `et0-era5-2025-04-01--2026-09-20.json`. São 12.912 horas UTC solicitadas, 12.792 valores válidos de 01/04/2025 00h até 15/09/2026 23h; as 120 horas finais são nulas. Hash, URL, coleta, unidades e coordenada estão em `et0-era5-full-manifest.json`. O parâmetro é ET0 de referência estimada pela reanálise ERA5, calculada com FAO56 Penman-Monteith, em mm acumulados na hora precedente, para grama com água ilimitada. Não é evapotranspiração real observada nem previsão meteorológica emitida. A célula retornada foi -29,0/-51,5, aproximadamente0,25 grau, para a solicitação -29,10/-51,61. Não converter ausências em zero. Avaliar separadamente qualquer hipótese usada na cauda. [Documentação](https://open-meteo.com/en/docs/historical-weather-api). Dados CC-BY4.0; API gratuita restrita a uso não comercial. [Termos](https://open-meteo.com/en/terms).

## O que já existe localmente

Os coletores lidos usam SIGMA para estações em julho–setembro 2026 e SACE para janelas recentes. `outputs/mucum-propagacao-2026-09-21/raw/ana-2025-manifest.json` documenta coleta ANA desde 01/04/2025. Na busca por nomes de arquivos, antes desta pesquisa não havia arquivos identificados com 2020,2023 ou 2024. Isso não prova ausência de datas antigas dentro de todos os arquivos. Não executei coletores existentes. O histórico deve preservar estações oficiais como origem; SIGMA é agregador e não constitui licença explícita para redistribuição.

## Cheias antigas: respostas reais e limitações

Foram feitas cinco requisições pequenas ao endpoint ANA `DadosHidrometeorologicosGerais`, já usado no projeto. Todas retornaram HTTP200; o corpo foi validado:

| Estação/data | Linhas | Níveis válidos | Resultado |
|---|---:|---:|---|
| Muçum 86510000,09/07/2020 |96|92|76 aprovados,16 suspeitos,4 ausentes; nível10,93–21,02m |
| Muçum 86510000,05/09/2023 |76|0|Há chuva, nenhum nível; não usar como alvo |
| Muçum 86510000,02/05/2024 |96|96|Todos aprovados; nível23,01–25,57m |
| Antas 86472000,02/05/2024 |96|7|89 níveis ausentes;23,90–24,18m nos existentes |
| Passo Carreiro 86500000,02/05/2024 |0|0|ErrorTable: sem dados; HTTP200 não implica sucesso |

As amostras têm horários de15 min e valores de nível em centímetros no XML; a conversão apresentada acima é cm/100. O fuso não vem anexado a cada timestamp: verificar a convenção oficial antes de unir a UTC. `sample-manifest.json` registra URL e hash; `parsed-samples.json` registra os controles de qualidade. Não interpolar longos apagões no pico nem promover dados suspeitos silenciosamente.

O serviço legado respondeu hoje, porém seu [aviso oficial](https://telemetriaws1.ana.gov.br/Mapa.aspx) anunciava encerramento em 30/06/2026 e base secundária com atraso. A solução durável é a [API ANA documentada](https://www.ana.gov.br/hidrowebservice/swagger-ui/index.html), que possui séries telemétricas adotadas/detalhadas, curvas de descarga, medições e perfis transversais. A API exige acesso; não tentei autenticar nem solicitar cadastro. A interface Hidroweb oferece download público. Não estabeleci licença explícita destes dados nesta busca; preservar atribuição e regras de acesso.

## Usinas e vazões

O [catálogo ONS horário](https://dados.ons.org.br/dataset/dados_hidrologicos_ho) foi acessado via CKAN e salvo em `ons-metadata.json`, com dicionário. Maio 2024 CSV respondeu HTTP206 a um Range de256 KiB: cabeçalho e dados reais salvos em `ons-2024-05-first256k.csv.part`. O arquivo inteiro tem16.031.121bytes; a amostra começa em outras bacias e NÃO comprova ainda a presença das três usinas CERAN. Os Parquets listados de julho 2020,setembro 2023,maio 2024 têm aproximadamente1,14 / 1,20 / 1,28 MB e são o próximo lote preferencial.

Campos incluem afluência, defluência, vazão turbinada/vertida e níveis. ONS usa hora de fim:01h representa00h–00h59. Dados horários são enviados pelos agentes, podem faltar e sofrer revisões; não equivalem à base diária consistida. Licença no catálogo: Creative Commons Atribuição. Guardar versão, data da coleta e checksum. A [tabela CERAN](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHCA.php) oferece dados horários recentes; não identifiquei um histórico público completo nesta busca.

## Chuva, geometria e controle de retrospectivas

- [INMET](https://portal.inmet.gov.br/dadoshistoricos): índice anual de estações automáticas de2000 a 2026; baixar lotes 2020,2023,2024 e filtrar estações da bacia, começando por metadados. Não baixei os ZIPs grandes. Validar falhas e fuso por cabeçalho.
- [Cemaden](https://sws.cemaden.gov.br/): documentação de séries e acumulados; acesso histórico por formulário pode envolver CAPTCHA e email. Não enviei formulário nem contornei acesso. Disponibilidade e licença de cada extração seguem pendentes.
- [NASA IMERG](https://gpm.nasa.gov/data/imerg): chuva espacial0,1 grau / 30 min, útil para eventos antigos e comparação com pluviômetros. Fixar produto/versão. Final é retrospectivo e atrasado, enquanto Early tem latência operacional; não avaliar uma previsão de época usando Final como se já estivesse disponível.
- [SGB, marcas de cheia 2024](https://rigeo.sgb.gov.br/handle/doc/24939.5): relatório revisado várias vezes, com índice apontando versão 19 em 2026. O máximo da telemetria não deve substituir automaticamente a marca de cheia nem vice-versa. Obter versão mais recente, datum da régua, referências de nível, deslocamentos e validade da curva-chave. A curva pode mudar após cheia/erosão. A topologia BHO já presente ajuda na drenagem, mas não substitui seção transversal/batimetria.
- [Open-Meteo Single Runs](https://open-meteo.com/en/docs/single-runs-api): as rodadas individuais preservam inicialização; a documentação descreve o IFS desde março 2024 como hindcasts Cycle 49R1. Verificar a natureza da série antes de chamar de previsão realmente emitida. Para operação, inicialização não é disponibilidade pública: aplicar latência. Historical Forecast concatena primeiras horas de várias rodadas e não reproduz por si só um horizonte de12 h emitido no passado.

## Próximo lote e critérios

1. Usar ET0 já entregue em um candidato local, mantendo as séries de avaliação e os critérios congelados.
2. Expandir alvos/estações para as janelas 2020-06-01a 2020-07-20,2023-08-01a 2023-09-20,2023-10-01a 2023-11-30,2024-03-01a 2024-05-31. Começar por Muçum e medir ausência/QC antes de coletar todos os afluentes. O período inicial serve ao aquecimento do solo.
3. Baixar os três Parquets ONS pequenos, identificar de fato Castro Alves / Monte Claro / 14 de Julho e cruzar horários/afluência/defluência. Depois coletar meses de aquecimento necessários.
4. Recuperar curvas-chave e metadados de referência para os eventos com vazão/nível; geometria ausente fica explicitamente pendente.
5. Separar eventos completos para avaliação; nenhuma seleção de parâmetros pode ver esses alvos. Distinguir reconstrução com chuva/vazão futuras observadas de previsão com entradas conhecidas no instante de emissão. Guardar emissão, disponibilidade, validade, fonte e revisão de cada entrada.

Esta pesquisa encontrou fontes e evidência de disponibilidade; não demonstrou melhoria do modelo nem98% de acerto. O alvo de precisão deve fixar erro tolerado em metros, horizonte, eventos, número de amostras e tratamento de indisponibilidade. Acerto global em períodos calmos não basta para comprovar desempenho em cheias.
