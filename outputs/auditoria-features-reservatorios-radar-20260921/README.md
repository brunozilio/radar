# Radar — procedência das 24 entradas de nível dos reservatórios

**67 checks passaram.** Foram reconstruídas as 24 colunas de `additional-features.npz` diretamente dos 18 CSVs ONS preservados, com diferença máxima **zero**. Os 12.928 timestamps coincidem exatamente com a grade do Radar no experimento runtime19. Nenhum modelo foi treinado, nenhum HGE foi executado e nenhuma fonte foi alterada.

## Fonte e ordem das colunas

São 38.764 linhas ONS, sem duplicatas por usina/timestamp, identificadas por `JIUHQJ` (14 de Julho), `JIUHMC` (Monte Claro) e `JIUHCA` (Castro Alves). Para cada usina, primeiro `val_nivelmontante`, depois `val_niveljusante`; para cada campo, **nível, diferença em 1h, inclinação em 3h, inclinação em 6h**. Os nomes coincidem com `experiment.json` original. `feature-catalog.csv` mapeia os índices originais 0–23 aos índices 180–203 propostos para o Radar, com unidades, faixas e ausências.

Níveis são tratados em metros; diferenças/inclinações referem-se à grade nominal horária. Não são taxas instantâneas de medição quando o asof reutiliza uma leitura. Não há conversão para volume/armazenamento, subtração entre réguas distintas ou alteração de datum.

## Contrato temporal realmente executado

Para origem `O`, seleciona-se o registro mais recente com timestamp **≤ O−60min**. Ele é aceito somente se sua idade em relação a esse corte atrasado for **≤90min**. Assim, a política permite idade total de até **150min em relação a O**, não 90min. O maior valor efetivamente aceito no acervo é 121min; todas as fontes utilizadas estão pelo menos 60min antes da origem.

As diferenças de 1/3/6h usam a série assim construída nas origens anteriores correspondentes. Ambos os extremos de cada diferença foram conferidos como estritamente anteriores à emissão; nenhum usa observação em `O` ou posterior. Testes sintéticos da função pura preservada confirmaram aceitação em exatamente 90min e rejeição em 90min+1s após o corte atrasado.

Os rótulos **23:59 são literais**, sem conversão para meia-noite. Houve 3.230 seleções de campos com esse horário, contando montante/jusante e eventuais reutilizações. O teste de fronteira confirma que uma leitura das 23:59 não entra na origem 00h, cujo corte é 23h; ela pode entrar em 01h, com corte 00h e idade residual de um minuto.

## Ausências e anomalias preservadas

`source-selection-trace.csv` confere **77.568 seleções** contra `input-trace.csv`, incluindo arquivo e linha bruta: 77.541 utilizáveis, 12 sem registro anterior, 14 expiradas e uma com valor mais recente ausente. Após as diferenças, a matriz tem 310.095 células finitas e 177 ausentes.

A ausência mais recente é o montante de Julho em **30/05/2025 01h**, CSV maio/2025 linha 698, usado na origem 02h. O valor continua NaN apesar de existir leitura finita anterior às 23:59 dentro da janela permitida. Não houve bypass. A mesma regra foi conferida em teste sintético com observação futura presente.

O valor suspeito de jusante Julho **168,74 m em 03/05/2025 14h**, linha 63, permanece e alimenta a origem 15h e suas diferenças posteriores. Não foi corrigido ou mascarado. A auditoria anterior de qualidade e seu contexto permanecem aplicáveis.

No fim do acervo, as fontes ONS terminam às 11h de 21/09; a leitura ainda é aceita em 13h e expira em 14h/15h. Isso está preservado, sem buscar níveis CERAN ao vivo para preencher o histórico.

## Limites para incorporar ao candidato

O atraso de 60min, a expiração e UTC−3 são **hipóteses do experimento**, não horários históricos de publicação certificados. Os cabeçalhos CERAN preservados confirmam compatibilidade nominal de grandeza/unidade; não demonstram mesmo datum, sensor, revisão ou agregação temporal ONS/CERAN. Não transferir automaticamente este contrato para inferência ao vivo.

Acrescentar estas colunas não requer descartar linhas com nível de reservatório ausente: preservar o membership baseline declarado e deixar o tratamento nativo de NaN do HGB. Esta auditoria só certifica reconstrução, alinhamento e regras do artefato; não avalia o candidato nem autoriza promoção.

Reprodução: `PYTHONDONTWRITEBYTECODE=1 /tmp/radar-hge-venv/bin/python outputs/auditoria-features-reservatorios-radar-20260921/audit.py`. Executa somente leitura e funções puras de preparação de entradas. O nome histórico do ambiente virtual não implica execução de HGE.
