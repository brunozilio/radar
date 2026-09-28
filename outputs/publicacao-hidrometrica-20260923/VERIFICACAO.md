# Publicação hidrométrica — 23/09/2026

O modelo `radar_mucum_hydrometry_v1` está público em https://radar.brunozilio.com/#previsao. O cálculo original de 10:31:52 BRT, com referência observada às 09h e alvos das 11h às 15h, foi publicado às 10:47:34 BRT a pedido explícito do usuário. Os horários e valores não foram alterados.

Foram removidas, para esse modelo, a exigência de chuva e a restrição de publicação somente em avaliação. Permanecem a identificação experimental, as observações reais de quatro estações e três usinas e o arquivo permanente do cálculo. A meta de 98% não está demonstrada.

Validação concluída: 296 testes Python, 73 testes Node, compilação, ESLint focal, contrato do pacote e comparação visual/API em produção. `browser-production.log` registra gráfico visível e os cinco valores conferidos; `production-desktop.png` e `production-mobile.png` mostram a página real. O arquivo remoto, os sete recibos de entrada e o pacote de execução foram conferidos por SHA e conteúdo (`archive-proof.json`, `publication-proof.json`).

Contêiner ativo: versão 68, imagem `5232e75ea2fa5f28cad73c3bea47a573f52d38e732cdba7ab109b8df0249e273`. Worker confirmado após a publicação: `f14f0427-2d9d-417b-87f8-f8b258abfdbf`. A tentativa automática às 10h38 executou, mas as quatro consultas ANA excederam o tempo de leitura nas duas tentativas; CERAN respondeu normalmente. Por isso foi publicado o artefato completo já gerado, com seu histórico real, sem inventar novas entradas. O próximo cálculo automático continua dependente da disponibilidade das fontes de níveis e vazões.

Uma hipótese sobre o bootstrap motivou uma alteração local, mas o arquivo de produção confirmou que ele executou. A alteração foi revertida; tentativas adicionais de imagem falharam no Docker e não substituíram o contêiner 68. `scripts/run.mjs` permanece como no contêiner publicado.

A publicação pontual utilizou R2 autenticado, arquivando antes de atualizar `latest.json`. O runtime compartilhado já existia, manteve `custom_metadata.sha256` correto e não foi regravado. O attempt, recibo e issue exclusivos dessa publicação não possuem esse metadata adicional na API REST; seus bytes, SHA, identidade e ligações foram conferidos por leitura. Eles não fazem parte da fila de repetição do servidor. Não houve alteração das credenciais nem criação de rota sem autenticação.
