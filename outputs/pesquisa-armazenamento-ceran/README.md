# Armazenamento dos reservatórios CERAN — pesquisa delimitada

Consultado em 21/09/2026. Encontrados cadastro oficial atual ONS, três fichas técnicas CERAN e PAE Monte Claro emitido após maio/2024. **Não foi obtida curva cota-volume completa com vigência pós-avarias.** Não houve alteração de modelos, interpolação, cálculo de armazenamento observado ou promoção de candidatos.

## Números utilizáveis, com limites de vigência

O [cadastro público ONS de reservatórios](https://dados.ons.org.br/dataset/reservatorio) informa os seguintes valores no CSV coletado hoje. O dicionário confirma cota em m e volumes em hm³; 1 hm³ equivale a 1 milhão de m³. São parâmetros cadastrais, não observações de volume disponível no instante.

| Reservatório | ID / código ONS | Cota mín./máx. normal (m) | Vmín./Vmáx. (hm³) | Vútil publicado (hm³) | Vmáx.−Vmín. calculado (hm³) |
|---|---|---:|---:|---:|---:|
| Castro Alves | JIUHCA / 97 | 239 / 240 | 87 / 92 | **4,600** | **5,000** |
| Monte Claro | JIUHMC / 98 | 147 / 148 | 10,100 / 11,280 | **1,450** | **1,180** |
| 14 de Julho | JIUHQJ / 99 | 103 / 104 | 50,470 / 55,180 | **4,710** | 4,710 |

**Contradições cadastrais preservadas:** diferença de 0,400 hm³ em Castro e −0,270 hm³ em Monte entre o volume útil publicado e a diferença dos limites. Não escolher um deles, corrigir ou atribuir a arredondamento sem confirmação. `cadastro-three-reservoirs.csv` mantém campos originais e cálculos de revisão separados. A coluna `res_id` no CSV corresponde aos identificadores das séries horárias; o dicionário simplificado nomeia esse identificador como `id_reservatorio`.

O catálogo ONS explicita que **não fornece histórico deste cadastro**, sendo atualizado diariamente. Recursos CSV atualizados em 21/09/2026, segundo metadados; `dat_entrada` significa entrada da usina em operação, não vigência do volume/curva. Logo, não aplicar automaticamente essa fotografia cadastral a 2020, 2023, maio/2024 ou à execução das obras.

As fichas CERAN hospedadas em caminhos de maio/2022, sem revisão/data técnica explícita dentro do PDF, fornecem referências de projeto anteriores às avarias:

| Ficha CERAN | Volume no NA máximo normal | Área nesse nível | Nível máximo normal |
|---|---:|---:|---:|
| [Castro Alves](https://ceran.com.br/wp-content/uploads/2022/05/1_ficha_tecnica_CA.pdf) | 91,77 hm³ | 5,00 km² | 240 m |
| [Monte Claro](https://ceran.com.br/wp-content/uploads/2022/05/1_ficha_tecnica_MC.pdf) | 11,28 hm³ | 1,40 km² | 148 m |
| [14 de Julho](https://ceran.com.br/wp-content/uploads/2022/05/0_ficha_tecnica_14J.pdf) | 55,00 hm³ | 5,07 km² | 104 m |

Esses volumes são **totais no nível normal**, não volumes úteis. As diferenças frente ao cadastro ONS permanecem explícitas. A página comercial CERAN de 14 de Julho informa área genérica de 6 km², enquanto a ficha associa 5,07 km² à cota 104 m; não uniformizar as duas. Área em uma cota não fornece curva de armazenamento, nem autoriza extrapolação linear para cheia.

## Documento posterior à cheia e curvas ainda ausentes

O [PAE Monte Claro, 1112-MCL-RT-PAE-0001-3, emissão 07/08/2024](https://ceran.com.br/wp-content/uploads/2024/08/Plano-de-Acao-de-Emergencia-UHE-Monte-Claro.pdf), p.12, repete **11,28 hm³ e 1,40 km² no NA máximo normal**, e mínimo normal 147 m-IBGE. A data posterior à cheia não comprova, por si, levantamento batimétrico realizado depois dela nem representa toda a evolução de obras até 2026.

A p.42, quadro 8, confirma que o estudo usou curva cota-volume de Monte Claro e informações equivalentes de Castro Alves/14 de Julho. Cita arranjo baseado na RPS 2022/projeto As Built e documento hidrológico **1112-MCL-AP-PAE-0006**. Não foi encontrada no PDF a tabela numérica completa da curva ou coeficientes com intervalo de validade. O documento é síntese de estudo de ruptura hipotética, não série operacional nem calibração para previsão rotineira.

As três fichas e as páginas 12/42 do PAE foram renderizadas e conferidas visualmente. Não se adotaram vazões de projeto ou cotas maximorum como limites físicos para eliminar extremos.

## Regimes após maio/2024: acervo reutilizado

Sem repetir downloads, foram referenciadas as fontes primárias já preservadas em `outputs/historico-vazoes-ceran/` e `outputs/pesquisa-castro-20260921T204404Z/`:

- ONS, 09/05/2024: perda de dados/voz em 01/05, dano no vertedouro livre de 14 de Julho em 02/05, dados medidos e/ou estimados enviados pela operadora. Não identifica a origem de cada valor do arquivo horário.
- CERAN, 04/05/2026: recuperação da cota operacional de 14 de Julho em **dezembro/2024**, obras concluídas em **março/2025**; Monte Claro teve casa de força inundada e recuperada. Não publica curva de armazenamento por etapa.
- LPIA FEPAM 00424/2025: Castro Alves com deplecionamento temporário autorizado de até 3 m, cota mínima de até 237 m; sem alteração permanente prevista da soleira/níveis. Essa licença autoriza condições e não comprova datas/níveis praticados. Validade impressa até 12/09/2026; renovação não examinada.
- CERAN, 06/07/2026: obras de Castro acima de 80% de execução. Não confirma conclusão nem regime efetivo em setembro.

Separar pré-avaria, transição, restauração e obras quando as datas efetivas forem documentadas. O cadastro diário atual não resolve essas vigências.

## Níveis históricos já pareáveis e horários

A série pública ONS `dados_hidrologicos_ho` já baixada contém `val_nivelmontante` e `val_niveljusante`, ambos em m, e `val_volumeutil` em **percentual**. As linhas compartilham `id_reservatorio` e `din_instante` com Q/I. O inventário local não baixa nenhum mês novamente:

| Acervo abril/2025–21/09/2026 | Linhas | Montante presente | Volume percentual presente |
|---|---:|---:|---:|
| Castro Alves | 12.921 | 12.921 | 8.338 |
| Monte Claro | 12.921 | 12.921 | 12.921 |
| 14 de Julho | 12.922 | 12.921 | 12.561 |

Também inventariados julho/2020, setembro/2023 e maio/2024, com cobertura por variável e arquivo em `historical-level-inventory.json`. Não confundir contagem de linhas existentes com ausência de horas: lacunas de calendário continuam documentadas nos acervos anteriores. No pico de maio/2024 há queda grave de cobertura das três usinas já auditada.

No acervo 2025–2026, percentuais chegam abaixo de 0 e acima de 100 (Castro −100 a 800,8; Monte −18,85 a 732,25; Julho −99,86 a 617,78). Esses valores foram apenas inventariados, sem invalidar ou cortar: correspondem a uma escala de volume útil operacional e exigem curva/vigência/QC, não à fração de toda a capacidade geométrica limitada automaticamente a 0–100%.

A norma primária já preservada **RO-AO.BR.02 Rev.08, vigência 02/07/2024**, p.3, diz que o ONS obtém percentual útil a partir de tabelas cota-volume fornecidas pelos agentes. Na p.5 usa horário oficial de Brasília e esclarece que validação horária não é tratada nessa rotina. O dicionário do exportador descreve 01h como fim do intervalo 00:00–00:59; interpretação dos registros 23:59 e vínculo preciso de versões históricas continuam pendentes. Na p.9 a agregação diária usa **nível montante da hora 24**, mas **média das 24h para afluência/defluência**: não parear dados diários dessas grandezas como se fossem todos simultâneos ou todos médias.

## Uso defensável e próximos dados necessários

É possível examinar níveis e Q/I da mesma usina e timestamp, preservando origem, revisão, atraso e regime. Ainda não se deve converter o percentual histórico em hm³ com o cadastro de hoje, fabricar curva linear por dois limites, ou calcular tempo de retenção dividindo volume total por uma vazão pontual.

A relação de conservação deve usar variação de armazenamento entre instantes coerentes e fluxos integrados no intervalo, além de transferências e demais termos pertinentes. A afluência ONS pode ser calculada por balanço; usá-la para validar esse mesmo balanço pode ser circular. Não inferir armazenamento causal de `I−Q` pontual, somar afluências/defluências em cascata ou desconsiderar contribuições laterais e propagação.

Próximo lote prioritário, ainda não executado: tabela cota-área-volume/coeficientes enviados ao SADHI por cada agente, cadastro com datas de vigência, batimetrias/RPS e projeto As Built citados no PAE, e cronologia efetiva de deplecionamento/recomposição. Em seguida, conciliar as divergências do cadastro antes de qualquer balanço quantitativo. Nenhuma mensagem externa foi enviada.

## Proveniência e falhas

Respostas novas, URLs, data UTC, status e hashes: `manifest.json` e `raw/`. Acervo reutilizado e hashes: `reused-source-manifest.json`; URLs/coleta originais permanecem nos manifestos das pastas de origem. Cadastro ONS: Creative Commons Atribuição; documentos CERAN não exibem licença aberta de redistribuição identificada, preservados localmente para auditoria.

Buscas localizaram CD-OR.AS.JAC revisões 25/26, mas os URLs públicos consultados retornaram **404** (incluindo alternativa canônica da Rev.25). Os resultados indexados não foram tratados como PDFs recuperados/verificados. Não foram obtidas curvas completas, vigência operacional por dia, medições de armazenamento independentes ou confirmação do datum altimétrico comum entre réguas distintas.
