# Histórico hidrológico e evolução controlada

Alteração de 22/09/2026. Não há descarte automático de medições após 48 horas.
Níveis ANA/SACE/DCRS, chuva e vazões permanecem no SQLite local enquanto o
contêiner existe e no D1 após confirmação da sincronização. O cache de inicialização
e algumas consultas de tela continuam limitados a 48 horas, sem apagar o arquivo.
Dados apagados antes desta alteração não são reconstruídos por ela.

A fila local usa sequência persistente de inserção/alteração, em vez de horário
de medição. Cada consumidor confirma lotes inteiros; uma falha mantém o lote para
reenvio. Uma leitura antiga recebida agora também entra na fila. O disco do
contêiner é temporário: a confirmação no D1/R2 é o limite da garantia de conservação.

Cada tentativa de previsão preserva:

- respostas brutas e seus recibos/horários/checksums, mesmo quando faltam dados;
- diagnóstico da cobertura de chuva e dos níveis/vazões exigidos na hora;
- nas tentativas calculadas, os 180 valores usados, a previsão original e a
  correção de tendência em avaliação paralela;
- código, pesos congelados, dependências declaradas e entradas de apoio do runtime.

O R2 recebe objetos identificados pelo SHA256 em `projection/blobs/` e um recibo
em `projection/receipts/`. O recibo é publicado depois de todos os seus objetos.
Criações são condicionais: repetição de conteúdo idêntico é aceita; colisão é
erro. A ponte do aplicativo não permite sobrescrever nem excluir essas evidências.
Antes de reenviar um objeto, o cliente consulta seu SHA no R2. Isso evita o
reenvio do mesmo runtime em todas as tentativas; a criação segue condicional
para proteger também chamadas concorrentes.
`projection/issues/` também passa a exigir criação imutável. `latest.json`, as
rodadas por hora e os checkpoints de trabalho continuam sendo índices mutáveis.
Não há rotina de expiração para o arquivo hidrológico.

A publicação de uma nova previsão ocorre apenas depois de arquivar a tentativa.
Quando falta nível aprovado na hora, Q/I das três usinas, cobertura medida de pelo
menos 50% em cada uma das cinco regiões de chuva ou algum campo do vetor final,
a emissão anterior permanece disponível. A checagem a cada 15 minutos verifica
se os dados chegaram; não força recálculos com dados incompletos. Uma hora já
publicada não é recalculada.

Desde 23/09, a coleta procura a hora completa mais recente posterior à última
publicada, com no máximo três horas de idade real. Todas as fontes observadas
continuam correspondendo à mesma referência. Só são emitidos os alvos originais
H+1 a H+6 ainda futuros; a referência nunca é avançada para aparentar atualização.
O estado operacional em `projection/refresh.json` informa última checagem,
aguardo por dados ou falha; ele não altera as evidências nem os valores publicados.

A correção `radar-short-term-shadow-v1` não altera valores públicos. O replay do
único episódio já analisado apresentou melhora em recessão e regressões em alguns
outros regimes; não autoriza promoção. O runner antigo de retreinamento misturava
NWP histórico `precipitation_previous_day1` com o produto atual e foi bloqueado.
O modelo congelado continua experimental; seu treinamento não é certificado pelo
novo contrato de coleta.

O contrato e o construtor de datasets estão em `hydro-feature-contract.md`.
A próxima substituição exige dados suficientes, eventos separados no tempo,
comparação por antecedência real e aprovação nos critérios da meta. A operação
atual tem seis alvos nominais; isso não comprova seis horas completas de antecedência
nem a meta de 1–12 horas. Não foi demonstrada assertividade de 98%.
