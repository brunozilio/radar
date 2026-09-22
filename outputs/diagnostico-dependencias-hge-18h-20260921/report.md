# Dependência da previsão HGE das vazões futuras

Emissão preservada: 2026-09-21T21:02:09.728188+00:00; origem 2026-09-21T18:00:00-03:00. Os 14 pontos foram reproduzidos com erro máximo 7.11e-15 m, usando 263 referências a blobs verificados. O estado hidrológico final também foi reproduzido; erro máximo do balanço numérico 2.84e-14 mm.

## Resultado principal

Às 08h de 22/09, o HGE publicado experimentalmente projeta 30.67 m a partir de 20049.67 m³/s. A contribuição roteada de vazões futuras estimadas de 14 de Julho é 18119.61 m³/s (90.37% do total). Não há contribuição histórica dessa usina nesse alvo: todos os pesos já usam entradas estimadas para a origem ou depois dela.

O escoamento local responde por 827.74 m³/s e inclui água armazenada de chuva passada. Zerar somente a chuva incremental futura resulta em 30.63 m, diferença de 0.034 m. Isso NÃO zera o escoamento local nem a chuva das bacias a montante.

Manter as vazões de montante nos últimos valores conhecidos resulta em 16.31 m neste contrafactual. A diferença de 14.36 m identifica sensibilidade às estimativas futuras; não comprova que persistência seja melhor. O experimento histórico de mistura com persistência já havia piorado o erro nas vazões altas. Nenhuma emissão foi substituída.

## Evolução da dependência

| Alvo BRT | Antecedência real (h) | Peso Julho com entrada estimada | HGE (m) | Sensibilidade sem chuva local nova (m) | Sensibilidade persistência montante (m) |
|---|---:|---:|---:|---:|---:|
| 21/09 19h | 0.9640 | 0.1765 | 15.241 | 15.237 | 14.736 |
| 22/09 00h | 5.9640 | 0.6116 | 22.752 | 22.715 | 16.851 |
| 22/09 06h | 11.9640 | 1.0000 | 29.686 | 29.648 | 16.543 |
| 22/09 08h | 13.9640 | 1.0000 | 30.669 | 30.635 | 16.306 |

A decomposição aditiva vale para vazão, não para nível, pois a curva de conversão é não linear. Peso de entradas estimadas não representa probabilidade. Leituras históricas incluem limitações de atraso, preenchimento por último valor e revisões do pipeline preservado. As sensibilidades não são limites físicos nem intervalos de confiança. Não foi treinado ou promovido um modelo, nem gerada evidência de precisão prospectiva.

Próxima prioridade: previsão de defluências da cascata e sua validação em eventos separados, com documentação de armazenamento/regimes. Ajustar PET ou somente a chuva local não resolve a origem predominante desta extrapolação.
