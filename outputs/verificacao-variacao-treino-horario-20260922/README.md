# Verificação independente — variação do treino entre 00h e 01h

**170 verificações aprovadas.** Leitura local dos snapshots `mucum-hourly-20260922T000704-0300` e `mucum-hourly-20260922T010016-0300`, sem importar helpers operacionais, treinar, fazer inferência ou consultar a rede. O diagnóstico do root foi reproduzido; não houve divergência concreta.

O corte conferido é **21/09/2026 às00h, UTC−3, exclusivo**. Antes dele, os114campos numéricos dos históricos ANA/CERAN têm timestamps, valores e NaNs idênticos entre os snapshots. Os60campos `raw:` da grade também não mudaram. Esse resultado se limita ao histórico numérico preservado e ao intervalo: não é uma comparação de todos os XMLs/QCs, nem afirma ausência de revisões depois do corte.

Apesar disso, **94 das180colunas mudaram, somando538.204células**, nas12.912origens históricas. Todas as contagens por coluna foram recalculadas. Há51.648posições de15min antes do corte.

| Série | Atraso00h → 01h | Deslocamento adicional reproduzido | Posições comparadas | Diferenças |
|---|---:|---:|---:|---:|
| Muçum86510000, nível | 15→30min | 1quarto de hora | 51.647 | 0 |
| Santa Tereza86472600, nível | 15→75min | 4quartos de hora | 51.644 | 0 |
| Castro Alves, defluênciaQ | 0→60min | 4quartos de hora | 51.644 | 0 |

Valores finitos **e NaNs** foram iguais após o deslocamento. As posições iniciais sem correspondente na grade antiga foram conferidas por busca independente no histórico de origem, para as duas versões: último registro anterior ou igual à consulta, sem pular NaNs, idade máxima de15min para nível e90min paraCERAN. Essa reconstrução também foi exata. As últimas observações e idades atuais dos três casos foram recalculadas diretamente das séries.

As máscaras de treino dos14horizontes foram reconstruídas a partir de base finita, alvo finito, primeiras24entradas finitas e alvo estritamente anterior ao corte. Todos os índices coincidem com os snapshots de auditoria. Emh1, **10.875→10.899membros**, com258entradas,234saídas e10.641origens comuns. Entre essas origens comuns,7.429bases mudaram; nenhum alvo mudou. As contagens dos14horizontes, inclusive mudanças de base/alvo, coincidem com `membership.csv` do diagnóstico original.

## Interpretação do código

Em `prepare_current`, o atraso é calculado pela distância entre a origem atual e a última observação finita da fonte. Para níveis e vazões, esse atraso é aplicado à consulta de **toda a grade histórica**. Para chuva, os acumulados históricos são deslocados pelo atraso atual truncado a passos de15min. Portanto, fontes históricas idênticas podem gerar uma matriz diferente a cada atualização. A verificação por deslocamento demonstrou isso exatamente nos três casos acima; não pretende decompor causalmente todas as alterações de chuva e meteorologia.

O runner reconstrói as entradas, calcula novamente a máscara e ajusta modelos em cada execução. **Um corte temporal fixo impede admitir alvos depois da data definida, mas não congela matriz, membros, bases/respostas, pesos derivados ou modelos.** Alterar a base também altera a resposta de treino `alvo−base`, mesmo que o alvo fique igual. Esta auditoria não atribui a mudança das previsões a um único componente e não mede o efeito de congelar latências.

A idade observada agora é uma hipótese de preparação reaplicada ao passado, não certificação dos horários de publicação históricos. Nenhum candidato foi promovido. **A meta de98% não foi atingida ou demonstrada por esta conferência de integridade.**

## Artefatos

`verify.py` é reproduzível com Python+NumPy e escreve apenas nesta pasta. `verification.json` preserva170checks; `direct-shift-checks.csv`, `independent-history.csv`, `independent-feature-changes.csv` e `independent-membership.csv` contêm a evidência detalhada. `input-hashes.json` identifica todas as fontes lidas; os hashes de entradas e resultados do diagnóstico original também foram conferidos. `artifact-hashes.json` cobre os arquivos desta auditoria, exceto ele próprio. Nenhum snapshot, script operacional ou resultado do root foi alterado.
