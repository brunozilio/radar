# Hipótese experimental: atualização pela leitura local mais recente

O modelo público calcula com todas as fontes completas da mesma hora; geralmente emite cerca de uma hora depois dessa referência. Uma leitura aprovada de Muçum adquirida depois da referência e antes da emissão pode corrigir o ponto inicial da trajetória. A hipótese foi sugerida após examinar as rodadas de 22–28/09/2026; esse período **já foi usado no desenvolvimento**.

## Fórmula congelada para avaliação shadow

Usar somente a leitura mais recente de Muçum com timestamp posterior à referência, anterior ou igual à emissão, aprovada no XML ANA recebido antes da emissão e com idade de no máximo 60 minutos. Interpolar linearmente entre o nível observado na referência e o primeiro alvo futuro do modelo público para estimar o valor do modelo no instante dessa leitura. Somar a diferença entre leitura e interpolação a cada ponto futuro, limitada a ±0,50 m. Não alterar horários, horizonte nominal, valores do modelo público ou artefatos congelados. Sem leitura elegível, registrar candidato indisponível.

Este ajuste usa uma observação posterior à referência, mas anterior à emissão. No replay com o CSV SGB atual, assumir disponibilização 45 minutos depois da medição apenas para diagnóstico; essa hipótese não prova disponibilidade histórica. A avaliação prospectiva deve usar os recibos ANA arquivados de cada emissão, comparar exatamente os mesmos alvos e separar 1–6h, cheia, subida, pico e recessão. O candidato permanece não publicável até mostrar ganho sem regressão crítica em eventos independentes.
