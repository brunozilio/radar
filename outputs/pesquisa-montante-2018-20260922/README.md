# Montante nas duas semanas de2018 — disponibilidade ANA

Seis sondagens concluídas, sem novas buscas, retries, treino ou inferência. Todos os GETs retornaram HTTP200: dois com dados de Linha José Júlio e quatro com mensagem explícita `Sem dados` para Santa Tereza/Carreiro. Os arquivos são finais e conservam respostas completas, recibos, todos os campos/QC e índices XML1-based.

| Posto | Janela literal | Registros | NivelFinal aprovado | Cadência / lacunas |
|---|---|---:|---:|---|
| Linha José Júlio86472000 |30/08–05/09/2018|668|668|15min; faltam05/09 15:45,16:00,16:15,16:30|
| Linha José Júlio86472000 |30/09–06/10/2018|672|672|15min; nenhuma lacuna nos672 horários|
| Santa Tereza86472600 |30/08–05/09/2018|0|0|Sem dados no endpoint consultado|
| Santa Tereza86472600 |30/09–06/10/2018|0|0|Sem dados no endpoint consultado|
| Passo Carreiro86500000 |30/08–05/09/2018|0|0|Sem dados no endpoint consultado|
| Passo Carreiro86500000 |30/09–06/10/2018|0|0|Sem dados no endpoint consultado|

Os1340 níveis finais da Linha são finitos, positivos, sem zeros, vazios, QC suspeito ou não avaliado. Nenhuma duplicata/conflito e nenhum registro fora da janela ou grade15min. Cobertura de horas exatas167/168 na primeira semana e168/168 na segunda. O salto de4500s na primeira corresponde às quatro posições ausentes; os demais intervalos são900s. Não houve preenchimento.

Máximos **discretos aprovados recuperados** de NivelFinal:995.00 em`2018-09-03 04:45:00` e1295.00 em`2018-10-03 23:15:00`. São valores brutos, convencionalmente cm conforme os boletins comparáveis, mas o XML não traz atributo explícito de unidade. Não certificam o pico contínuo nem o zero da régua. Não foram convertidos ou normalizados no JSONL.

Há uma ressalva relevante de publicação: o [boletim SGB02/09/2018 17h](https://www.sgb.gov.br/sace/boletins/Taquari/20180902_17-20180902%20-%20174931.pdf), já preservado na pesquisa anterior, indica Linha em manutenção. A resposta ANA obtida agora contém931.00 aprovado em`2018-09-02 17:00:00`. Isso documenta diferença entre publicação contemporânea e acervo recuperado, sem determinar a causa ou demonstrar disponibilidade operacional naquele instante. Em`2018-10-03 22:00:00`, ANA apresenta1282.00 aprovado, igual ao [boletim SGB03/10 22h](https://www.sgb.gov.br/sace/boletins/Taquari/20181003_22-20181004%20-%20092639.pdf). A coincidência não certifica todo o contrato temporal/histórico.

As quatro respostas Sem dados têm1193bytes e identificam explicitamente a estação na mensagem de erro de aplicação. Não são falhas HTTP/rede, tampouco prova de inexistência em todos os acervos ou em outra resolução. `all-qc/` possui dois JSONLs de dados e quatro arquivos vazios vinculados aos recibos e status explícitos; vazios não representam série de zeros. Todos os campos de chuva/vazão/QC retornados foram preservados e contados em `availability.json`, sem interpretação hidráulica.

Fuso/DST, referência vertical e mudanças de régua, publicação histórica, revisões e disponibilidade real na origem continuam não verificados. Timestamps mantêm o texto literal. Não se ajustou atraso, não se consultaram outros postos, não se alterou contrato operacional. Os insumos restantes do Radar não foram avaliados e nenhuma janela ficou automaticamente admissível para treino.

## Suplemento: conferência independente da âncora horária Muçum

A pedido do coordenador, `check_hourly_anchor.py` conferiu diretamente os dois XMLs Muçum anteriores, sem importar o builder, e comparou `outputs/diagnostico-ancora-horaria-2018-20260922/`. **6625 verificações passaram**:336 origens,1680 rastros,3876 linhas de alvos dentro da janela,48 grupos de cobertura,156 exclusões de fronteira, hashes das entradas/artefatos. Não foi refeita qualquer inferência ou ajuste.

| Janela | h | Programados | Alvos aprovados | Pares âncora exataO−1h/alvo | Pares também completos nas derivadas1/2/4/8h |
|---|---:|---:|---:|---:|---:|
|30/08–05/09|1|167|163|160|144|
|30/08–05/09|6|162|158|153|137|
|30/08–05/09|12|156|152|147|131|
|30/09–06/10|1|167|164|160|140|
|30/09–06/10|6|162|159|155|136|
|30/09–06/10|12|156|154|150|130|

Âncora é sempre leitura **exata**O−1h aprovada; derivadas usam somente extremos anteriores à origem. A derivada0,5h permanece ausente em todas as336 origens, sem substituição. Os alvosO+h são exatos e estritamente aprovados; QC não aprovado permanece ausente. Nenhuma busca de endpoint pula dado inválido e nenhuma linha cruza o hiato entre semanas. No recorte alto>=7m, `missing_truth` do CSV é a contagem desconhecida de toda a agenda, separada dos alvos altos observados — não uma classificação desses desconhecidos como cheias. A referência operacionalO−15min/maxage15 segue com zero pares. Um atraso declarado de1h não prova latência real de publicação e seis campos locais não são matriz completa Radar. Cobertura não mede precisão; meta98% não foi avaliada.

## Evidência reproduzível

`plan.json` anterior aos seis GETs registra inventário restrito do cache; as ocorrências adicionais da string2018 nos manifests eram hashes/frações de segundo, sem respostas pertinentes aos três postos. `collect.py` limita-se aos seis recursos e não repete recibos existentes. `raw/*.receipt.json` inclui URL completa, HTTP, headers, início/fim UTC, bytes e SHA256. `source-manifest.json` reúne os recibos; `audit.py` verifica integralmente XML→JSONL e produz25 verificações aprovadas. `prior-evidence-references.json` aponta PDFs e pesquisa anterior porhash, sem modificá-los. `hourly-anchor-independent-check.json` documenta o suplemento. Manifesto próprio e check final preservam todos os arquivos desta pasta; nada foi escrito em fontes anteriores, scripts compartilhados, documentos principais ou operação.
