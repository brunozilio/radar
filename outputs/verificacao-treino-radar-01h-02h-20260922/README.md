# Verificação da variação de treino entre 01h e 02h

**381 verificações passaram**, sem divergência com o diagnóstico do coordenador. Na etapa principal não houve ajuste, inferência de modelo, consulta de rede ou execução/importação de geradores operacionais. O suplemento posteriormente autorizado reaplicou somente 28 previsões emitidas e um contrafactual, descritos abaixo, sem novo ajuste ou emissão. A comparação usa os snapshots selados `mucum-hourly-20260922T010016-0300` e `mucum-hourly-20260922T020011-0300`, com corte exclusivo em 21/09/2026 00h UTC−03.

Antes do corte, os 114 campos numéricos dos históricos ANA/CERAN normalizados são iguais, inclusive timestamps e NaNs. Também são iguais os campos brutos da grade derivada. Isso não é uma revisão integral dos campos QC textuais de todos os XML históricos; é comparação das fontes numéricas seladas efetivamente usadas no preparo. Seus hashes e manifestos foram conferidos.

As diferenças da matriz são **75 colunas e 144.159 células**, restritas às colunas 45–119, de precipitação observada e cobertura. As colunas de níveis/vazões e as 60 de previsão meteorológica permanecem iguais antes do corte. As bases Muçum e os alvos também permanecem iguais.

## Atraso de chuva, separado de nível

O código `prepare_current` encontra o último `rain` finito até a origem de cada ciclo e calcula o atraso da chuva a partir dele. Aplica depois `int(atraso/900)` como deslocamento de toda a série histórica de acumulados/coberturas de cada posto. `idades-fontes.csv` registra H nos postos ANA; não é um registro do atraso de chuva.

Dos 27 postos, sete mudaram seu atraso de chuva:

| Posto | Última chuva, ciclo 01h → 02h (UTC−03 assumido) | Atraso real em minutos | Deslocamento em slots de 15min | Regiões com peso |
|---|---|---:|---:|---|
| 86060010 | 21/09 08h → mesma | 1020 → 1080 | 68 → 72 | Alto Antas, Tainhas |
| 86102000 | 21/09 10h → mesma | 900 → 960 | 60 → 64 | Alto Antas, Tainhas |
| 86125000 | 21/09 11:59 → mesma | 781 → 841 | 52 → 56 | Prata-Turvo, Alto Antas |
| 86200900 | 21/09 11h → mesma | 840 → 900 | 56 → 60 | Alto Antas |
| 86298000 | 21/09 19h → mesma | 360 → 420 | 24 → 28 | Alto Antas |
| 86403000 | 21/09 23h → 22/09 01h | 120 → 60 | 8 → 4 | Carreiro, Prata-Turvo |
| 86448000 | 21/09 19h → mesma | 360 → 420 | 24 → 28 | Baixo Antas, Alto Antas |

Seis postos ficaram uma hora mais antigos sem nova chuva finita. O posto 86403000 recebeu chuva mais recente, reduzindo seu atraso em uma hora. Os 20 restantes mantiveram o atraso relativo. Em 86125000, o minuto residual é descartado pelo `int`: atrasos de 781/841 minutos tornam-se deslocamentos efetivos de 780/840 minutos. Essa truncagem foi preservada, sem arredondar o timestamp literal 11:59.

A distinção de campo é material em **86200900**: o atraso de nível registrado no CSV é 780→840 minutos, enquanto o atraso de chuva efetivo é **840→900 minutos**. A última chuva finita continua às11h, embora haja nível posterior. Não atribuímos os campos de chuva ao atraso de nível.

## Reconstrução independente da chuva

Foram reconstruídas **968.400 células em cada ciclo**, 1.936.800 no total, a partir dos intervalos de chuva dos 27 históricos selados. O método soma apenas intervalos válidos com duração positiva ≤90min e precipitação finita não negativa, cujo término já ocorreu até a consulta atrasada; desconta a fração anterior à borda da janela. Preserva pesos regionais, cobertura mínima de 0,5, ausência de renormalização, limites da grade inicial e defasagens P3 de 3/6/12h.

Não foram chamados `observed_rain_windows`, `telemetry_features` ou `prepare_current`. As máscaras de NaN reconstruídas coincidem exatamente com as duas matrizes. A maior diferença numérica foi **8,86652×10⁻¹⁴**, abaixo da tolerância de 2×10⁻¹⁰. Essa concordância numérica comprova a reconstrução dos campos; não garante invariância de árvores sob perturbações mínimas de entrada, e nenhuma inferência foi executada para testar isso.

Como as séries anteriores ao corte e os pesos são idênticos, e as duas matrizes se reproduzem com os atrasos específicos acima, as mudanças dos campos de chuva são explicadas por realinhamento histórico. A chegada ou não de dados recentes muda o atraso reaplicado a todo o passado, sem alterar as observações históricas anteriores ao corte. Não há inferência aqui sobre erro de previsão futuro.

## Amostras, respostas e pesos

Os 14 conjuntos operacionais de treino, h1–h14, foram reconstruídos e comparados com `training-indices.npz` dos auditores de suporte de 01h e 02h. Todos têm índices, ordem, bases, alvos, respostas delta e pesos idênticos. Não houve inclusão/exclusão de origem. Em h1, são 10.899 linhas em ambos os ciclos.

Portanto, nesta rodada a variação não veio de novos rótulos ou de mudança de admissibilidade. As entradas de chuva das mesmas amostras mudaram. **Corte temporal fixo não congela a matriz nem os parâmetros estimados do modelo.** Isso não é uma medição de erro futuro.

## Suplemento limitado: diagonais e alvo das07h

A pedido posterior do coordenador, `check_diagonals.py` carregou os 28 modelos já emitidos e reaplicou cada um somente ao seu vetor/base original. As **28 diagonais coincidem exatamente** com os JSON de emissão e a tabela preservada, e os hashes dos modelos conferem com os artefatos declarados. Não houve refit, nova emissão ou escrita no ledger.

Para o mesmo alvo de 22/09/2026 07h UTC−03, a emissão de01h usava h6 e a de02h usa h5. Reapliquei uma vez o modelo antigo de **h5** ao vetor/base novo para conferir o caminho ordenado:

`18,565743602805167 → 19,10654979667524 → 19,22825367238508 m`.

Logo, a revisão total **+0,6625100695799127 m** é igual a **+0,5408061938700719 m** (troca conjunta de inputs/base e horizonte, conservando o conjunto antigo de modelos) mais **+0,12170387570984076 m** (troca do modelo h5 nos inputs novos). A soma confere dentro de 10⁻¹⁴, e os três valores coincidem exatamente com a decomposição salva.

O valor intermediário nunca foi emitido. A ordem desse caminho importa; não são parcelas causais isoladas, melhora de precisão ou erro observado. O suplemento não reaudita os demais contrafactuais nem as outras12 revisões por alvo.

## Artefatos e limites

`rain-delays.csv` contém as 27 latências de chuva e a coluna separada de atraso de nível. `history-comparison.csv`, `raw-grid-comparison.csv`, `feature-changes.csv` e `membership.csv` guardam as contagens; os dois NPZ `reconstructed-rain-cycle*.npz` guardam as reconstruções independentes. `verification.json`, código e hashes permitem reprodução local.

A idade reconstruída não certifica publicação/recepção histórica, fuso do endpoint ou referência vertical. Nenhuma fonte, modelo, operação ou auditoria anterior foi alterada. A meta permanece não atingida. Não reexecutar depois de congelamento externo sem autorização.
