# Frequência de ausência do bloco Carreiro

Contrato confirmado: **18 = nível H de Passo Carreiro ANA 86500000, 19–23 = dH0.5, dH1, dH2, dH4 e dH8**, na ordem. O nível está em metros; dH são taxas em m/h nominal. Esse bloco não contém vazão Q nem chuva da região Carreiro. A reconstrução independente dos seis campos, a partir dos históricos de nível, reproduziu exatamente 154.944 células dos perfis A/B, inclusive NaNs.

Ambos os perfis usam atraso de Carreiro de 30 minutos e seleção do registro mais recente até a consulta, com idade pós-consulta ≤15 minutos. Não se pula um último valor inválido. Os blocos A/B são idênticos neste acervo, embora outros campos/âncoras possam diferir entre perfis. Portanto suas contagens não constituem amostras independentes.

**O treino atual nunca vê o bloco Carreiro ausente:** todas as 24 máscaras fase×horizonte, reconstruídas de forma independente, exigem os primeiros 24 campos completos nos dois perfis. Isso vale para os blocos A, B e misto, inclusive no recorte de alvos ≥7m. Medição de frequência foi feita antes de qualquer inspeção de resultados do candidato proposto.

Nas 12.912 origens anteriores ao corte final, cada perfil tem 11.987 blocos completos, 90 parcialmente ausentes e 835 inteiramente ausentes. São 925 origens com alguma ausência (7,16%). Ausência completa significa seis campos não finitos; parcial significa de um a cinco. Na prática, H ausente torna todas as derivadas ausentes, enquanto uma observação anterior ausente pode afetar apenas parte das derivadas.

## Avaliação já congelada

As contagens abaixo valem em A e B para alvos de cheia conhecidos. Alvos desconhecidos são contabilizados separadamente no CSV, não convertidos em cheia/erro/acerto.

| Fase/horizonte | Alvos ≥7m | Completo | Parcialmente ausente | Seis ausentes |
|---|---:|---:|---:|---:|
| Validation, todos os 12 horizontes (por horizonte) | 28 | 28 | 0 | 0 |
| Test, 1h | 237 | 144 | 16 | 77 |
| Test, 6h | 237 | 140 | 15 | 82 |
| Test, 12h | 237 | 140 | 9 | 88 |

Ao exigir também base Muçum finita, há 236 pares de cheia; o caso excluído em cada horizonte está na categoria dos seis campos Carreiro ausentes. Assim, em 1/6/12h os pares com bloco todo ausente são 76/81/87. Essa é uma condição de disponibilidade, não uma atribuição causal de erro.

No calendário inteiro de test, 1/6/12h têm respectivamente 1.967/1.962/1.956 origens, com 544 blocos totalmente ausentes e 16 parcialmente ausentes em cada horizonte. Na validation, as contagens inteiramente ausentes são 286/281/275 e as parciais 53, para 6.551/6.546/6.540 origens. A diminuição do calendário decorre da fronteira temporal de cada horizonte, sem mover alvos para fora do período.

## Escopo e limites

Foram feitas 299 verificações, sem ajuste, inferência, consulta de rede ou alteração dos dados. O código `audit.py` não importa helpers operacionais. Conferiu o manifesto do experimento misto, a atribuição PCG64(57), os índices/cortes/máscaras e o alinhamento das origens com o calendário congelado. `training-missingness.csv` tem 144 grupos; `evaluation-missingness.csv`, 288, distinguindo agenda, alvos observados/desconhecidos, pares e cheias.

O candidato PCG64(58) que oculta aleatoriamente 25% das origens não foi auditado nesta etapa. Corrupção aleatória de linhas não reproduz a duração, a dependência temporal ou a causa das falhas reais; tampouco fornece observações novas ou prova generalização. Eventual ganho em períodos já examinados continua sendo desenvolvimento, sem promoção. Comparar estas contagens à taxa de ocultação não valida automaticamente a taxa escolhida.

`finalize.py` verifica os hashes de entrada e grava o manifesto dos artefatos próprios. Fontes e treinamentos prévios permanecem intactos; não executar novamente após congelamento externo sem autorização.
