# Fuso de DataHora no legado ANA — revisão delimitada

**Não foi encontrada declaração explícita suficiente de timezone/DST aplicável a `DataHora` de `DadosHidrometeorologicosGerais`, estação Muçum86510000, em2025/2026.** A hipótese UTC−3 permanece corroborada para a apresentação atual, sem ser promovida a contrato certificado da operação. Nenhuma flag de elegibilidade, dado, modelo ou automação foi alterada.

Esta rodada reutilizou15artefatos pertinentes e seus metadados de coleta, sem repetir WSDL/DISCO, consultas de dados ou buscas gerais já realizadas. **Zero fontes/requests novos**, sem autenticação ou contatos externos.32verificações locais passaram. A conclusão negativa é limitada às fontes examinadas; não afirma inexistência de documentação em outros acervos.

## O que cada fonte realmente estabelece

| Fonte preservada | Evidência | Limite para a operação-alvo |
|---|---|---|
| [Portal ANA Gerar Gráficos](https://www.snirh.gov.br/hidrotelemetria/gerarGrafico.aspx), resposta21/09/2026 comMuçum selecionada | DeclaraUTC−3 na apresentação e identifica a estação86510000; nível emcm. A auditoria anterior encontrou73níveis iguais no relógio nominal do legado, com apoio do epochUTC no mapaANA. | A série está embutida noHTML; não há vínculo público visível do backend com`DadosHidrometeorologicosGerais`. Coincidência de valores/horários não certifica versão ou vigência histórica. |
| [Manual legado ANA2013](https://www.ana.gov.br/telemetria1ws/Telemetria1ws.pdf), texto completo revisto | Descreve`DataHora` na operação **DadosHidrometeorologicos**, semUTC/GMT/fuso/DST. A introdução relaciona os bancos com a visualização nos sistemas Telemetria1/HIDRO. | Essa referência genérica ao sistema não especifica o fuso nem a operação **Gerais**. O único trecho“Brasília” no texto é endereço institucional, não contrato temporal. |
| [WSDL legado](https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx?wsdl), já auditado | Requisição comstrings e resposta de dados emschema/diffgram genérico. | Não declara`DataHora` individualmente na resposta-alvo nem timezone/DST; campos homônimos em operações de escrita não devem ser transferidos para essa leitura. Não repetimos esses pedidos. |
| [Apresentação ANA/Progestão2020](https://progestao.ana.gov.br/destaque-superior/eventos/webinarios/cotas-de-alerta/3-definicao-de-valores-de-referencia.pdf), página4 já conferida no acervo | Interface declaraUTC−3 e descreve Brasília sem ajuste de verão. | Evidência da interface/produto naquele documento, sem cláusula vinculando a operação-alvo ou suas versões2025/2026. |
| [Formato HIDRO1.2/ANA2012](https://www.ana.gov.br/arquivos/infohidrologicas/cadastro/OrientacoesParaEnvioDosDadosHidrologicosColetadosDuranteaResolucaoANEEL_396_1998.pdf), pp.26–28 | Distingue mês/ano, hora da leitura e média diária. As respostas convencionais recém-recuperadas têm`DataHora` no dia1 e campos de cada dia. | Campo homônimo com semântica diferente:07h/17h são horários nominais do observador;00h de média diária não é observação instantânea. Não define o fuso do timestamp telemétrico legado. |
| [Manual HidroWebService20/02/2026](https://www.gov.br/ana/pt-br/assuntos/monitoramento-e-eventos-criticos/monitoramento-hidrologico/orientacoes-manuais/manuais/manual-hidrowebservice_publica.pdf) e [Swagger atual](https://www.ana.gov.br/hidrowebservice/swagger-ui/index.html), preservados | Distingue campos de medição/coleta e atualização na base; filtros de leitura/última atualização. | API diferente. A OpenAPIv1 preservada não contém declaração explícita deUTC/GMT/fuso/DST na busca textual examinada. Mesmo uma convenção da API nova não seria automaticamente o contrato do legado. |
| [SACE Taquari](https://sace.sgb.gov.br/taquari/), código público preservado | Obtém offset do navegador e ajusta timezone da sessão. | Horário apresentado por uma sessão não prova offset fixo doCSV nem da outraAPIANA. |

## Distinções necessárias

1. **Medição** é o instante atribuído à observação. O manual da API nova distingue esse campo da atualização, mas isso não define formalmente`DataHora` na operação antiga.
2. **Publicação/recepção/atualização** podem ocorrer depois. O relógioUTC da nossa coleta e o cabeçalhoHTTP`Date` descrevem a respostaHTTP, não o fuso da observação. `DataIns` das séries convencionais foi mantido como campo administrativo original; não foi convertido em primeira publicação.
3. **Hora do observador** nas leituras convencionais07h/17h permanece nominal, sem certificação deUTC−3/DST nesta coleta. Não substitui a cadência ou o contrato da telemetria.
4. **Rótulo diário/mensal** não é instante medido: média diária às00h não deve alimentar emissão no começo do dia, e dia1 nos registros mensais não significa que todos os valores foram medidos naquele dia.
5. **Unidade e referência vertical** são contratos separados: nível emcm e código da estação não resolvem fuso, vigência do zero/sensor, revisões ou disponibilidade passada. Os limites de datum encontrados anteriormente continuam intactos.

## O que falta precisamente

Declaração oficial que nomeie **a operação`DadosHidrometeorologicosGerais` e o campo`DataHora`**, indiqueUTC−3fixo ou regra deDST, significado de medição/recepção e datas/versões de validade que abranjam2025/2026. Também falta histórico de disponibilização/revisões para reconstruir o que estava conhecido em cada emissão. A nova documentação convencional não preenche essas lacunas.

Não foram enviadas solicitações aos canais técnicos já documentados, nem houve acesso autenticado. A decisão de não acrescentar buscas nesta rodada evita repetir fontes que já se mostraram insuficientes; não transforma a busca negativa em prova universal.

## Evidências e integridade

`reused-source-manifest.json` registra os15arquivos, URLs, hashes e apontadores para os manifestos originais com datas/recibos. Os corpos primários permanecem nas pastas anteriores, sem cópias ou alterações. `legacy-manual-extracted.txt` é uma extração local nova doPDF previamente coletado, não um novo documento oficial. `bounded-text-search.json` preserva a busca por termos e linhas, incluindo ocorrências deBrasília sem sentido de fuso.

`audit.py`, `verification.json` e `conclusion.json` permitem repetir a conferência local e registram32checks. A busca textual tem o limite de texto extraído e código público; não pretende analisar cláusulas inexistentes ou backend não publicado. `artifact-hashes.json` cobre os arquivos desta entrega, exceto ele próprio. Nenhum modelo foi executado.
