# Auditoria independente — acréscimo de junho/2024 ao Radar

**4.206 verificações passaram, sem divergência encontrada.** Os24 modelos candidatos e24 controles congelados foram reaplicados com duas threads:48 reaplicações e todas as previsões finitas reproduzidas **exatamente**, sem tolerância numérica. As288 métricas foram recalculadas diretamente dos registros; inteiros coincidem exatamente e valores decimais foram conferidos com tolerância1e−12. Nenhum ajuste, coleta ou alteração de fonte foi feito.

## Integridade, máscaras e cronologia

Foram verificados40 hashes de artefatos e36 de entradas no início e no final, além dos4 artefatos do manifesto pré-fit. Fonte executada e protocolo coincidem com os revisados antes do ajuste. O horário do registro de revisão antecede o manifesto pré-fit; datas de modificação dos modelos são posteriores ao manifesto. Essa ordem é corroborada pelo código que salva os vetores antes de fit; timestamps locais não equivalem a certificação externa independente.

As36 máscaras pré-fit/finais são idênticas e foram reconstruídas sem importar os helpers do experimento. Os72 vetores de resposta, alvo e peso coincidem exatamente com a reconstrução;24 planos conferem com as contagens, somas de pesos e cortes. Os24 conjuntos de parâmetros dos candidatos coincidem com os respectivos controles, inclusive todos os parâmetros retornados porget_params e120 variáveis de entrada.

Junho acrescenta167/162/156 pares em1/6/12h e126 alvos≥7m emcada horizonte. O target foi deslocado separadamente dentro de junho e do histórico recente; não há ponte para2025, repetição deorigem ou alvos extras após21/06. Os blocos recentes preservam os cortes01/10/2025 e01/07/2026 e suas mesmas exclusões de fronteira. Pesos mantêm `1+2*(abs(target-base)>=1)+2*(target>=9)`. Nenhuma máscara usa o resultado do candidato ou exige auxiliares completos.

As120colunas recentes,base,truth,times ecomplete24 foram novamente comparadas à referência original:1.549.440 células idênticas, incluindo NaNs. A matriz nova foi lida como artefato selado; esta auditoria não refez sua integração dechuva nem mudou os pequenos efeitos de ponto flutuante já documentados na preparação.

## Cobertura e denominadores

As102084 linhas conservam exatamente chaves,alvos,bases ehorários da referência. A disponibilidade deprevisão é igual nas duas famílias. Inferência usa base disponível independentemente de haver alvo conhecido.

`denominator-partition.csv` separa72 grupos fase×horizonte×população em três categorias disjuntas: alvo desconhecido, observado<7m e observado≥7m. No full_schedule há **34 alvos desconhecidos por horizonte na validação e23 no teste**. São ocorrências por horizonte, não uma contagem deeventos independentes. Desconhecido não é abaixo7, acerto ou erro.

No recorte alto, validação mantém28 alvos/28 pares; teste mantém237 alvos/236 pares/**1 falha de previsão** por horizonte. A falha continua no denominador de alvos observados. Os registros com alvos desconhecidos também não são convertidos em acerto. Completo24/ausente24 permanecem apenas populações diagnósticas.

## Resultado conferido, sem promoção

| Fase | Horizonte | Acertos controle→junho | MAE controle→junho(m) | Máximo controle→junho(m) |
|---|---:|---:|---:|---:|
|validation|1|28→28/28|0.066681→0.066222|0.253657→0.265657|
|validation|6|24→25/28|0.258712→0.318992|1.096290→1.887676|
|validation|12|7→11/28|0.908493→0.842143|2.619470→2.693398|
|test|1|230→231/237|0.077472→0.067352|1.284834→1.061054|
|test|6|149→157/237|0.599275→0.564239|5.717301→5.165169|
|test|12|83→89/237|1.361813→1.225579|7.589997→7.502781|

validation: acertos melhoram em2, empatam em3 e pioram em7 horizontes; MAE melhora em3/12.

test: acertos melhoram em12, empatam em0 e pioram em0 horizontes; MAE melhora em12/12.

O ganho no teste e as regressões na validação são ambos preservados, sem selecionar modelo por horizonte. Os períodos já foram inspecionados e constituem desenvolvimento; não são evidência prospectiva nem novo holdout. Nenhuma precisão mínima98% foi demonstrada e nenhum modelo foi promovido.

## Limites da prova

Joblib permite conferir configuração,árvores e inferência, mas não demonstra isoladamente cada peso consumido pelo otimizador. A evidência sobre membership/respostas/pesos combina fonte executada, manifesto pré-fit e vetores salvos; não houve novo fit para fingir prova independente. Metadados de fuso/publicação/datum e o regime pós-avarias demaio continuam não certificados. Valores ONS e seus conflitos foram preservados como definidos, não corrigidos pela auditoria.

`audit.py` executa somente leitura e reaplicação de modelos já salvos, com `threadpool_limits(limits=2)`, sem importar coletores/roteamento. O nome histórico do ambientePython não representa execução deHGE: somente Radar foi usado. `replay.csv`, `metrics-independent.csv`, `membership.csv`, `denominator-partition.csv` e `flood-contrasts.csv` conservam resultados completos. `verification.json` detalha os checks; `input-hashes.json` e o manifesto próprio permitem reproduzir/verificar esta pasta. Acervos e código raiz permanecem intocados.
