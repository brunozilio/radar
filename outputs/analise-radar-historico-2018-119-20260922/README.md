# Efeito da adição de2018 sob a âncora horária experimental

Comparação pareada entre novos controles somente2025/2026 e candidatos com todos os exemplos admissíveis de2018. Os dois lados usam a mesma preparação, os mesmos parâmetros, pesos e alvos. Os120campos preparados são preservados; o estimador recebe119, omitindo exclusivamente dH0,5deMuçum, inteiramente ausente nos dois lados. A tentativa120falhou antes de qualquer modelo concluído e permanece preservada.

| Fase | Horizonte | Alvos≥7m | Pares | Acertos controle→+2018 | MAE controle→+2018(m) | Maior erro controle→+2018(m) |
|---|---:|---:|---:|---:|---:|---:|
| test | 1h | 237 | 236 | 228→228 | 0.1300→0.1312 | 2.2889→2.2416 |
| test | 6h | 237 | 236 | 151→156 | 0.6573→0.6200 | 6.2851→5.8732 |
| test | 12h | 237 | 236 | 79→75 | 1.4198→1.3669 | 8.0599→7.1748 |
| validation | 1h | 28 | 28 | 27→28 | 0.1118→0.1079 | 0.5495→0.4987 |
| validation | 6h | 28 | 28 | 21→20 | 0.3692→0.3692 | 2.1737→1.9214 |
| validation | 12h | 28 | 28 | 9→8 | 0.8501→1.0017 | 2.4378→2.2598 |

## Os12horizontes, sem selecionar somente os favoráveis

- validation/all: acertos melhoram em10, pioram em2 e empatam em0; MAE melhora em9 e piora em3; erro máximo piora em5.
- validation/level_ge_7m: acertos melhoram em4, pioram em5 e empatam em3; MAE melhora em4 e piora em8; erro máximo piora em5.
- test/all: acertos melhoram em8, pioram em4 e empatam em0; MAE melhora em9 e piora em3; erro máximo piora em6.
- test/level_ge_7m: acertos melhoram em8, pioram em3 e empatam em1; MAE melhora em9 e piora em3; erro máximo piora em6.

Os períodos de avaliação já eram conhecidos no desenvolvimento. As duas semanas2018 entram somente no treino e não são apresentadas como teste inédito. Esses controles foram treinados novamente sob a âncora1h; não representam reprodução dos modelos operacionais de180entradas nem dos controles antigos.

Acerto exige erro absoluto≤0,50m antes de arredondamento. Falhas são mantidas no denominador de alvos observados; verdade ausente continua desconhecida. Os subconjuntos complete_upstream18/missing_upstream18 referem-se às colunas originais6..23, sem classificar a ausência estrutural de dH0,5 como perda de montante.

Métricas retrospectivas não comprovam98%prospectivos. Fuso,datum,publicação histórica e equivalência entre regimes permanecem sem certificação. Nenhum candidato foi promovido, nenhuma previsão operacional foi substituída e nenhuma combinação porhorizonte foi escolhida depois dos resultados.
