# Status da previsão pública e do modelo complementar — 23/09/2026

Correção publicada e verificada no navegador de produção, em desktop e em 360px de largura.

A mensagem antiga era a data real da última previsão pública, e não a emissão do novo modelo em avaliação. O painel agora separa os dois estados. Os alvos da previsão pública que já passaram não aparecem mais como próximos horários no gráfico ou na tabela. O histórico e a data de 22/09 às 21h31 foram preservados.

Na verificação de produção, a tela mostrou:

> Modelo complementar em avaliação: calculado em 23/09 às 10:18 (Brasília). Este cálculo ainda não é usado no gráfico.

> Última previsão pública: 22/09/2026 às 21:31. Os horários previstos já venceram.

> Sem previsão atualizada para as próximas horas.

A referência do cálculo complementar foi 09h; há cinco pontos experimentais arquivados. A previsão pública continua aguardando suas entradas completas. Não foi habilitada substituição pelo modelo complementar, alterada sua calibração nem inventado um horário público novo.

O servidor só expõe status, horários, versão e recibo do modelo complementar depois de confirmar o arquivamento. Pontos experimentais, fontes brutas e erros internos são excluídos dessa informação pública. Comparei a metadata da API com `propagation-shadow.json` no arquivo R2, verificando hash e recibo.

Validação: 283 testes Python e 71 testes Node aprovados, ESLint e compilação aprovados, runtime com 201 arquivos verificados. React Doctor permaneceu em 68/100 com o mesmo aviso anterior de fetch no efeito, sem novo diagnóstico. No navegador, verifiquei previsão vencida, horários parcialmente vencidos e status separado, além do painel real publicado. O preview local tinha 503 de outras fontes porque foi iniciado sem o coletor/armazenamento; os testes do painel usaram respostas controladas. A conferência final em produção não usou mocks nem relógio simulado.

Worker: `3b981c38-bbc7-43a2-a9b8-5c96ececb335`. Container: versão `67`, confirmado em execução.

Evidências: [API e implantação](production-confirmed.json), [conferência do arquivo](metadata-proof.json), [verificação no navegador](production-browser-check.log), [desktop](production-after-desktop.png), [celular](production-after-mobile.png).
