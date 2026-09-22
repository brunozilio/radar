# Auditoria independente — Radar119 com/sem2018

**1602 verificações passaram.** Os48 modelos salvos reproduzem exatamente as previsões nas102084 linhas agendadas, com projeção fixa119 e base correta. As288 métricas foram recalculadas diretamente das previsões e reconciliadas, mantendo alvos desconhecidos, falhas e subpopulações. Nenhumrefit ou acesso àrede foi executado; inferência limitada aos48joblibs já existentes, comthreadpool2.

Confirmados hashes dos artefatos/fontes, pré-fit e projeção;48máscaras,144vetores(48respostas+48pesos+48targets) e48planos idênticos aos da tentativa120preservada. Os conjuntos de treino foram reconstruídos das matrizes: índices, ordem cronológica sem duplicações, respostas, pesos e datas-alvo estritamente anteriores aos cortes. Target é deslocado separadamente em cada janela2018 e na série recente; nenhuma ponte entre janelas/anos. As linhas recentes aparecem intactas ao final do candidato aumentado.

Configurações dos48modelos conferem os hiperparâmetros congelados,119entradas e180iterações, iguais entre famílias. Apenas oíndiceoriginal1(Muçum dH0,5h), estruturalmente ausente, foi retirado. `complete_upstream18` mantém originais6:24, equivalentes às projetadas5:23; a subpopulação não depende da coluna removida. A matrizfonte120permanece intacta.

As mesmas origens/targets/bases/populações são usadas porambas asfamílias. Previsões são reaplicadas onde abase éfinita, inclusive quando truthfalta; alvos ausentes não filtram emissão nem se convertem emacertos. Na métrica alta>=7m, a contagem `missing_truth` continua referente àagenda da população, não éclassificação de valores desconhecidos como cheias. Falhas comtarget observado permanecem no denominador observado.

## Resultado conferido, sem promoção

Cheias, agenda completa: validação tem28alvos/28pares emcada horizonte; teste tem237alvos/236pares e1falha. A comparação usa novos controles comâncoraMuçum1h, não reprodução dos antigos modelos operacionais.

| Recorte | h | Acertoscontrole→+2018 | MAEcontrole→+2018(m) | Máximoabscontrole→+2018(m) |
|---|---:|---|---|---|
|Validação alta|1|27→28/28|0,111758→0,107853|0,549548→0,498729|
|Validação alta|6|21→20/28|0,369183→0,369223|2,173732→1,921356|
|Validação alta|12|9→8/28|0,850095→1,001721|2,437757→2,259779|
|Teste alto|1|228→228/237|0,130020→0,131165|2,288854→2,241640|
|Teste alto|6|151→156/237|0,657329→0,619989|6,285061→5,873246|
|Teste alto|12|79→75/237|1,419848→1,366877|8,059888→7,174799|

No teste alto, acertos melhoram em8horizontes, empatam em1 e pioram em3; MAEmelhora em9/12. Na validaçãoalta, acertos melhoram em4, empatam em3 e pioram em5; MAEmelhora em4/12. Oganho deMAE12h não vira ganho deacertos12h. Resultado misto: não há domínio consistente ou base para promover/selecionar família porhorizonte. Acerto pontual28/28 emvalidação1h não demonstra meta98%prospectiva.

## Artefatos e limites da prova

`audit.py` reproduz a conferência; `training-reconstruction.csv` conserva hashes dos inputs119/respostas/pesos porfit; `membership.csv` contém os24conjuntos recentes e acréscimos; `inference-replay.csv` registra48aplicações exatas e faltas de base/truth; `independent-metrics.csv` traz288métricas e `contrasts.csv`144comparações. `input-hashes.json` e `verification.json` vinculam asfontes, e manifesto/check final sela esta pasta.

Umjoblib deHGB não prova isoladamente todas asamostras, respostas ou pesos consumidos pelo otimizador durantefit. A evidência aqui combina código executado/hash, máscaras/vetores pré-fit, reconstrução independente deconjuntos e previsões reproduzidas, semrefit. Os horários registrados localmente mostram ordenação pré-fit→conclusão, mas não constituem prova externa autenticada dessa cronologia.

Avaliação recente já é desenvolvimento inspecionado. As janelas2018 foram selecionadas porpesquisa/documentação e preparadas sob contrato explícito, mas isso não certifica datum/fuso, regime hidráulico, revisões, disponibilidade operacional passada ou independência estatística. Nenhum dado operacional, fonte, modelo ou experimento do coordenador foi alterado. Meta98% não alcançada por esta avaliação e nenhuma promoção efetuada.
