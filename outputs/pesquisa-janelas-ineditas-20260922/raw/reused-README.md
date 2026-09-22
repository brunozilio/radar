# Diversidade de eventos anteriores a 2020 — pesquisa Radar

Concluída em 22/09/2026. **Nenhuma série de nível foi recuperada nas três sondagens de Muçum 86510000.** As três respostas são HTTP 200 com mensagem explícita `Sem dados`; não houve falha de rede nessas consultas. A pesquisa oferece janelas documentais candidatas, ainda sem insumos suficientes para treino. Não houve normalização, interpolação, inferência, ajuste, promoção ou alteração operacional.

## Janelas sondadas e força da documentação

| Janela literal inclusiva | Documento / evidência | Nível ANA recuperado | Limite |
|---|---|---:|---|
| 18–24/07/2011 | Artigo hospedado no Boletim Geográfico do RS menciona inundação regional em 21/07/2011, citando Eckhardt et al. (2013); artigo SGB já preservado inclui máximo anual de Muçum em 2011. | 0 registros | O artigo do RS também menciona **11/07/2011**. Conflito preservado, sem corrigir data. Não foi obtido o AVADAN original ou horário do pico de Muçum. |
| 08–14/10/2015 | Boletim da Defesa Civil estadual datado 11/10/2015 aparece no índice web e lista municípios atingidos no Vale. | 0 registros | O GET direto da página retornou **404**, com corpo preservado; evidência textual é a representação do buscador. Impacto regional não estabelece pico, data exata ou nível em Muçum. |
| 24–30/05/2017 | Boletim extraordinário SGB de 26/05/2017, 22h; retrospectiva municipal confirma cheia em maio. | 0 registros | Muçum e Linha José Júlio aparecem em manutenção. A previsão para Estrela não é observação de Muçum. |
| 2019 — sem janela escolhida | Relatório SGB 2022, PDF p.23 / impressa19, tabela3: zero eventos observados e zero boletins em 2019 na contabilidade SAH. | Não consultado | Nenhuma data suficientemente documentada nesta busca. Não significa inexistência de cheias no ano. |

As três semanas foram pré-registradas em `collection-plan.json` antes dos GETs ANA, com motivação documental e sem usar erros ou previsões do modelo para seleção. O inventário local restrito examinou 40 XMLs pertinentes e não encontrou timestamps desses anos para reutilização. **Não se afirma que todo o workspace ou todo o acervo ANA foi esgotado.**

O [boletim primário SGB de 26/05/2017](https://www.sgb.gov.br/sace/boletins/Taquari/20170526_22-20170527%20-%20001639.pdf) usa a legenda “Equipamento em manutenção” para os campos ausentes e declara monitoramento/previsões em teste. Nível em cm; referência de inundação de Muçum então indicada em 1.600 cm. Esse limiar diferente dos 1.800 cm de documentos posteriores **não comprova mudança do zero**. A [Prefeitura de Bom Retiro do Sul, publicação15/01/2018](https://bomretirodosul.rs.gov.br/noticia/view/2550) registra duas cheias em 2017, maio e junho, com máximos de16m e18m **na Barragem Eclusa**, não na régua de Muçum. Não foi criada uma quarta janela arbitrária de junho sem dia documentado.

A [publicação científica de2021 no portal oficial do RS](https://revistas.planejamento.rs.gov.br/index.php/boletim-geografico-rs/article/download/4444/4124), PDF pp.13–14 / impressas64–65, contém as duas datas conflitantes de2011. O seu estudo primário é sobre Encantado em2020; as afirmações de2011 são **citação secundária**, mesmo estando em domínio oficial. Não elevamos isso a registro primário certificado do episódio de2011. Os documentos primários SGB/ANA recuperados não fecharam essa data.

A [página estadual de11/10/2015](https://www.estado.rs.gov.br/defesa-civil-divulga-novo-boletim-sobre-situacao-nos-municipios-e-nas-estradas) permanece uma pista documental com recuperação direta malsucedida. O corpo404 e o resultado de busca foram guardados separadamente; não se apresenta o HTML404 como texto válido do boletim.

## Cobertura efetivamente verificada

Cada pedido ANA abrange sete dias. Todos retornaram exatamente a mensagem de ausência da estação86510000 no período solicitado. `probe-results.json` liga URL, UTC de coleta, SHA-256, statusHTTP e corpoXML. Não existem linhas para classificar como aprovadas/suspeitas/reprovadas, nem campos vazios dentro de linhas: **ausência de registros é distinta de QC negativo**. Duplicatas e conflitos são zero porque nenhuma linha foi retornada. Há zero níveis em horários exatos e em quartos de hora; as grades168horas/672quartos são apenas referência de calendário, não cadência comprovada para o sensor histórico.

Os corpos podem ter o mesmo hash porque o serviço devolve mensagem idêntica sem ecoar as datas. Os três pares requisição/URL/metadados permanecem separados. Não houve retries. Nenhum dado foi convertido em zero. O resultado não prova inexistência de série convencional, dados em outro produto, arquivo local do operador ou restrição temporal do endpoint. Não foi feita consulta anual ampla.

## Régua, relógio e regime: o que continua pendente

O [artigo primário SGB sobre Muçum](https://rigeo.sgb.gov.br/handle/doc/24429), PDF p.5, já preservado e reutilizado por hash, relata ausência de registro de mudança de zero no histórico estudado; a seção foi levantada em22/07/2022, com dados até08/2022. A análise usa máximos anuais de **dupla leitura**, que não equivalem a sequência15min. Não certifica continuidade física até2026 nem disponibilidade na emissão passada.

As investigações locais anteriores continuam válidas como limites: notas SGB publicam33,985m e33,96m para referências de Muçum, sem explicação completa da diferença e das vigências. Não foram descobertos nesta rodada novos certificados de nivelamento, monografias/relocações ou vínculo explícito entre `DataHora` do serviço legado e fuso/DST de2011/2015/2017. Nenhum timestamp foi deslocado, arredondado ou atribuído a UTC por conveniência. Ausência atual no endpoint tampouco informa quando um registro original teria sido publicado.

As janelas são anteriores às avarias demaio/2024. O acervo primário ONS/CERAN já documenta interrupções/danos e restaurações posteriores; isso exige distinguir regimes de operação em qualquer comparação futura. O rótulo “pré-avarias” sozinho não prova equivalência entre2011,2015,2017,2020 e2026. Nesta rodada não foram consultadas séries ONS, chuvas, níveis auxiliares ou previsões meteorológicas dessas semanas; a disponibilidade dos120insumos do Radar é desconhecida. Não substituir previsão histórica por reanálise ou chuva futura observada.

## Próximo caminho concreto, sem ação externa executada

1. Consultar o acervo convencional ANA/Hidroweb de Muçum86510000 e os boletins de dupla leitura citados pelo SGB, inicialmente pelas três semanas, preservando cadência, QC, revisão, régua e unidade. Se houver só duas leituras diárias ou máximos isolados, isso não atende automaticamente à avaliação horária do Radar.
2. Resolver2011 pelo AVADAN original e pela monografia/série da estação; recuperar o boletim estadual2015 por arquivo oficial antes de afirmar data local. Para2017, verificar registros do observador e manutenção referida no boletim. São pedidos/consultas futuras, **não dados obtidos**.
3. Para2019, manter pendente até surgir fonte oficial com data. Depois de recuperar nível útil, examinar chuva contemporânea e usinas dentro de um protocolo próprio. Não reservar ou declarar independência de teste por simples menção de evento; aqui houve apenas pesquisa documental e sondagens de cobertura, nenhuma avaliação de modelo.

## Reprodução e integridade

`collect.py` registra plano/cache, coleta no máximo3sondagens ANA e4documentos específicos; recusa repetir tentativas existentes. `audit.py` verifica22condições de integridade, mensagem, HTTP e precedência do plano. `new-source-manifest.json` preserva7requisições diretas:6HTTP200 e1HTTP404; `reused-source-manifest.json` referencia9artefatos anteriores sem modificá-los. PDFs novos: boletim2017 e artigo oficial-hospedado2021; HTML municipal2017 recuperado. Textos extraídos são derivados identificados pelo nome; o texto `sgb-2022.txt` veio do PDF pré-existente, sem novo download.

`artifact-hashes.json` cobre os artefatos desta pasta, exceto o próprio manifesto. Acesso público não foi interpretado como licença irrestrita de redistribuição; cópias locais foram preservadas para auditoria. Nenhuma mensagem foi enviada a terceiros.
