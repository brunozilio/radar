# Vazões CERAN/ONS — junho de 2024

Foi adquirido um único [CSV mensal oficial ONS](https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/dados_hidrologicos_ho/DADOS_HIDROLOGICOS_HO_2024_06.csv), listado no catálogo preservado: HTTP200, 15.510.508 bytes. Nenhuma retentativa. A seleção conserva 2.160 linhas brutas, 720 por usina, sem arredondar horários ou reparar valores. `source_record_index` é o índice **zero-based da linha de dados**, excluindo o cabeçalho. `23:59` permanece literal (30 por usina).

Todas as afluências e defluências selecionadas são finitas e positivas; isso não significa controle de qualidade oficial aprovado. A disponibilidade sob atraso declarado de 60min/idade máxima de 90min cobre 3.024 consultas nas 168 origens de 15–21/06, incluindo atrasos de 1/2/4/8h. Não comprova publicação em tempo real em 2024. O mês completo fornece margem anterior à janela sem preencher lacunas.

| Usina | Registros de 15–21/06 | Diferença absoluta Qdef−(Qtur+Qvert+Qoutras)>1m³/s |
|---|---:|---:|
| 14 de Julho | 168 | 37 |
| Monte Claro | 168 | 0 |
| Castro Alves | 168 | 0 |

Em 14 de Julho, as diferenças na semana variam de −169 a +1m³/s; o primeiro registro com diferença maior que 1 em módulo é 19/06 às18h. No mês completo são250 registros sinalizados, com diferença mínima−173m³/s. As consultas do modelo alcançariam registros sinalizados em43 das168 origens, porque usam também instantes passados. São denominadores diferentes, não contagens conflitantes.

A soma segue a definição da rotina ONS RO-AO.BR.02 Rev.08 já preservada, sem somar afluência, transferência ou vertida não turbinável. O limiar de1m³/s é diagnóstico, não reprovação oficial. O conflito não identifica qual campo deve ser corrigido. Nenhum valor foi substituído pela soma.

Outros fatos descritivos: em14deJulho, Qdef=Qafluente nas720linhas mensais; MonteClaro tem vazão turbinada zero nas720linhas. Isso não prova vazão medida, estimativa, erro, inexistência de armazenamento ou equivalência de regime com2025/26. O contexto documentado de avarias pós-maio permanece relevante, mas não determina sozinho a interpretação de cada campo.

A verificação independente em `outputs/verificacao-qi-radar-junho2024-20260922/` reconstruiu as2.160linhas e cada uma das3.024consultas por busca do maior timestamp elegível, com17.296checks. Nenhum modelo foi treinado ou aplicado. Nenhuma alteração operacional. `artifact-hashes.json` sela a aquisição original; `supplement-manifest.json` sela este relatório e referências adicionadas.

Decisão: conservar estes dados como fonte experimental com sinalizações explícitas. Uma matriz/experimento de junho exige política prévia para campos conflitantes, níveis ausentes e regime pós-avaria, comparada de forma simétrica; não introduzir correções escolhidas a partir do erro de previsão.
