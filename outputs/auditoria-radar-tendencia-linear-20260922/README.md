# Auditoria independente do componente linear de tendência

**5.982 verificações passaram**, sem divergência concreta. Foram conferidos os 24 bundles, 144 reaplicações dos controles e 96 saídas novas (linear isolado/híbrido, em 48 combinações de fase/horizonte/perfil), além das 1.440 métricas. Todas as previsões reaplicadas coincidiram exatamente nesta execução, inclusive as calculadas manualmente com os coeficientes Ridge. As 864 métricas dos três controles permaneceram idênticas às do experimento misto. Nenhum novo ajuste ou consulta de rede foi realizado.

## Procedência, amostras e equações

O protocolo preservado tem SHA-256 `523a56df3d6fe52a7ef856bf5f2d22be17f31a2b2f2f471a63d5592f23b2a613`. Os horários registrados de protocolo, pré-fit e conclusão estão ordenados; são metadados locais, não certificação externa do instante em que o otimizador iniciou. Manifestos e hashes de fontes/modelos foram conferidos antes e depois da auditoria.

As 24 máscaras foram reconstruídas dos cortes temporais e da interseção das entradas completas24/âncoras/alvos. A atribuição PCG64(57) confere: 6.408 origens A e 6.504 B. Ordem, ausência de duplicação, corte exclusivo dos alvos, resposta `target − base do perfil escolhido` e pesos `1 + 2×(|resposta|≥1) + 2×(target≥9)` foram preservados. Os metadados originais de treino conferem. Há 204.168 linhas de avaliação, duas vistas das mesmas 102.084 origens/horizontes.

Os 20 índices são as cinco taxas nominais dH0.5/dH1/dH2/dH4/dH8 de cada uma das quatro estações, excluindo os níveis absolutos. São as colunas 1–5, 7–11, 13–17 e 19–23 dos 180 campos originais; não há coluna extra de idade. O parâmetro dH é uma taxa por tempo nominal entre consultas atrasadas, não necessariamente por intervalo real entre medições.

A mediana de imputação é **não ponderada**, conforme o protocolo. Média e variância/escala são ponderadas pelos pesos originais; todas são estimadas somente nas linhas de treino. Os slopes de treino são todos finitos. A imputação só atende slopes ausentes na avaliação; as entradas originais da árvore não são preenchidas. A maior diferença na reconstrução independente das médias foi 8,67×10⁻¹⁸; nas escalas, 2,78×10⁻¹⁶.

As equações normais foram verificadas diretamente com a reconstrução das estatísticas: `Zᵀ W (Zβ + b − y) + 1000β = 0` e `1ᵀ W (Zβ + b − y) = 0`. Maior resíduo de estacionariedade dos coeficientes: 1,28×10⁻¹⁰; intercepto: 3,20×10⁻¹³, ambos abaixo de 10⁻⁷. Não houve resolução/refit da regressão. Ridge usa alpha 1000, intercepto não penalizado e solver cholesky. Parâmetros HGB coincidem com o pai, com 180 campos e 180 iterações.

O arquivo HGB não prova sozinho quais pesos ou resíduos foram passados ao otimizador. A evidência é o código executado preservado, os hashes, as amostras/pesos reconstruídos, os metadados e a reaplicação do modelo salvo. Os hashes do resíduo reconstruído são dos nossos valores calculados, sujeitos à diferença de arredondamento de até 4,45×10⁻¹⁵ no termo linear de treino; não são um recibo independente dos bytes efetivamente entregues ao fit.

## Resultado misto conferido

Contra o modelo misto sem termo linear, o híbrido melhora MAE de cheia no teste nos 12 horizontes de ambos os perfis. Acertos melhoram em 11 horizontes e pioram em 6h em cada perfil. Na validação, os acertos melhoram/empatam/pioram em 5/2/5 horizontes A e 5/1/6 B; não há domínio do novo modelo.

| Cheia/test | Acertos misto → híbrido | MAE misto → híbrido | Maior erro misto → híbrido |
|---|---:|---:|---:|
| A, 6h | 170 → 165 / 237 | 0,602111 → 0,451277 m | 6,299646 → 4,080086 m |
| B, 6h | 166 → 161 / 237 | 0,635535 → 0,473386 m | 6,505761 → 4,521595 m |
| A, 12h | 75 → 91 / 237 | 1,328673 → 1,110717 m | 7,792800 → 8,991903 m |
| B, 12h | 75 → 94 / 237 | 1,384912 → 1,167521 m | 7,606918 → 8,913888 m |

Cada grupo de cheia/test mantém 237 alvos observados, 236 pares e uma falha; os grupos de validação têm 28 observados/pares. Alvos desconhecidos continuam separados, e falhas permanecem no denominador observado. Os 233/237 acertos do híbrido em 1h correspondem a 98,31% nesse recorte histórico específico e **não** demonstram que a meta geral foi atingida. Todos os períodos já foram inspecionados e são desenvolvimento; não se escolheu um modelo por horizonte nem houve promoção.

## Maior erro em 12h

`check_worst.py` localiza o maior erro de cada perfil e recompõe os componentes independentemente:

- A: origem 21/07/2026 16h BRT, alvo 22/07 04h. Base 3,27 + linear 0,668881 + árvore 1,559216 = 5,498097 m, observado 14,49 m, erro absoluto 8,991903 m. dH1 Muçum −0,14 m/h nominal.
- B: origem 21/07/2026 17h BRT, alvo 22/07 05h. Base 3,22 + linear 1,190039 + árvore 1,836073 = 6,246112 m, observado 15,16 m, erro absoluto 8,913888 m. dH1 Muçum −0,08 m/h nominal.

Nos dois casos faltam os cinco slopes de Carreiro (colunas 19–23), que o ramo linear recebe pelas medianas do treino. O ramo da árvore mantém os NaNs originais. Isso é evidência do cálculo, não prova de que a ausência causou o erro; não foi feito contrafactual de preenchimento.

## Reprodução e limites

Executar `audit.py` e `check_worst.py` no runtime local NumPy/sklearn do experimento, com `PYTHONDONTWRITEBYTECODE=1`; ambos usam somente arquivos locais. `finalize.py` confere integridade de fontes e grava os hashes dos artefatos próprios, excluindo o manifesto de si mesmo. Não refazer a execução após congelamento externo sem autorização.

Reaplicação e equações verificam a consistência numérica deste experimento, não a disponibilidade histórica certificada dos insumos, datum, fuso ou independência dos episódios. Extrapolação linear não é conservação física nem garantia de segurança fora do treino. Nenhuma alteração operacional foi realizada.
