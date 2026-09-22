# Revisão anterior ao ajuste — acréscimo de junho/2024

**Nenhum bug impeditivo encontrado. 409 verificações locais passaram**, sem treinamento, predição ou rede. Foram revisados código/protocolo, entradas seladas, máscaras, cronologia, bases/alvos e configuração dos24 modelos de controle. A conclusão se limita ao desenho e aos artefatos anteriores ao ajuste; não certifica o resultado futuro da execução.

## Conferências

- **Simetria das120colunas:** matriz recente12912×120 coincide exatamente com as primeiras120colunas da referência original no domínio temporal predefinido, inclusive1.549.440 células,NaNs,base,truth,times ecomplete24. Reconstrução recente usa fontes estritas; sua igualdade com a referência permite reaplicar os controles sem refit. Protocolo de junho usa o mesmo contrato observado/QC explícito/atrasos/pesos/ONS literal; não acrescenta NWP nem variável de evento.
- **Datas e alvos:** junho é uma série separada168×120,15–21/06. `shift` é aplicado separadamente ao truth de cada dataset antes de concatenar as amostras de treino. Últimos h alvos de junho permanecem indisponíveis e nenhuma linha cruza para2025. Há167/162/156 pares novos emh1/6/12,126 alvos≥7m em cada. Não entram2018,2020,2021,2022,2023 nem abril/2024 como dados extras.
- **Máscaras/cortes:**24 máscaras recentes reproduzem as congeladas exatamente. Validação usa alvos anteriores a01/10/2025; teste usa os dois blocos originais, primeiro com alvo anterior a01/10 e segundo com origem≥01/10 e alvo anterior a01/07/2026. A lacuna deorigens que atravessam a fronteira deoutubro é preservada, não silenciosamente preenchida. Todos os alvos extras ficam antes dos dois cortes.
- **Uma linha por origem:** junho é concatenado cronologicamente antes das linhas recentes. Não há origem duplicada, imputação ou exclusão por entrada auxiliar incompleta. Linha/Carreiro ausentes nas novas linhas permanecem NaN. Cada um dos24 fitsets combinados tem pelo menos um valor finito em todas as120colunas, evitando repetir a falha da coluna inteiramente ausente do experimento anterior.
- **Pesos:** mesma expressão `1+2*(abs(target-base)>=1)+2*(target>=9)`. Os72 vetores previstos no manifesto pré-fit são resposta/nível/peso para24 ajustes;36 máscaras compreendem24 recentes e12 extras. `membership-review.csv` recalcula contagens e somas esperadas independentemente, sem chamar helpers do experimento.
- **Configuração:**24 controles salvos foram abertos somente para ler configuração e número decolunas. Parâmetros de perda/folhas por horizonte e receita fixa coincidem com os previstos para candidatos. Runtime coincide com o experimento observado120. Nenhum `fit` ou `predict` foi chamado nesta revisão.
- **Avaliação:**102084 chaves únicas, bases, alvos exatos e horários dos alvos reconciliados com o controle congelado. Previsão é tentada para origem com base finita, mesmo que o alvo seja desconhecido; nenhuma seleção de inferência usa o resultado futuro. A cobertura esperada é a mesma do controle. `complete24` é recorte diagnóstico, não restrição de treino.
- **Plano pré-fit:** código grava protocolo,36 máscaras,72 vetores,24 planos e seus hashes antes do primeiro ajuste. Faz replay exato do controle em cada fase/horizonte antes do ajuste correspondente; divergência aborta, não substitui silenciosamente o histórico. Hashes de entradas/modelos são guardados e reconferidos ao final. A existência dessa ordem no código não substitui verificar manifesto, horário de execução e artefatos produzidos depois.

## Limites e acompanhamento

A matriz de junho não foi reconstruída da fonte nesta subetapa: foram verificados seus hashes/contrato e o conjunto de entradas seladas. A conferência anterior da matriz, conduzida separadamente, registra pequenas diferenças de aritmética dechuva; esta revisão não arredondou entradas nem presume invariância das árvores a essas diferenças.

QC aprovado não demonstra datum/fuso/publicação histórica. Junho é posterior às avarias das usinas, tem falta deLinha/Carreiro, cobertura dechuva incompleta e conflitos decomponentesONS preservados. Esses limites permanecem heterogêneos e explícitos; igualdade decolunas/receita não torna períodos fisicamente equivalentes.

As métricas no código mantêm falhas no denominador de alvos observados e não transformam alvo desconhecido em acerto. O campo específico `missing_truth` não está na tabela agregada: pode ser derivado no recorte `all` por scheduled_rows−observed_targets, enquanto o recorte alto precisa separar abaixo7 de desconhecido via predictions. Isso é uma ressalva de apresentação, não alteração dos cálculos ou bloqueio encontrado. Recomenda-se deixar essa distinção explícita no relatório final.

Ficam para auditoria após a execução: igualdade dos vetores efetivamente salvos aos esperados, replay dos24 candidatos, igualdade dos controles e recomputação das288 métricas. Um joblib isolado não prova quais pesos/resíduos foram consumidos pelo otimizador; evidência necessária combina fonte executada, manifesto pré-fit e artefatos, sem reivindicar prova interna dos pesos.

Períodos já inspecionados são desenvolvimento. Nenhuma promoção ou precisão98% decorre desta aprovação técnica do desenho. Fontes/código raiz e artefatos anteriores permaneceram intocados.

`review.py` é reproduzível sem fit/predict/rede; `input-hashes.json` identifica os arquivos efetivamente lidos; `verification.json` detalha409 verificações. Manifesto e check próprios encerram esta pasta.
