# Acervo auditado — cheia de setembro de 2023

Coleta pública em 21/09/2026. Uso de pesquisa, sem interpolação, treinamento, alteração de modelos ou alocação de teste. Este evento já estava exposto em amostra ANA de 05/09/2023 e documentos SGB consultados; **não é um holdout novo ou cego**.

## Inventário e cobertura

| Série | Identificador | Linhas disponíveis | Cobertura esperada | Máximo defluente |
|---|---|---:|---:|---:|
| ONS Castro Alves | JIUHCA / 97 | 714 | 720 horas | 9.636 m³/s — 04/09 19h |
| ONS Monte Claro | JIUHMC / 98 | 714 | 720 horas | 14.807 m³/s — 04/09 20h |
| ONS 14 de Julho | JIUHQJ / 99 | 714 | 720 horas | 15.114 m³/s — 04/09 22h |
| ANA Muçum | 86510000 | 2.364 registros únicos | 2.880 intervalos de 15 min | Nível aprovado máximo 21,79 m |

Horários acima são os originais sem fuso. Todas as três usinas têm **96/96 registros de 03 a 06/09**, com afluência e defluência presentes durante o pico. As seis horas ausentes em cada usina coincidem: 18/09 02–03h e 07–09h; 19/09 16h. Não há Q/I nulo, zero ou negativo nas 714 linhas de cada usina. Isso não equivale a certificação das medições.

ANA: 2.023 níveis finais aprovados, 11 suspeitos, 330 registros sem nível final disponível/QC e 516 intervalos sem registro. A partição soma 2.880. Somente níveis finais aprovados foram normalizados de cm para m. Suspeitos e indisponíveis estão separados, com todas as variáveis/QC mantidas no JSONL e XML originais. Dois valores de `NivelSensor` foram reprovados pela fonte; esses números não viraram nível final aprovado.

O último nível aprovado antes da interrupção é **04/09 19:30, 21,79 m**; o primeiro depois é **08/09 14:15, 6,61 m**. Os 11 níveis suspeitos ocorrem antes da interrupção, entre 04/09 16:45 e 19:15. Não há nível aprovado no pico. A marca retrospectiva SGB **26,108 m, aproximadamente 05/09 02:30**, foi nivelada em **08/09/2023**; não foi inserida na série nem tratada como telemetria disponível na hora.

## Sinalização semântica

Aplicou-se apenas revisão, sem substituir/excluir números. Na convenção ONS, defluente fecha com turbinada + vertida + outras estruturas; a parcela vertida não turbinável não se soma novamente. Afluência é outra grandeza, associada ao balanço hidráulico, e não deve ser forçada a igualar a defluência. O catálogo público informa dados horários reportados pelos agentes, não consistidos pelo ONS e sujeitos a revisão.

Uma linha merece revisão: **Castro Alves, 01/09 21h**, Qdef=164, Qtur=159, Qvert=0, Qoutras=18 m³/s; residual Qdef−soma=−13 m³/s. O limiar absoluto >1 usado para inventariar resíduos **não é tolerância oficial e não torna a linha inválida**. Não há zero defluente com componentes positivos neste mês. Não se aplicou filtro de extremos, correção de balanço, teste de outlier estatístico nem seleção pelo erro de modelos.

As vazões superiores a 9.999 m³/s estão preservadas. Sua existência não prova que um valor particular de 9.999 em outro período seja sentinela ou vazão legítima: **essa semântica continua não documentada**. Não se presumiu igualdade entre o detalhamento dos componentes CERAN e ONS.

## Horários, causalidade e admissibilidade

- **Submodelo experimental de vazões de 14 de Julho:** o conjunto tem alvo Q e entradas Q/I a montante presentes no evento extremo, portanto é candidato útil para pesquisa histórica, sujeito à revisão da linha sinalizada e ao regime operacional. Não depende de haver nível de Muçum no pico. Nenhum modelo foi treinado aqui e não se autoriza promoção.
- **Causalidade:** construir cada origem de previsão usando somente intervalos encerrados antes dessa origem, acrescidos de latência explicitamente presumida. Nunca usar Q/I futuros como entradas históricas, afluência futura “conhecida” por vir do arquivo mensal, interpolação atravessando lacunas ou seleção de latências pelo teste. A data de coleta é 2026, e o Parquet apresenta Last-Modified de fevereiro de 2025; não recupera a versão exata disponível em setembro de 2023. Sem arquivo de publicações/recebimentos original, o estudo continua retrospectivo, mesmo ao simular uma latência conservadora.
- **Convenção de tempo:** preserva-se `din_instante`. Dicionário ONS descreve a hora como fim do intervalo. A norma RO-AO.BR.02 Rev.08 (vigência 02/07/2024) usa horário oficial de Brasília; isso não comprova sozinho o contrato do exportador de 2023. Há 30 registros 23:59 por usina; a coluna derivada interpreta 23:59 como 24:00, claramente marcada como hipótese ainda não verificada. A contagem de 720 horas e os grupos de lacunas usam essa hipótese. UTC derivado presume America/Sao_Paulo. ANA também mantém o original e deriva UTC apenas supondo UTC−03; confirmação explícita do endpoint vigente segue pendente.
- **Validação de níveis:** não admissível como hidrograma completo ou avaliação do pico de Muçum. Trechos aprovados podem ser examinados com sua cobertura e QC explícitos; a marca nivelada é evidência retrospectiva separada. Não há curva-chave/seção com vigência 2023 neste lote.
- **Regime físico:** setembro de 2023 antecede avarias de maio de 2024 e intervenções posteriores nas usinas. Não pressupor a mesma relação propagação/armazenamento/controle no regime de 2026. Identificar regime e realizar análise de sensibilidade, sem promover por um ganho retrospectivo neste evento já inspecionado.

## Zero da régua e evidência documental

Os PDFs oficiais previamente coletados foram reutilizados por referência com SHA-256 conferido em `documentation-manifest.json`, sem novo download. A versão 19 do [relatório SGB de 2024](https://rigeo.sgb.gov.br/handle/doc/24939.21), páginas 15 e 18, informa a parada da PCD em 04/09/2023 19:30 e a marca nivelada 26,108 m (relatório SGIH 257170). Não constitui certificado de continuidade do zero da régua em todas as datas. A página 19 usa zero de 33,96 m para marcas de 2024. A [nota SGB versão 3, março de 2026](https://rigeo.sgb.gov.br/handle/doc/25578.3), página 12, informa zero ortométrico 33,985 m, referência PA008/MAPGEO2015, sem vigência detalhada que permita vinculá-lo automaticamente a setembro de 2023.

**Não foi localizada confirmação explícita do zero/referências, deslocamentos, reinstalações do sensor/régua ou vigência específica de setembro de 2023.** A diferença documental de 2,5 cm não foi classificada como arredondamento nem mudança física. A altitude genérica do inventário não deve ser confundida com zero da régua. Próxima fonte necessária: ficha de instalação/manutenção e nivelamento da estação 86510000, relatório SGIH 257170, referências RN e curvas/seções com datas; canais públicos SGB `alerta.taquari@sgb.gov.br` e ANA `hidro@ana.gov.br`. Nenhuma mensagem foi enviada.

## Arquivos e reprodutibilidade

- `source-manifest.json`: URLs públicas, coleta, status HTTP, headers, hash e cache utilizado; três XML ANA e Parquet ONS preservados em `raw/`. O XML de 05/09 foi reutilizado do acervo e os pedidos ANA novos cobrem 01–04 e 06–30/09, evitando baixar a mesma janela.
- `catalog.json`: contagens, variáveis, QC, lacunas e identificadores; `peak-coverage.json`: máximos com horários originais e cobertura do pico.
- `ana-mucum/`: níveis por QC, registros integrais e lacunas de 15 min; `ons-ceran-source-values.csv`: extração sem valores corrigidos; `ons-ceran-interpreted.csv`: colunas derivadas e hipóteses explícitas.
- `ons-missing-hours.csv`, `ons-semantic-review.csv`: lacunas e única linha de revisão; `ons-reservoir-inventory.csv`: contagem/nomes de todos os reservatórios no arquivo original para auditar seleção das três usinas.
- `audit.py` e `ana-helper-snapshot.txt`: auditoria local reproduzível. Dependências pandas/numpy e DuckDB 1.4.4; runtime temporário removido. `finalize.py` verifica hashes/contagens/conversão; `validation.json` registra verificações concluídas.
- Fontes de semântica, licença/atribuição ONS e revisões permanecem vinculadas ao acervo primário `outputs/pesquisa-qc-semantica-fontes/source-manifest.json`; não foi inferida licença ANA ausente no endpoint. `artifact-hashes.json` cobre os artefatos entregues.
