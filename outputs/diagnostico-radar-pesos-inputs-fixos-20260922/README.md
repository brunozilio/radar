# Variação de pesos nos mesmos inputs

Comparação descritiva de dois conjuntos de modelos Radar já emitidos. Nenhum ajuste ou previsão nova foi registrada. Nas linhas abaixo, ambos os modelos recebem exatamente os mesmos180campos e a mesma base das02h. O valor do modelo das01h é um contrafactual não emitido.

| h nominal | Alvo a partir das02h | Modelo anterior | Modelo atual emitido | Efeito da troca de pesos |
|---:|---|---:|---:|---:|
| 1 | 2026-09-22T03:00:00-03:00 | 18.8772 | 18.8783 | +0.0010 |
| 2 | 2026-09-22T04:00:00-03:00 | 19.0480 | 19.0887 | +0.0407 |
| 3 | 2026-09-22T05:00:00-03:00 | 19.2428 | 19.2878 | +0.0450 |
| 4 | 2026-09-22T06:00:00-03:00 | 19.3636 | 19.4420 | +0.0784 |
| 5 | 2026-09-22T07:00:00-03:00 | 19.1065 | 19.2283 | +0.1217 |
| 6 | 2026-09-22T08:00:00-03:00 | 18.9710 | 19.0513 | +0.0803 |
| 7 | 2026-09-22T09:00:00-03:00 | 18.7014 | 18.6894 | -0.0120 |
| 8 | 2026-09-22T10:00:00-03:00 | 18.7028 | 18.6442 | -0.0586 |
| 9 | 2026-09-22T11:00:00-03:00 | 18.5025 | 18.5812 | +0.0787 |
| 10 | 2026-09-22T12:00:00-03:00 | 18.3171 | 18.1516 | -0.1655 |
| 11 | 2026-09-22T13:00:00-03:00 | 18.1224 | 18.1541 | +0.0317 |
| 12 | 2026-09-22T14:00:00-03:00 | 17.9848 | 17.9608 | -0.0240 |
| 13 | 2026-09-22T15:00:00-03:00 | 17.6970 | 17.6467 | -0.0503 |
| 14 | 2026-09-22T16:00:00-03:00 | 17.4946 | 17.4789 | -0.0157 |

As28diagonais (modelo/origem correspondentes) reproduzem exatamente as emissões originais. Parâmetros, versão declarada, runtime e corte são iguais entre os conjuntos.

Isso mede apenas o efeito computacional de trocar os modelos salvos com os inputs fixos. Não prova qual previsão é melhor. Aplicar pesos antigos a outra configuração de atraso pode criar desalinhamento; não foi escolhido para operação.

Ao comparar origens01h/02h no mesmo horizonte nominal, os alvos são diferentes. Não somar esta tabela à revisão por mesmo alvo sem uma decomposição que preserve os horizontes. H13/14 reutilizam parâmetros de12h e não são validação adicional de precisão.
