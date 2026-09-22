# Contrato temporal público de Muçum — verificação em 21/09/2026

**Encontrada fonte primária atual com estação, unidade e fuso explícitos:** a página pública [ANA — Gerar Gráficos](https://www.snirh.gov.br/hidrotelemetria/gerarGrafico.aspx), após selecionar a estação **86510000 / MUÇUM / RIO TAQUARI / ANA / SGB-CPRM**, declara **UTC−3** e identifica o eixo como **nível (cm)**. A resposta íntegra está em `raw/ana-form-mucum-data.html`, com coleta e SHA-256 no manifesto. Isso confirma a convenção da apresentação atual desse produto; não confirma automaticamente o contrato do serviço legado, versões históricas, continuidade do zero da régua ou disponibilidade passada.

## Evidência direta e rastreio da consulta

A navegação pública usa uma sessão anônima, sem credenciais. A página inicial chama `Default.aspx/SetCookie`; isso foi reproduzido como publicado. O mapa oferece link `gerarGrafico.aspx`. A pesquisa por 86510000 retorna a opção **291051520 — 5 - 86510000 - MUÇUM**. Selecionar essa opção envia o formulário à própria `gerarGrafico.aspx`, pelo evento `ctl00$cphCorpo$ctl01$lstEstacoes`. Não se adivinhou uma API interna.

Na resposta dessa seleção:

- Linha 330: mensagem explícita de disponibilização em UTC−3.
- Linha 525: estação Muçum selecionada e identificador interno 291051520.
- Linha 1901: título da estação com código, rio, responsável e operadora.
- Linha 1902: `chartData` contendo a série retornada pelo servidor, antes de executar JavaScript.
- Linha 2001: unidade nível (cm); linha 2019: `dataProvider: chartData`.

`contract-evidence.json` preserva esses trechos com referências de linha. A série tem 671 registros, de **14/09/2026 18:30 a 21/09/2026 18:00**, mantidos nos horários originais em `ana-graph-extracted-data.json`. Não houve interpolation, alteração ou filtragem por modelo.

**Limite do vínculo:** os dados vêm embutidos no HTML de resposta da própria página ASP.NET. O HTML/JS público inspecionado não mostra requisição a `ServiceANA.asmx/DadosHidrometeorologicosGerais`. Não há base para afirmar que o backend da página usa esse serviço ou a mesma versão de banco. A convenção explícita do portal não foi promovida a contrato documentado desse outro endpoint.

## Corroboração com o legado e com UTC no mapa oficial

A resposta do endpoint legado, coletada separadamente para 21/09/2026, contém **73 horários numéricos em comum** com a página: **73/73 níveis idênticos, maior diferença 0 cm**. O pareamento usa o relógio nominal das strings; como o portal declara UTC−3, isso corrobora essa interpretação atual das strings do legado. Não valida revisões históricas, latência, disponibilidade na origem da previsão ou identidade física do sensor.

O mapa público atual [ANA Hidrotelemetria](https://www.snirh.gov.br/hidrotelemetria/Mapa.aspx) fornece um iframe Experience Builder. Sua configuração pública aponta para o WebMap Cotas de Referência, que aponta para a camada:

[ANA — CotasReferencia2 / MapServer / 2](https://portal1.snirh.gov.br/server/rest/services/SGH/CotasReferencia2/MapServer/2?f=pjson).

A consulta filtrada por `Codigo=86510000` retorna Muçum, identificador interno 291051520, ANA/SGB-CPRM, coordenadas −51,8686/−29,1672, `Ult_Dado=1387` e `Data_ult_dado=1790024400000`. O campo temporal tem tipo `esriFieldTypeDate`; a camada retorna `dateFieldsTimeReference:null` e `datesInUnknownTimezone:false`. A [documentação primária Esri de Query Map Service Layer](https://developers.arcgis.com/rest/services-reference/enterprise/query-map-service-layer/) define retorno em UTC e a convenção UTC quando a referência de tempo é nula. A resposta ANA se interpreta, por esse contrato técnico, como:

**21/09/2026 21:00Z = 21/09/2026 18:00 UTC−3, valor 1387**, correspondente ao nível de **1387 cm** da página e ao `NivelFinal=1387.00`, aprovado, do legado às 18h.

A unidade de `Ult_Dado` não está explicitada no metadado dessa camada; a identificação como cm usa a correspondência com a página oficial da mesma estação. O epoch é evidência de serialização UTC segundo o protocolo, não prova de que o carregamento da base nunca sofreu um erro de fuso. A coincidência atual reforça a interpretação, sem substituir documentação do endpoint legado.

A cadeia completa é preservada: HTML do mapa → configuração do Experience Builder → WebMap → metadados da camada → resposta da consulta de Muçum. `comparison-summary.json` contém as contagens e timestamps; `portal-legacy-comparison.csv` guarda cada confronto com QC original.

## Ressalva SACE e fonte complementar

A página pública [SACE Taquari](https://sace.sgb.gov.br/taquari/) calcula `getNameTimeZone()` usando `Date.getTimezoneOffset()` do navegador e chama `LoginService.setTimeZone(...)` (linhas 389–399 do HTML preservado). Portanto a apresentação do portal tem entrada de fuso da sessão; não se deve tratar um horário visual isolado como contrato fixo do CSV. O CSV público de Muçum preservado contém `data_hora_medicao` e `indice`, sem offset/unidade explícitos no cabeçalho. Não foi executada mudança de fuso nem chamada administrativa nesse sistema.

Também foi preservada a [notícia oficial SGB de 22/07/2026](https://www.sgb.gov.br/w/boletim-de-alerta-hidrologico-da-bacia-do-rio-taquari-niveis-seguem-em-elevacao-em-municipios-monitorados), que declara horário de Brasília para o boletim e cita Muçum. É evidência do boletim, não especificação do CSV ou SOAP.

## Conclusão para o registro prospectivo

1. **Confirmado para o produto público atual ANA:** apresentação UTC−3, nível em cm e identidade administrativa 86510000 Muçum, com série numérica acessível sem autenticação.
2. **Corroborado para o legado atual:** 73 níveis coincidem no relógio nominal da página, e o último também coincide com o epoch UTC do mapa. Não foi localizado contrato explícito do campo `DataHora` em `DadosHidrometeorologicosGerais` nem vínculo público entre seu backend e o da página.
3. **Ainda pendente:** continuidade física/zero da régua, sensores e revisões, horários de recepção/publicação, cobertura histórica da convenção e versões de dados efetivamente disponíveis a cada emissão passada.
4. **Nenhuma flag de elegibilidade, modelo, script compartilhado ou dado anterior foi alterado.** A descoberta permite que o responsável pelo ledger avalie uma fonte alternativa explicitamente documentada, mas este lote não autoriza remover bloqueios nem promover modelos.

## Preservação

`manifest.json` cataloga as respostas brutas finais, URLs, instantes e SHA-256. `request-log.json` conserva o histórico de requisições: duas respostas intermediárias de formulário sem dados foram substituídas pela repetição posterior e estão marcadas `retained=false`; os HTMLs finais com dados e evidências não foram substituídos. Não se declara preservado o conteúdo das duas respostas intermediárias descartadas. Cookies de sessão foram mantidos somente em memória pelo cliente; não se usaram credenciais.

`validation.json` verifica hashes e comparação; `artifact-hashes.json` cobre a entrega. Scripts locais servem apenas à reprodutibilidade deste lote; não foram incorporados ao pipeline. Não foram enviadas mensagens externas.
