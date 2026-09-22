# Primeira comparação retrospectiva nas reservas2021/2022

Modelos e entradas foram fixados antes da inferência. Comparação120 observada versus120+2020; nenhum novo treino. Os modelos usam também treino posterior aos anos reservados: isto não reproduz uma previsão possível com somente dados disponíveis naquela época.

## Recorte de nível observado >=7 m

Acertos: erro absoluto <=0,50 m. O denominador inclui alvos observados sem previsão; MAE/máximo usam os pares disponíveis. Horas consecutivas e horizontes compartilham eventos e não são evidência independente.

| Período | Horizonte | Acertos controle→candidato / alvos | MAE controle→candidato (m) | Máximo controle→candidato (m) |
|---|---:|---:|---:|---:|
| 2021 | 1h | 11→11 / 11 | 0.0490→0.0608 | 0.1370→0.1434 |
| 2021 | 6h | 8→9 / 11 | 0.3474→0.2349 | 0.7555→0.6274 |
| 2021 | 12h | 6→10 / 11 | 0.4620→0.2649 | 0.7456→0.6157 |
| 2022 | 1h | 307→310 / 312 | 0.0739→0.0652 | 1.1085→0.9829 |
| 2022 | 6h | 194→218 / 312 | 0.6406→0.4714 | 3.7423→2.9726 |
| 2022 | 12h | 147→120 / 312 | 1.0272→1.0630 | 5.8169→4.8777 |
| pooled | 1h | 318→321 / 323 | 0.0731→0.0650 | 1.1085→0.9829 |
| pooled | 6h | 202→227 / 323 | 0.6306→0.4633 | 3.7423→2.9726 |
| pooled | 12h | 153→130 / 323 | 1.0079→1.0357 | 5.8169→4.8777 |

## Todos os horizontes, sem seleção

- 2021 / all: acertos melhoram/empatam/pioram em 8/1/3 horizontes; MAE melhora em 10/12; máximo piora em 7/12.
- 2021 / level_ge_7m: acertos melhoram/empatam/pioram em 7/3/2 horizontes; MAE melhora em 8/12; máximo piora em 6/12.
- 2022 / all: acertos melhoram/empatam/pioram em 9/0/3 horizontes; MAE melhora em 8/12; máximo piora em 0/12.
- 2022 / level_ge_7m: acertos melhoram/empatam/pioram em 8/0/4 horizontes; MAE melhora em 10/12; máximo piora em 0/12.
- pooled / all: acertos melhoram/empatam/pioram em 12/0/0 horizontes; MAE melhora em 10/12; máximo piora em 0/12.
- pooled / level_ge_7m: acertos melhoram/empatam/pioram em 9/0/3 horizontes; MAE melhora em 10/12; máximo piora em 0/12.

Nenhum modelo foi promovido. Percentuais pontuais históricos não satisfazem a meta: faltam evidência prospectiva certificada, tamanho amostral por horizonte, dez eventos independentes e incerteza apropriada à dependência temporal. A janela já foi vista; se estes erros forem usados para modificar modelos, passa a ser desenvolvimento e não um novo teste independente.

changes.csv contém todos os72 contrastes de período/subconjunto/horizonte, sem ocultar regressões. analysis.json preserva os piores casos de12h e hashes das entradas.
