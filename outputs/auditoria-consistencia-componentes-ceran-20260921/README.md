# Defluência zero versus componentes — CERAN/ONS

Auditoria local de 21/09/2026, nos 18 CSVs mensais preservados de abril/2025 a setembro/2026. **A regra sinaliza exatamente três registros: Monte Claro em 22/07/2026 às 07h, 08h e 09h.** Foram lidas 38.764 linhas; não há duplicação de usina/timestamp. Fontes, hashes, valores e linhas ficaram preservados. Não houve download, treino, máscara, correção nem alteração de modelos.

## Regra aplicada

Defluência total exatamente zero **e** turbinada, vertida e outras estruturas todas finitas **e** soma dessas três parcelas maior que 1 m³/s. O limiar de 1 m³/s é diagnóstico explícito solicitado, não tolerância ou reprovação oficial ONS. Qualquer componente ausente/não finita torna a soma desconhecida; não foi substituída por zero. Não se incluíram afluência, transferência ou vertida não turbinável na soma.

A [rotina ONS RO-AO.BR.02 Rev.08](https://www.ons.org.br/%2FMPO%2FDocumento%20Normativo%2F4.%20Rotinas%20Operacionais%20-%20SM%205.13%2F4.3.%20Rotinas%20P%C3%B3s-Opera%C3%A7%C3%A3o%2F4.3.2.%20Apura%C3%A7%C3%A3o%20de%20Dados%2FRO-AO.BR.02_Rev.08.pdf), p.3, define QDEF=QTUR+QVER+QOTR. O [dicionário ONS](https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/dados_hidrologicos_ho/DicionarioDados_DadosHidrologicosHorarios.pdf) identifica os quatro campos em m³/s, permitindo zero e nulo. Foram consultados os documentos primários já preservados e seus hashes, sem ampliar pesquisa. A regra vale para essas colunas ONS; não foi transferida às parcelas das páginas CERAN.

## Distribuição temporal

Corte pelo timestamp original: antes de 01/07/2026 00:00 versus a partir dessa data, incluindo o trecho disponível de 21/09/2026. Não é apenas a janela de teste terminada em 20/09.

| Usina | Registros antes / depois | Q=0 antes / depois | Regra positiva antes / depois |
|---|---:|---:|---:|
| Castro Alves | 10.943 / 1.978 | 0 / 0 | 0 / 0 |
| Monte Claro | 10.942 / 1.979 | 0 / 3 | 0 / 3 |
| 14 de Julho | 10.943 / 1.979 | 0 / 0 | 0 / 0 |

## Os três registros

Arquivo original: outputs/mucum-propagacao-2026-09-21/raw/DADOS_HIDROLOGICOS_HO_2026_07-ceran.csv. Linhas incluem o cabeçalho como linha 1; valores em m³/s.

| Timestamp original | Linha | Qdef | Qtur | Qvert | Qoutras | Soma |
|---|---:|---:|---:|---:|---:|---:|
| 22/07/2026 07:00 | 2000 | 0 | 0 | 0 | 6 | 6 |
| 22/07/2026 08:00 | 2001 | 0 | 0 | 0 | 6 | 6 |
| 22/07/2026 09:00 | 2002 | 0 | 0 | 0 | 6 | 6 |

Portanto os três zeros de Monte Claro são cobertos pela regra geral, sem depender do tamanho do erro do modelo. O conflito não identifica qual coluna está incorreta, nem fornece automaticamente uma defluência substituta. Outras parcelas originais estão no CSV integral da extração; não somamos vertida não turbinável novamente.

## Componente desconhecida

Há um registro com componente ausente: Castro Alves, 23/02/2026 07h, arquivo fevereiro/2026 linha 1208, Qdef=72, Qtur=53, Qvert=0 e Qoutras vazia. A soma permanece desconhecida e não recebe a sinalização acima, pois Qdef não é zero. Não há Q=0 com componente desconhecida neste acervo. zero-with-unknown-components.csv fica sem registros; unknown-components-all-defluences.csv preserva o caso Castro.

## Limites e artefatos

O catálogo ONS informa dados dos agentes sujeitos a lacunas/revisões e sem consistência assegurada. Ausência desta sinalização não equivale a dado aprovado. A auditoria não cobre todos os tipos de erro, zeros afluentes, sentinelas, atrasos ou saltos. O fato de todos os casos estarem depois do corte não autoriza apresentar uma mudança de política escolhida após esta inspeção como teste independente.

Timestamps permanecem como publicados, sem deslocamento. A norma usa Brasília; o vínculo do exportador histórico e o tratamento de 23:59 continuam com as ressalvas anteriores. Nenhum dos três casos fica em uma fronteira de fuso ou de dia que altere a partição solicitada.

- flagged-complete-components.csv: três linhas, todas as colunas originais, soma, diagnóstico e localização/hash da fonte.
- zero-defluence-all.csv: todos os zeros do acervo (os mesmos três).
- monte-claro-2026-07-22.csv: dia completo, 24 registros, para contexto sem recorte seletivo.
- flagged-by-date.csv: contagem diária/usina.
- summary.json: regra e contagens incluindo zeros explícitos.
- source-manifest.json e documentation-manifest.json: fontes/dicionário/norma com hashes.
- audit.py: reprodução local, gravando somente nesta pasta.
