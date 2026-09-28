# Retenção longa e previsão condicionada a dados completos

Publicado em `radar.brunozilio.com`, 22/09/2026 às 21h39–21h42 BRT.
Worker: `2393eaec-c662-4ab3-9637-11a9282f47ec`, 100% do tráfego.
Contêiner em execução: versão 63, imagem
`sha256:6b6a6c2726f9fb2d3f65c4e51a58cc3efdf86117061db740fc2d7da45a9e6c6a`.

Implementado:

- Nenhuma exclusão automática após 48h nas quatro tabelas hidrológicas nem no
  histórico DCRS. Consultas de cache/tela podem continuar usando janelas curtas.
- Fila persistente de sincronização, confirmação integral e reenvio de backlog,
  dados tardios e alterações. O D1 genérico recebe atualizações; a tabela DCRS
  legada preserva a primeira medição da chave, como antes.
- Gate de níveis aprovados na hora, Q/I das três usinas, cobertura medida de pelo
  menos 50% em cada uma das cinco regiões e vetor completo. Falha de transporte
  de pluviômetro secundário só bloqueia se faltar cobertura. O histórico fica
  intacto; dados ausentes são excluídos apenas da cópia usada no cálculo atual.
- Arquivos R2 imutáveis dos dados, código, pesos, vetor e diagnóstico de cada
  tentativa. Publicação somente depois da confirmação do arquivo. SHA256, criação
  condicional e bloqueio de exclusão/sobrescrita na ponte de evidências.
- Correção de tendência somente em shadow; nenhum candidato promovido. Contrato
  de 180 entradas contemporâneas e construtor de dataset causal para treino futuro.
  Treinamento legado que misturava produtos NWP incompatíveis foi bloqueado.

Validação:

- 211 testes Python + 59 testes Node passaram.
- TypeScript, ESLint específico e `git diff --check` passaram.
- Next build e Wrangler dry-run, incluindo imagem Linux/amd64, passaram. Permanece
  aviso preexistente de rastreamento dinâmico do Python no Next, sem falha de build.
- Smoke test da imagem final, sem rede: tentativa incompleta preservada, dois blobs
  com hashes conferidos e nenhum resultado de previsão criado (`runtime-smoke.log`).
- API pública de previsão e de níveis retornaram HTTP 200 (`public-api.json`).
- Cloudflare confirmou Worker atual, imagem esperada e instância 63 rodando
  (`production-verification.json`). `deploy.log` conserva a publicação.

Limites da comprovação:

A última emissão pública, de 21h31, antecede a publicação e foi preservada. Às
21h42 ainda não havia recibo de uma tentativa nova no R2: a hora 21h já havia sido
calculada. Portanto o pipeline novo foi testado localmente/imagem e está implantado,
mas ainda não se observou uma emissão real dele nesta verificação. A nova precisão
não foi medida prospectivamente; 98% não estão demonstrados. Dados apagados antes
desta mudança não foram recuperados automaticamente. Uma interrupção definitiva
antes da confirmação remota pode perder dados ainda no disco temporário.

Documentação: `docs/hydrology-long-term-history.md`, `docs/hydro-feature-contract.md`.
