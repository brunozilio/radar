# Auditoria das colunas Radar core33

As mesmas 33 posições têm a mesma definição matemática, identidade nominal de fonte e unidades nas matrizes original e 2023. A função telemetry_features é idêntica por AST nas duas cópias congeladas e no código atual. A reconstrução independente a partir das grades de 15 minutos coincide exatamente em **450.384 células** (426.624 originais e 23.760 de 2023), incluindo NaNs.

| Posições na matriz120 | Posições core33 | Fonte e conteúdo |
|---|---|---|
| 0–5 | 0–5 | Muçum 86510000: H e dH0,5/1/2/4/8 |
| 6–11 | 6–11 | Linha José Júlio 86472000: H e dH0,5/1/2/4/8 |
| 24–30 | 12–18 | 14 de Julho JIUHQJ: Q06, Q, I, dQ06 1/2/4/8 |
| 31–37 | 19–25 | Monte Claro JIUHMC: mesmos sete campos |
| 38–44 | 26–32 | Castro Alves JIUHCA: mesmos sete campos |

`H` está em metros, derivadas de H em m/h. Q e I estão divididas por 1.000 (não valores em m³/s sem escala). `Q06=max(Q/1000,0)^0,6`; **dQ06 é a derivada dessa potência por hora**, não derivada da vazão bruta. O clipping pertence apenas à potência; Q/I preservam seus valores. Afluência I e defluência Q são de cada usina individual, não somas na cascata. O CSV columns.csv registra todas as 33 posições, fórmulas e unidades.

Os atrasos congelados são Muçum 15 min, Linha José Júlio 30 min, com expiração de 15 min após a consulta; Q/I 60 min, expiração de 90 min. idades-fontes.csv confirma os valores do snapshot original, e o builder2023 declara os mesmos. Comparação matemática não certifica disponibilidade histórica real.

## Cobertura

| Matriz | Origens | Linhas com todos33 finitos | Linhas com alguma falta | Células ausentes |
|---|---:|---:|---:|---:|
| original2025_26 | 12928 | 12427 | 501 | 1720 |
| added2023 | 720 | 486 | 234 | 2115 |

No lote2023, entre pares base/alvo finitos h1/h6/h12, são 503/493/481 pares; 483/473/461 têm todos33 finitos e **20 em cada horizonte continuam com alguma falta**. A seleção core33 não deve acrescentar um filtro de completude: as máscaras originais do experimento devem permanecer. Contagens da matriz original cobrem toda a grade preservada, não equivalem às máscaras temporais de treino de uma fase.

## Correspondência e limites

A correspondência de colunas é consistente para o experimento fatorial declarado. Isso é distinto de certificar equivalência física das medições: datum, manutenção dos sensores, validade de Q reportada, fuso/publicação e regime operacional entre 2023 e 2025/26 continuam sem certificação.

O preparo original mescla história já em grade e HTML CERAN recente; o de2023 consulta CSVs ONS mensais com timestamps literais, inclusive23:59. Esta auditoria recompõe derivados das grades preservadas, não reconstrói a cadeia original de ingestão ONS/CERAN nem declara versões de fonte intercambiáveis. A auditoria anterior da matriz2023 verificou a consulta literal diretamente; nenhuma nova consulta foi feita aqui.

Core33 elimina os12 campos Santa Tereza/Carreiro e todos75 campos de chuva do conjunto120. Manter mesma ordem não demonstra que esse corte melhorará previsões. Nenhum modelo foi lido, treinado ou executado; nenhum dado ou código operacional foi modificado.

Protocolo disponível e preservado nesta execução: sim. O conteúdo integral e o hash, quando disponível, ficam em verification.json.
