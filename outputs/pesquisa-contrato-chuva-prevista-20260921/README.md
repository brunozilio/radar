# Contrato temporal da chuva prevista — auditoria delimitada

Auditoria em 21/09/2026. Fontes e modelos existentes foram somente lidos. Nenhum modelo, dado de entrada ou critério de promoção foi alterado.

## Conclusão

O uso de precipitation_previous_day1 nos acumulados de origem +1 até +12 horas é **compatível com desenvolvimento retrospectivo sob o contrato documentado**, com disponibilidade histórica presumida. Não foi identificado impedimento documental que, por si só, invalide esse experimento. Isso não certifica uma emissão operacional histórica: faltam identificação da rodada, horário efetivo de publicação e versão do arquivo disponível em cada origem.

Na documentação da [Previous Runs API](https://open-meteo.com/en/docs/previous-runs-api), o deslocamento é relativo ao **tempo válido**: day1 representa previsão nominal de 24 horas antes desse tempo. Não representa uma rodada única fixada 24 horas antes da origem do nosso modelo. Para origem O e alvo T=O+h:

- h=1: referência nominal T−24h = O−23h;
- h=6: O−18h;
- h=12: O−12h.

Logo, o corte nominal fica antes da origem em todos esses horizontes. Trata-se de inferência do contrato de lead fixo; não atribuímos esses horários como inicializações reais de cada registro. Ciclos discretos, composição de modelos e interpolação exigem rastreamento da rodada efetiva. Acumular valores de vários tempos válidos também pode misturar rodadas.

## Unidade e alinhamento

A [Forecast API](https://open-meteo.com/en/docs) define precipitation como soma, em mm, da hora anterior ao timestamp. Assim, somar os valores nos timestamps O+1,...,O+W representa as W horas futuras, excluindo a hora que termina em O. O sufixo day1 não transforma o campo em precipitação acumulada de 24 horas nem em observação.

Os três arquivos têm cinco pontos e 12.960 horários por ponto, de 01/04/2025 00:00 até 22/09/2026 23:00, timezone America/Sao_Paulo e offset −10.800 s. GFS/ECMWF não têm valores ausentes; ICON tem 77 por ponto, de 09/04/2026 22:00 até 13/04/2026 02:00. Inventário, hashes, coordenadas da grade e intervalos estão em local-input-audit.json.

As URLs originais GFS/ECMWF estão nos sidecars preservados: endpoint previous-runs-api.open-meteo.com/v1/forecast, hourly=precipitation_previous_day1, start_date=2025-04-01, end_date=2026-09-22, timezone=America/Sao_Paulo e models específico. Não localizamos sidecar com URL original ICON; sua identidade decorre da configuração e arquivo locais, não de metadado de rodada na resposta.

## Inicialização não é disponibilidade

A [Single Runs API](https://open-meteo.com/en/docs/single-runs-api) identifica rodadas por run em UTC. Esse horário é a inicialização, não a publicação: modelos globais normalmente levam 4–6 horas adicionais. Esse intervalo típico é compatível com a folga nominal mínima de 12 horas acima, mas não garante ausência de atrasos excepcionais, falhas ou publicação tardia.

A mesma página informa arquivo para a maioria dos modelos desde 02/04/2026. O acervo ECMWF HRES 9 km anterior inclui hindcasts do ciclo 49R1, e há mudança para 50R1 em 12/05/2026 06 UTC. Isso não equivale automaticamente ao histórico operacional e à versão ecmwf_ifs025 usada aqui. Não substituímos os arquivos existentes por esse produto.

A documentação de [atualizações dos modelos](https://open-meteo.com/en/docs/model-updates) separa last_run_initialisation_time, last_run_modification_time e last_run_availability_time. Conversão concluída não significa disponibilidade; servidores redundantes podem divergir, com recomendação de margem de 10 minutos. Essa API descreve a última rodada, não fornece neste acervo um ledger histórico de publicação.

## O que o código local faz

Referências lidas: scripts/hydro_hourly_collect.py, hydro_hourly_forecast.py, hydro_hourly_models.py, hydro_hge_dependencies.py e hydro_reservoir_mucum_experiment.py. O coletor ao vivo usa precipitation no endpoint Forecast API; o histórico usa precipitation_previous_day1. Os acumulados históricos consultam timestamps futuros válidos, e não chuva observada futura. Isso é aceitável para uma previsão se a rodada já estava disponível.

As respostas locais não expõem run, issued_at ou publicação por valor. generationtime_ms é tempo de processamento da resposta, não emissão. O source_lead_hours=24 dos sidecars é anotação local, não prova individual de origem.

## Limites para interpretar o experimento novo

1. A disponibilidade anterior à origem é hipótese explícita; não há certificação causal operacional, nem prova de imutabilidade/backfill do acervo.
2. Histórico usa lead nominal de 24 horas; live usa o produto de rodadas mais recentes. A distribuição, idade e composição das previsões diferem.
3. Médias de membros com janela completa são aceitáveis como regra definida previamente, mas a composição varia na lacuna ICON. Registre membros/contagem; não interprete mudança de composição como melhora meteorológica.
4. Nenhum resultado deve servir como avaliação prospectiva, autorização de promoção ou comprovação de assertividade sem o registro real de entradas disponíveis.
5. Para uma futura avaliação certificável, preservar resposta completa por origem, coleta em UTC, hash, modelo/versão, rodada e disponibilidade; quando houver Single Runs, selecionar run com publicação demonstradamente anterior à origem. Não tratar hindcast reconstruído como emissão histórica sem evidência.

## Evidências preservadas

source-manifest.json registra URLs, tentativas HTTP diretas (403) e hash da extração pública obtida pela ferramenta web. sources/open-meteo-web-extract.txt é a extração textual dessa ferramenta, não uma resposta HTML bruta. A data da consulta é conhecida; o horário exato interno da requisição web não é exposto e não foi inventado. timing-contract.json preserva a regra e os 12 horizontes.

A conclusão é documental e sobre os arquivos inspecionados; não revisa independentemente a nova implementação dos 20 atributos informada pelo agente principal.

