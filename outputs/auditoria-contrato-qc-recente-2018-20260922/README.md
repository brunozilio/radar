# Proveniência/QC recente para comparação experimental com2018

**Resultado: não houve mudança de valores ao exigir QC explícito aprovado e última ocorrência literal neste acervo congelado.** Isso foi verificado, não presumido. A semântica potencialmente problemática do cache continua documentada abaixo; aqui ela não gerou divergência observada para NivelFinal/ChuvaFinal.

Foram lidos86 XMLs dos27postos na precedência2025→principal→latest→fresh do snapshot15h. Os54 arrays de nível/chuva dos caches normalizados foram reproduzidos exatamente, sem chamar load_ana, merged ou prepare_current e sem escrever nos caches. Os quatro níveis raw/delayed do telemetria-latencia e truthMuçum do features.npz foram reproduzidos exatamente. 537775 timestamps porposto, somados, foram preservados; não são amostras horárias independentes.

- Zero valores finitos aceitos exclusivamente porQCausente nos XMLs pertinentes.
- Zero eventos de revisão invalidante pulada após um valor anterior finito, nos dois campos auditados e na precedência histórica observada.
- Zero divergências entre legado eQCestrito com mesmaregra finite-only.
- Zero divergências entre legado eQCestrito/último-registro, nos valores finais dentro da grade2025/26; zero mudanças em truthMuçum e nos horários exatos dos quatro níveis.

As120colunas observadas da matrizcongelada também foram reconstruídas manualmente a partir do snapshot:1551360 células, bases/truth/tempos exatos. A auditoria anterior de chuva, que reproduziu60campos×51709posições exatamente, foi vinculada aos hashes de todos os seus insumos não-código ainda idênticos. Não foi refeita a integração regional nesta etapa; o trabalho novo é a reconstrução integral das observações eQC dos XMLs e sua equivalência aos caches/fresh.

## Duas regras distintas, preservadas para auditoria

`load_ana` aceita valor numérico finito/não negativo comQC Dado aprovado **ou ausente**, e só sobrescreve o campo histórico se o novo valor for finito. Assim uma revisão inválida poderia manter valor antigo. Em seguida, `merged` atualiza cada timestamp fresh substituindo todos os campos, inclusiveNaN. Não se deve generalizar a ausência de diferença encontrada para outras fontes ou snapshots.

O novo artefato experimental usaQC estrito e **cada última ocorrência substitui o campo anterior, inclusiveNaN**, na ordem2025.xml→principal.xml→latest.xml→fresh. Ocorrências duplicadas dentro deum XML seguem ordem documental; isso é uma regra explícita deprecedência, não demonstra cronologia de revisão do provedor. `lineage/` conserva as três variantes:legado,QCestrito comfinite-only eQCestrito/latest. Valores foram auditados antes/depois do corte01/07/2026, sem usar erro deprevisões.

## Arquivos prontos para reconstrução experimental

`strict-latest/ana-COD.npz` contém `times`, `level`(m), `rain`(mm), máscaras `_finite` e `_qc_approved`, textos `_qc`, identificadores `_source_id` e `_source_record_index`. Há27 arquivos, com todos os timestamps, inclusive valores inválidos comoNaN. Não pule timestamps inválidos ao selecionar níveis nem ao calcular dt da chuva. OQC pode estar aprovado mas o valor falhar porausência/faixa; porisso máscaraQC e finitude são separadas.

`source-index.json` mapeia source_id para caminhoXML, hash, papel/precedência e número de registros. Índices de registro são1-based. `lineage/ana-COD.npz` permite reproduzir quem forneceu cada valor de cada variante. `source-qc-counts.csv` lista contagens porarquivo/campo/QC; arquivos de divergências/revisões vazios representam contagemzero, não erro de leitura. As fontes originais continuam emseus diretórios, intactas e referenciadas porhash.

`mucum-hourly-exact-60min.npz` fornece somente a preparação de âncora experimental exataO−1h e truthMuçum estrito exato sobre12928origens da grade congelada, de01/04/2025 até21/09/2026 15h. Possui12851bases finitas; a base congeladaO−15min tinha12844. A diferença é alteração da idade/seleção da âncora, **não mudança deQC ou correção de nível**. Não contém previsões, modelos ou métricas deerro.

| Nível | Timestamps da série | Valores de nível finitos | Atraso congelado reproduzido |
|---|---:|---:|---:|
|86472000|51607|51271|30min|
|86472600|50143|49966|15min|
|86500000|49743|48427|30min|
|86510000|51564|51372|15min|

As fontes deQ/I e as60colunas NWP não foram reavaliadas nesta tarefa. Q/I do snapshot foi usado somente na reconstrução das120colunas; o objetivo é comparação observada semNWP. Nenhuma inferência, ajuste ou mutação operacional foi realizada.

Oparser usaUTC−3 como convenção computacional e nívelcm→m como contrato congelado; oXML não certifica porisso fuso/DST,datum, vigência, publicação histórica ou qualidade física. O relatório mostra fidelidade ao snapshot e regras explícitas, não certificação hidrológica ou independência. A base antiga permanece preservada. Uma futura comparação deve aplicar a âncora60min eQCestrito igualmente acontrole/candidato, com todos os alvos e falhas mantidos, sob protocolo separado.

Auditoria principal:237 checks passaram; suplemento120colunas exato, vínculo de56 insumos da auditoria dechuva. Todos os arquivos são experimentais, sem promoção nem alegação de98%. Manifesto final/check preserva esta pasta.
