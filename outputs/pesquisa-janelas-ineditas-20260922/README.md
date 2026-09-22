# Duas janelas novas documentadas em 2018 — sondagem de disponibilidade

Resultado: **há nível horário público ANA de Muçum86510000 em dois episódios ainda não usados nos experimentos registrados, mas nenhuma das janelas é admissível diretamente sob o contrato atual da âncora**. Esta rodada não ajustou modelos, não fez inferência e não incorporou dados. Consulta documental não constitui validação inédita ou independência certificada.

| Janela literal consultada | Registros / cadência | Nível final aprovado | QC restante | Máximo discreto aprovado recuperado |
|---|---|---|---|---|
| 30/08–05/09/2018 | 168; exatamente3600s entre registros,00h inicial–23h final | 164 | 4 suspeitos | 912cm em03/09/2018 07:00:00 |
| 30/09–06/10/2018 | 168; exatamente3600s,00h inicial–23h final | 165 | 2 suspeitos,1 não avaliado | 1166cm em04/10/2018 03:00:00 |

Todos os336 níveis finais são numéricos finitos, positivos, sem zero, sem timestamp duplicado e sem lacuna na grade **horária recebida**. Isso não equivale a336 alvos aprovados: somente329 têm `CQ_NivelFinal=Dado aprovado`. Os máximos acima são máximos discretos da amostra aprovada, não certificação dos picos reais. As datas não receberam fuso, arredondamento nem deslocamento.

As sete exclusões de QC ficam preservadas nos XMLs/JSONLs e em `availability.json`: setembro02/09 03h561cm,04h615,05h662,06h701, todos suspeitos; outubro30/09 10h309cm não avaliado,02/10 19h447 e03/10 13h898 suspeitos. Nenhum foi convertido em alvo aprovado. Não há campos de nível final vazios nessas respostas; a perda de cobertura aprovada decorre de QC, não de ausência física de linhas.

## Documentação oficial e confrontos pontuais

O índice SGB já preservado em `outputs/mucum-propagacao-2026-09-21/raw/sgb-boletins-lista.html` trouxe as datas, sem inventar janelas pelo erro do modelo. O relatório SGB2022, também reutilizado, contabiliza2 eventos/13 boletins em2018; para2019 registra0/0, o que não demonstra ausência universal de cheias. Não foi justificada nova data em2019 ou2020 fora do acervo usado nesta busca delimitada.

- [Boletim SGB02/09/2018 17h](https://www.sgb.gov.br/sace/boletins/Taquari/20180902_17-20180902%20-%20174931.pdf): Muçum845cm. O registro ANA `2018-09-02 17:00:00` tem845cm e QC aprovado, numericamente idêntico. Linha José Júlio aparece em manutenção nesse boletim; não se coletaram auxiliares nesta rodada.
- [Boletim SGB03/10/2018 22h](https://www.sgb.gov.br/sace/boletins/Taquari/20181003_22-20181004%20-%20092639.pdf): Muçum1126cm. ANA `2018-10-03 22:00:00` tem1126cm aprovado. A faixa1000–1100cm para04/10 é **previsão do boletim**, não observação recuperada.

Ambos declaram o sistema em teste e nível em cm. Os valores de Muçum são inferiores ao limiar de inundação1600cm indicado nesses documentos; são episódios de elevação/cheia da bacia, sem atestar inundação urbana em Muçum. O limiar1600cm versus1800cm em documentos posteriores não prova mudança de zero. Dois pontos coincidentes auxiliam o confronto, mas não certificam datum, relógio, revisões ou disponibilidade histórica. `Last-Modified` HTTP dos PDFs, hora no nome do arquivo, momento do boletim e `DataHora` telemétrico não são contratos intercambiáveis.

## Compatibilidade e limites

Para uma origem horária O e consulta O−15min, a última leitura horária interna é O−1h: idade45min após a consulta. O contrato de expiração15min rejeita todas as336 origens consultadas (na primeira, sequer existe leitura anterior dentro da resposta). Assim são **zero pares âncora/alvo elegíveis nos12 horizontes**, apesar dos alvos horários exatos disponíveis. Não arredondamos medições, não interpolamos e não alteramos o contrato. `availability.json` guarda o denominador de targets exatos porh, excluindo a fronteira final; os rastros `*-anchor-coverage.json` mostram cada consulta/idade.

Há672 posições de15min esperadas porsemana, mas só168 horários de medição recebidos (164/165 aprovados). A ausência de amostras sub-horárias nessa resposta não prova ausência em qualquer outro acervo. O fuso/DST do serviço legado, o zero da régua e sua equivalência2018↔2025/26, revisões e hora de primeira publicação permanecem sem contrato explícito. Nenhuma hipótese de UTC−3 foi aplicada ao conteúdo. Vazão/chuva e todos seus QC foram preservados e sumarizados, sem considerar vazão independente do nível ou auditá-la hidraulicamente. As usinas eram de regime pré-avarias2024; níveis/QI/chuva de montante não foram sondados, portanto a disponibilidade de todos os insumos Radar continua desconhecida.

Recomendação: catalogar as duas semanas como candidatas documentais com nível horário aprovado e bloqueio de compatibilidade de âncora. Qualquer mudança de resolução/idade exigiria protocolo explícito posterior, sem selecionar ajustes pelos resultados dessas janelas. Não há validação de modelo nesta rodada e a meta98% não foi aferida nem atingida.

## Proveniência e verificação

Foram4 buscas web,2 GETs de PDFs e2 GETs ANA, sem retries. `plan.json` foi gravado antes dos GETs; as buscas preliminares já haviam ocorrido e foram preservadas em `search-results.txt` (retorno textual da ferramenta, não corpo HTTP dos sites). `collect.py` limita os quatro downloads e respeita recibos existentes. `raw/*.receipt.json` conserva URL, headers, UTC da coleta e SHA256; XMLs/PDFs são integrais. `local-source-references.json` conserva referências/hash e cópias dos documentos locais consultados, incluindo snapshot do documento principal sem modificá-lo.

`audit.py` reproduz ALL-QC JSONL mantendo strings e índices XML1-based, contagens e rastros. `verification.json`:10 verificações passaram, incluindo fidelidade integral XML→JSONL, identidade da estação, os dois confrontos pontuais e os quatro hashes de recebimento. `manifest.json` e `manifest-check.json` verificam todos os artefatos próprios. Nenhuma ação operacional, treino, matriz, auxiliares ou nova pesquisa fora do escopo.
