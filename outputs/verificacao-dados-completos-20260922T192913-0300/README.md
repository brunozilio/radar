# Diagnóstico e bloqueio por dados completos — 22/09/2026

Correção preparada e testada localmente. Não publicada nesta execução.

## O que foi constatado

- O site executava inferência a cada 15 minutos, substituindo a rodada da mesma hora. Seu modelo era congelado, mas aceitava âncora de Muçum com até 90 minutos de atraso.
- A rotina de pesquisa treinava novamente a cada emissão; a comparação preservada entre 01h e 02h mostra 144.159 células históricas derivadas alteradas e uma revisão de +0,6625 m para o alvo 07h. Revisão entre emissões não é, por si só, erro contra a observação.
- A auditoria da pesquisa às 04h registrou âncora de 18,73 m frente ao máximo de treino de 15,31 m. Isso expõe limitação de generalização, sem provar a causa individual de cada erro do site.
- Conferência exploratória com as leituras ANA aprovadas da coleta de 19h29: 14 pares exatos em cada rodada de pesquisa 01h/02h/04h; MAE de 1,7426 / 2,2502 / 1,8027 m. Inclui todos os 14 alvos nominais daquelas emissões. Não equivale à amostra certificada da meta, nem comprova os valores exibidos publicamente. Dados e erros por alvo em `diagnostico-erros.json`.

## Regra implementada

O relógio continua consultando disponibilidade. A hora de referência é fixada antes da coleta. Só há previsão quando existem níveis aprovados dos quatro postos usados pelo modelo e vazões de entrada/saída das três usinas no instante H; chuva medida em (H−1h,H], com postos cobrindo a hora completa e no mínimo 50% do peso espacial de CADA uma das cinco regiões; previsão meteorológica e todos os 180 atributos atuais finitos. Chuva zero é válida; ausência não vira zero. Falha de coleta, conflito de dados e integridade também bloqueiam.

A integração de chuva da rotina completa usa os horários reais, sem deslocar uma janela atrasada para H. Os dados ANA recentes entram com qualidade explicitamente aprovada. Encantado e Santa Tereza também exigem âncoras exatas da própria cidade e montante; falha individual conserva a emissão anterior da cidade.

O servidor consulta a emissão persistida antes de calcular e não substitui uma rodada já publicada na mesma hora. Retentativa de publicação reutiliza o resultado completo salvo. Cada processo tem identificador de tentativa: um arquivo antigo de resultado/status não pode parecer uma emissão nova. `waiting_for_data` encerra sem inferência, publicação ou alteração da última previsão. Não registra ciclo de pesquisa como concluído.

## Verificação com dados atuais

Coleta pública nova às 19h29, referência 19h: Muçum 11,61 m e vazões das três usinas presentes. Faltam níveis exatos dos outros três postos. Cobertura de chuva por região abaixo do mínimo:

- Baixo Antas: 45.66%.
- Carreiro: 1.40%.
- Prata-Turvo: 0.00%.
- Alto Antas: 12.03%.
- Tainhas: 0.00%.

Resultado real: **aguardando dados; nenhuma previsão gerada**. Manifesto com hashes e corpos originais preservados nesta pasta.

## Limites

Esta alteração impede calcular com parâmetros ausentes ou horários misturados; não demonstra 98% de acerto nem elimina limitações do modelo. A validação prospectiva, datum e fuso das fontes continuam pendentes. O pacote local está preparado; o ambiente público permanece na versão anterior até uma publicação autorizada.

## Validação local concluída

43 testes Python relacionados e 41 testes TypeScript passaram. TypeScript sem erros; ESLint dos arquivos alterados sem erros; build Next concluído. O build apresentou avisos de rastreamento amplo do executável Python e arquivos de configuração (nenhum erro). Pacote de runtime: seis fontes alteradas idênticas ao pacote e aos hashes do manifesto. `git diff --check` sem erros.
