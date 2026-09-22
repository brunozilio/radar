# Entradas sem contribuição e falhas de cobertura

A nova política ignora uma entrada somente quando seu peso de roteamento congelado é exatamente zero. Não há tolerância numérica para descartar pesos pequenos, redistribuição dos pesos, preenchimento de lacunas ou novo treinamento. A opção anterior permanece disponível e sua execução original está preservada em `outputs/experimento-niveis-ate-mucum-20260921/`.

Comparação na grade completa de 23.538 alvos: os 38.256 valores finitos das duas famílias permaneceram **exatamente iguais**, incluindo previsões sem verdade observada. Nenhuma classificação de disponibilidade mudou; foram recuperados zero pares. O ajuste corrige uma exigência matemática desnecessária, mas não melhora a cobertura deste acervo porque as mesmas lacunas também atingem entradas necessárias.

Continuam 18.981 pares, 4.122 falhas de entradas, 288 âncoras ausentes e 147 alvos ausentes com entradas disponíveis. Os resultados de precisão permanecem idênticos: ganho misto do candidato, sem promoção e sem comprovação de 98%.

## Causa das falhas de entradas

As 4.122 falhas estão distribuídas por 344 origens. A auditoria estrutural identificou Passo Carreiro em todas elas, sem causa não explicada:

- 4.056 alvos dependem de vazão histórica ausente para reconstruir a âncora.
- 3.750 dependem de vazão histórica ausente no roteamento futuro.
- 2.214 dependem de uma vazão conhecida de base ausente para os preditores.

As causas se sobrepõem; não somar essas contagens. Os detalhes por origem/alvo estão em `failure-causes.csv`, com hashes em `failure-causes.json`. Nenhum dado ausente foi substituído por zero, último valor ou observação futura. A próxima investigação deve conferir QC/versões da estação 86500000 e níveis medidos disponíveis antes de propor tratamento local de entradas.

A mudança ficou no experimento histórico. Os dois modelos horários e as emissões anteriores não foram alterados. Esta execução não adiciona amostras prospectivas ao placar da meta.
