# Incidente de atualização da previsão — 23/09/2026

## Diagnóstico confirmado

- Às 08h34 BRT a última emissão pública era de 22/09 às 21h31, referência 21h.
- Coleta de níveis/vazões/chuva continuava alimentando D1. Cron permanecia configurado a cada 15 minutos.
- Tail ao vivo do ciclo 08h45 confirmou POST interno, erro `Network connection lost` no PUT de blob R2 e resposta 503. Apenas um recibo havia sido arquivado desde a implantação anterior.
- O código exigia sempre a hora corrente, descartando a oportunidade de calcular uma hora que ficasse completa depois da virada.

## Correção publicada

- HEAD com verificação de SHA antes do PUT imutável; runtime idêntico já arquivado não é reenviado. Criação concorrente continua condicional e conflitos não são sobrescritos.
- Seleção após coleta da última hora completa, posterior à publicada, com idade real máxima de três horas. Níveis, vazões e chuva mantêm a mesma referência.
- Somente o sufixo ainda futuro dos alvos originais H+1 até H+6 é publicado. Não altera pesos, fórmulas, referência, nem estende artificialmente o horizonte.
- Estado operacional persistido e aviso público de espera/falha com horário da última checagem; dados ausentes não viram zero.
- Contrato de entradas v2 registra atraso; leitor v1 preservado. Dataset v2 rejeita snapshots legados em vez de atribuir uma nova identidade a eles.

Worker ativo: `1561928b-cd49-402f-a483-859e02b06808` (100%). Contêiner versão 64, imagem `sha256:facc85f4fd2ff61d59797064ac052ccea813d5f6c4a6318be33dcbafe4b53dde`, confirmado em execução.

## Resultado real

O primeiro ciclo após o deploy concluiu às **08h49:56 BRT**, arquivando runtime, tentativa e recibo `projection/receipts/2c321ea1-8afb-4221-888a-c552fde69cb7.json`. PUTs retornaram 201. Estado público: `waiting_for_data`, sem erro de atualização.

- Referência 08h: faltam nível aprovado de 86472600 e cobertura mínima de chuva em Carreiro, Alto Antas e Tainhas.
- Referências 07h e 06h: somente Alto Antas impede o cálculo, com 47,2% de cobertura ante o mínimo de 50%.
- Referência 05h: fora da idade máxima de três horas.
- O GFS falhou na coleta local inicial, mas estava disponível na tentativa posterior em produção.

Não foi publicada previsão nova: o bloqueio atual é a falta legítima de entradas exigidas. A emissão anterior permanece identificada como antiga. Aviso e detalhes foram conferidos no navegador público.

## Validação e limites

227 testes Python e 68 Node passaram, além de TypeScript, ESLint dos arquivos alterados, build Next, dry-run Wrangler e execução do runtime empacotado com dados públicos. Manifesto empacotado confere com os arquivos locais.

Teste do cliente real com workerd/R2 local e corpo de 8.831.591 bytes demonstrou HEAD404 → PUT201 → HEAD200, sem segundo upload. O erro específico do ContainerProxy não foi reproduzido localmente: a falha foi observada em produção. O primeiro ciclo pós-deploy foi confirmado; um segundo ciclo periódico pós-deploy ainda não foi observado nesta verificação. Não houve treinamento, promoção do shadow ou comprovação de 98% de assertividade.

Evidências: `live-tail.jsonl`, `production-verification.json`, `receipt-after-deploy.json`, `reference-selection-production.json`, `public-after-deploy.json`, `r2-binding-smoke.json`, logs de testes/build/deploy e `source-checksums.json`.
