# Verificação independente das matrizes observadas2018

**17553 verificações passaram**, reconstruindo40.320 células(2×168×120) diretamente das séries ANA ALL-QC e dos CSVs ONS literais selados, sem importar builders/helpers operacionais. Níveis eQ/I coincidem exatamente; máscarasNaN idênticas. Integração de chuva por soma geométrica independente de intervalos encerrados: maior diferença absoluta2,842170943040401e−14, dentro da tolerância de comparação2e−10 previamente usada para esta reconstrução.

| Origens da janela | Células | NaN | Bases Muçum finitas | Truth exato/aprovado |
|---|---:|---:|---:|---:|
|30/08–05/09/2018|20160|7257|164|164|
|30/09–06/10/2018|20160|6913|165|165|

Foram conferidos também os arrays de15min, ordem/catálogo120colunas,240 contagens de cobertura porcoluna,60 grupos de cobertura da chuva,24 resumos de alvos,1344 rastros de nível,6048 consultas deQ/I e os hashes de preparação. Muçum consulta **exata**O−1h(maxage0) comQC explícito aprovado; dH0,5 permaneceNaN. Linha usa30min/maxage15; Santa15min eCarreiro30min permanecem ausentes. A seleção conserva o último registro mesmo inválido, sem pular para observação anterior válida.

ONS preserva o atraso60min/expiração90min apósconsulta, timestamps literais e todos os valores de fonte. As consultas foram conferidas contra os CSVs e seus índices de origem, incluindo flags diagnósticas; flags não modificaram entradas. Q/I brutos não foram cortados nem substituídos por componentes. A transformação existente `max(Q/1000,0)^0,6` é apenas o campo derivado especificado.

Alvos são exatos, aprovados e dentro da própria semana. Os últimos h de cada janela são excluídos porfronteira, sem criar ponte sobre o hiato. Falta de truth/base permanece separada; nenhuma faltaauxiliar impôs filtro adicional. O aquecimento de3dias fornece níveis anteriores ao primeiro horário central; porisso as contagens podem superar o diagnóstico anterior restrito aos XMLs centrais. `independent-target-coverage.csv` traz todos os denominadores recomputados.

## Chuva e cobertura

`contract-review.md` preserva a avaliação prévia. Incrementos só entram se finitos,0–150mm, QCexplicitamente aprovado e0<dt<=5400s, mantendo todos os timestamps ao calcular dt. Publicação histórica não foi demonstrada; a regra apenas usa extremos de medição já encerrados sob atraso declarado. Intervalo rejeitado contribui zero ao somatório e zero à cobertura, mantendo PNaN abaixo do limiar0,5, sem atribuir chuva física zero ao posto ausente.

86200900 tem apenas5/8 intervalos admissíveis entre48/59 leituras;42/50 intervalos maiores que90min foram excluídos, sem dividir precipitação em horas. Em86450000,04/10 23:01 foi preservado e cria intervalos60s/3540s corretamente encerrados; nada foi arredondado. Pesos são fixos, sem renormalização, e delays são os27 valores congelados truncados em15min.

Consequência estrutural, sem alterar parâmetros: Prata-Turvo permanece abaixo da cobertura0,5 (máximo0,4989339019189765) eTainhas no máximo0,15846994535519127; suas precipitações ficam ausentes. O limite não foi afrouxado. As75 colunas de chuva/cobertura têm5033/4702NaN nas duas semanas; os arquivos `rain-regional-coverage-independent.csv` e `rain-intervals-by-station.csv` detalham todo o cálculo.

## Evidência e limites

`rain_contract_audit.py` produz a reconstrução pré-matriz; `verify.py` compara todas as entradas e rastros sem importar funções operacionais. `reconstructed-*.npz` são somente artefatos de auditoria e não substituem a matriz original. `verification.json` contém os17553 checks e hashes das fontes usadas. Manifesto próprio/check final sela esta pasta; fontes, protocolos e matrizes do coordenador não foram alterados.

A diferença numérica pequena na chuva não é prova de invariância de futuras árvores: nenhuma inferência foi executada, e um limiar pode ser sensível à representação. Os hashes do acervo ALL-QC, antes auditado integralmente XML↔JSONL, foram novamente conferidos; nesta etapa não houve nova decodificação dos XMLs. ONS usa CSVs literais previamente auditados mais os hashes dos CSVs brutos, sem repetir sua decodificação.

UTC−3 é hipótese computacional explícita para compatibilidade dos arrays, não certificação de fuso/DST,datum,revisionamento ou publicação histórica. A hipótese de âncora1h eQC estrito precisa ser aplicada igualmente a controles contemporâneos e a qualquer candidato futuro. Igualdade da matriz não prova admissibilidade causal plena, capacidade de generalização ou cumprimento da meta98%. Nenhum treino, inferência, rede ou alteração operacional nesta auditoria.
