# Muçum: complemento documental de fuso e vigência

Pesquisa local concluída em 2026-09-21T21:16:06.188154+00:00. Duas fontes primárias novas, sem treino, alteração de modelos, ledger ou conversão de dados. Documentação anterior consultada e referenciada por hash em `prior-evidence.json`; não foi novamente baixada. Foram pesquisados identificador SGIH 257170, contrato temporal do endpoint e manutenção/troca de sensor; não foi obtida prova adicional de vigência do zero.

## Resultado e limites

- **ANA, apresentação Análise e disponibilização de dados hidrológicos, página 20:** captura da interface Hidro-Telemetria com período encerrando em 11/11/2024 e aviso explícito de UTC−3. Nível em cm e chuva em mm aparecem nos eixos. É uma corroboração histórica mais recente que a apresentação de 2020 já arquivada. A estação da captura é Porto Velho, não Muçum. Não estabelece o contrato `DataHora` de `DadosHidrometeorologicosGerais`, horário de recepção, atraso, política de revisão nem a configuração atual de Muçum em 2026. A data vista na interface não foi promovida a data de publicação do documento.
- **SGB/CPRM, Relatório Sistema de Alerta da Bacia do Rio Taquari, março/2014, Anexo III, página PDF 81:** o protocolo propõe guardar controle de equipamentos com datas de instalação e troca de sensores; lista Muçum 86510000 entre as estações com dados convencionais. Isso identifica uma classe documental útil para a investigação. Não comprova que tais registros estejam disponíveis, nem contém a ficha de manutenção ou nivelamento que concilie 2020–2026.

As páginas 20/81 foram renderizadas e conferidas visualmente. Fuso do endpoint atual e vigência/vínculo marco–régua–sensor continuam **PENDENTES**. A divergência documental anterior 33,985 m versus 33,96 m não foi resolvida. Não aplicar offset de 2,5 cm nem interpretar máximo manual/sensor como medições equivalentes.

## Proveniência e qualidade

`manifest.json` contém URLs públicas, coleta e término reais UTC, status HTTP, headers e SHA-256 dos bytes. O endpoint legado do SGB retornou HTML apesar de ter extensão PDF; essa resposta foi preservada como `sgb-legacy-redirect.html` e excluída da evidência. O conteúdo PDF foi obtido pelo bitstream público oficial, referente à mesma segunda fonte, sem credenciais ou contorno de acesso. Uma tentativa no runtime Python de documentos falhou na validação TLS; a coleta foi feita com o runtime hidrológico já existente e validação TLS padrão, sem desabilitá-la.

Unidades observadas na figura ANA: nível cm, chuva mm. Não há série nova de observações neste lote. Nenhum datum/zero atual ou intervalo de validade foi certificado; qualidade é documental, não QC de medições. Licença explícita de reutilização dos dois documentos não foi verificada; preserve atribuição ANA/SGB e uso local de pesquisa, sem presumir domínio público.

## Fontes

1. [ANA/Progestão — Análise e disponibilização de dados hidrológicos](https://progestao.ana.gov.br/destaque-superior/eventos/oficinas-de-intercambio-1/monitoramento-e-enquadramento/monitoramento-hidrologico/analise-e-disponibilizacao-de-dados-hidrologicos-walszon-terllizzie-araujo-lopes-ana.pdf).
2. [SGB/CPRM — Sistema de Alerta do Taquari, 2014](https://rigeo.sgb.gov.br/server/api/core/bitstreams/b772845b-ba72-4567-8915-0372b9cf76dc/content).

Próxima evidência útil continua sendo monografia/registro de nivelamento, instalação e troca de sensor com datas de vigência, além de documentação oficial que vincule o fuso ao endpoint. Nenhuma mensagem foi enviada a pessoas. Nenhuma pendência anterior foi considerada encerrada.
