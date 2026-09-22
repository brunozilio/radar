# Insumos observados de julho de 2020: levantamento delimitado

Foram consultadas oito estações públicas ANA de 04 a 13/07/2020: três níveis auxiliares e o maior peso de cada uma das cinco regiões de chuva. A janela cobre as origens extremas previamente identificadas em07/07 e12/07; não é seleção de acertos de um modelo. Antes dos GETs,190 XMLs existentes dessas estações foram inspecionados e não continham registros nessa janela.

As oito respostas HTTP200 estão preservadas com URL, horário, headers e SHA256. São 2,383 registros, conferidos campo a campo entre XML e JSONL, sem preenchimento, mudança de horário ou descarte dos valores/QC brutos. Não foi montada matriz ou ajustado modelo. Muçum e ONS foram reaproveitados por referência, sem novas consultas.

| Estação | Registros | Nível aprovado | Chuva aprovada | Cadência modal |
|---|---:|---:|---:|---|
| 86060010 | 213 | 0 | 213 | 3600 s |
| 86125050 | 0 | 0 | 0 | None s |
| 86160000 | 924 | 905 | 818 | 900 s |
| 86450000 | 46 | 46 | 46 | 3600 s |
| 86472000 | 960 | 911 | 960 | 900 s |
| 86472600 | 0 | 0 | 0 | None s |
| 86479000 | 240 | 240 | 240 | 3600 s |
| 86500000 | 0 | 0 | 0 | None s |

## Lacunas relevantes

Santa Tereza86472600, Passo Carreiro86500000 e o posto principal Prata-Turvo86125050 retornaram ausência explícita de dados. HTTP200 não implica observações presentes.

Linha José Júlio86472000 tem todos960 timestamps de15min, mas só911 níveis aprovados:41 são suspeitos e oito estão vazios. A chuva está aprovada nas960 linhas. A diferença entre existência de linha e disponibilidade de nível foi mantida.

Nas nove origens de resposta>8,09m em12h já identificadas no acervo Muçum, os seis níveis necessários ao bloco Linha José Júlio (consultaO−30min e recuos0,5/1/2/4/8h, idade máxima15min após consulta) estão disponíveis em9/9 origens. As54 consultas têm rastros em extreme-origin-linha-trace.csv. Isso não certifica Q/I, chuva regional, régua ou o futuro modelo.

O posto86450000 possui apenas46 chuvas, com ausência de linhas de05/07 00h a09/07 09h e de11/07 00h a13/07 23h. O posto Tainhas86160000 tem36 timestamps faltantes durante07–08/07 e106 chuvas vazias entre924 registros; apenas818 chuvas aprovadas. Alto Antas86060010 tem27 horários ausentes; Carreiro86479000 tem240/240 horários e chuvas aprovadas.

## Limite espacial da amostra

| Região | Soma máxima dos pesos dos postos consultados com alguma chuva aprovada |
|---|---:|
| Baixo Antas | 0.367052 |
| Carreiro | 0.527301 |
| Prata-Turvo | 0.014925 |
| Alto Antas | 0.278327 |
| Tainhas | 0.841530 |

Esses valores são tetos espaciais hipotéticos, não cobertura temporal de janelas nem chuva regional. Não renormalizar pesos ou tratar falta como zero. As demais estações com peso positivo precisam ser examinadas antes de formar os75 campos regionais.

## Limites e próximo passo

Os timestamps ingênuos e valores originais foram preservados. Datum/fuso, publicação histórica e comparabilidade dos regimes continuam pendentes. O acervo ONS previamente auditado contém zeros reportados suspeitos em Monte Claro/14 de Julho no pico de08/07; esta coleta não os corrige nem certifica. As origens extremas têm dados correntes de Q/I segundo a auditoria anterior, mas a matriz completa e a propagação de faltas pelos atrasos ainda precisam de verificação.

Há dados úteis, mas lacunas importantes. O próximo passo de preparação exige completar as estações de chuva, preservar filtros QC explícitos e auditar valores/lags das usinas. Este lote2020 já é desenvolvimento inspecionado; não é um novo holdout. As janelas2021/2022 reservadas separadamente não foram consultadas ou usadas aqui.

Reprodução local: audit.py lê os oito XMLs; finish.py confere campos, hashes, tetos e rastros. collect.py registra cada tentativa e não repete automaticamente uma requisição com sidecar existente.
