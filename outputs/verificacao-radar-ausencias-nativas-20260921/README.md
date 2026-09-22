# Verificação independente — Radar com ausências nativas

**Verificação inicial: 751 checks aprovados, 102.084 linhas e 48 modelos.** O número final de checks de integridade pode crescer com a inclusão dos relatórios no manifesto original; `verification.json` guarda o resultado exato da execução. Não houve ajuste de modelos, HGE, coleta ou alteração das fontes/saídas originais.

O experimento verificado é `outputs/experimento-radar-ausencias-nativas-runtime19-20260921`. A emenda é explícita: baseline e candidato são ajustes novos no runtime operacional scikit-learn 1.9.1. O baseline mantém a população original; o candidato retira apenas a exigência dos primeiros 24 campos completos no treino. Não se reivindica que o baseline novo reproduza as previsões históricas do runtime 1.6.1.

## Conferências realizadas

- Hashes das entradas e artefatos, cópia do protocolo e versões das bibliotecas.
- Reconstrução das 120 features de telemetria com as funções puras preservadas e dos 60 acumulados meteorológicos pela associação independente dos horários futuros. Diferença máxima **zero**, inclusive máscaras de ausência e ordem das colunas.
- Todos os cortes e memberships de treino, incluindo a união ordenada dos blocos anteriores a outubro e de outubro a julho. A pequena exclusão de fronteira do histórico é mantida; não se substitui silenciosamente pela regra operacional de corte único.
- Contagens de treino, presença de NaN, parâmetros congelados, 180 iterações/180 entradas por modelo, contagem de amostras nas raízes de todas as árvores e intercepto inicial ponderado. Diferença dos interceptos **zero**. O verificador não refaz os splits nem o ajuste de árvores.
- Inferência de cada um dos 48 modelos carregados sobre todas as origens programadas: diferença máxima **zero** em relação ao CSV preservado. Só a falta do H-base bloqueia a previsão; alvo ausente não impede inferência.
- Chaves, alvos, nível-base, classificação complete24/missing24 e denominadores de cobertura dos resultados agregados.
- Os **16.113 pares antigos** estão integralmente em `runtime-comparison.csv`. A maior diferença entre o arquivo histórico e o novo baseline é **1,1783888025628855 m**. Os valores antigos permanecem identificados; não foi relaxada a tolerância para chamá-los equivalentes.

## Cobertura conferida, por família

| Período | Linhas programadas | Pares avaliáveis | Pares complete24 | Pares missing24 | Previsões sem alvo |
|---|---:|---:|---:|---:|---:|
| Validação descritiva | 78.546 | 77.664 | 70.597 | 7.067 | 402 |
| Teste histórico já inspecionado | 23.538 | 23.115 | 16.113 | 7.002 | 147 |

No teste existem 276 linhas sem H-base e 276 sem alvo, com sobreposição. Essas duas contagens não devem ser somadas como exclusões independentes. Ambas as famílias preservam as mesmas linhas e disponibilidade de previsão. Os números por horizonte estão em `coverage.json`; os memberships e hashes de índices/alvos/pesos estão em `training-membership.json`. Métricas de precisão e a decisão sobre o candidato ficam no relatório principal do responsável, não nesta auditoria.

## Limites

A auditoria confere o conteúdo da emenda e as evidências preservadas; a precedência exata da emenda sobre a execução do teste é sustentada pelo registro do responsável, não por um novo recibo assinado. A validação já havia sido usada para escolher hiperparâmetros e não é independente. Os períodos de teste também já foram inspecionados.

Latências fixas do snapshot, revisões das fontes e previsão arquivada previous_day1 não certificam disponibilidade histórica. Fuso do serviço legado e referência física da régua continuam pendentes. Conferir arquivos/modelos não constitui promoção, inferência operacional ou comprovação de 98%.

Reprodução sem refit: `PYTHONDONTWRITEBYTECODE=1 /tmp/radar-hge-venv/bin/python outputs/verificacao-radar-ausencias-nativas-20260921/verify.py`. O nome do ambiente virtual é histórico; o verificador executa somente rotinas Radar, NumPy e inferência dos modelos HGB congelados.
