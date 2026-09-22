# Verificação independente — Radar com níveis dos reservatórios

**385 checks passaram.** Verificador reproduzível em `verify.py`, resultados em `verification.json`. Nenhum modelo foi reajustado, nenhum HGE foi executado e nenhuma fonte ou saída original foi alterada.

Foram conferidos os hashes dos artefatos executados e suas entradas. Relatórios em edição pelo responsável foram deliberadamente excluídos dessa barreira de integridade para evitar conflito com alterações simultâneas. A referência é `outputs/experimento-radar-niveis-reservatorios-20260921`.

## Resultado

- **102.084 linhas** mantêm exatamente ordem, chaves, alvos, nível-base e classificação complete24/missing24 do experimento anterior.
- As **204 colunas** são exatamente as 180 entradas anteriores acrescidas das 24 entradas preservadas. A grade temporal coincide, sem infinitos. A procedência dessas 24 entradas foi conferida separadamente em `outputs/auditoria-features-reservatorios-radar-20260921`: fontes, atraso/expiração, 23:59 literal, ausências e diferenças estão preservados.
- Os **24 modelos baseline** são os mesmos arquivos congelados do experimento runtime19, conferidos contra ambos os manifestos. O código executado contém ajuste somente do candidato; não há ajuste do controle.
- Os **24 candidatos** mantêm configuração, pesos/alvos declarados, cortes, membership complete24 e intercepto inicial do baseline. Contagens nas raízes de todas as árvores e metadados de treino coincidem. Ausências nas colunas acrescentadas não filtram o treino.
- Reaplicadas as **48 inferências** a todas as origens programadas: diferença máxima **zero** frente aos valores preservados. Somente a falta do nível-base impede inferência; ausência de alvo não a impede.
- Todos os valores baseline e **todos os campos das linhas baseline de evaluation.csv** permanecem exatamente iguais aos anteriores. Os denominadores de cobertura das duas famílias também são iguais. Nenhuma linha foi eliminada em função de erro, cheia, dado auxiliar ausente ou resultado do candidato.

`membership.json` preserva hashes dos índices ordenados, deltas-alvo e pesos; `coverage.json` registra agendamentos, ausências e pares por divisão temporal/horizonte. A reconstrução verifica a procedência e a inferência dos modelos salvos; não refaz seus splits nem substitui um registro completo de treinamento.

## Limites

Ambas as famílias usam o **baseline com treino complete24**. O candidato anterior treinado com ausências nativas não foi usado como controle nem combinado com estas entradas. Nos 24 conjuntos de treino, há **zero linhas com ausência nas colunas acrescentadas**. O código admite NaN, mas estes ajustes não aprenderam rotas específicas de ausência nessas entradas; a regra padrão do HGB se aplica se faltarem depois. Não interpretar esta execução como validação desse regime de ausência.

Os números são desenvolvimento histórico já inspecionado. A validação já foi usada para selecionar parâmetros anteriores. Atraso de publicação, fuso e referências físicas das fontes permanecem hipóteses conforme a auditoria das entradas. A política temporal admite até 150min de idade total em relação à origem: 60min de atraso mais 90min de validade após o corte atrasado. Nenhuma promoção, inferência operacional ou comprovação de 98% decorre desta verificação.

Reprodução sem refit: `PYTHONDONTWRITEBYTECODE=1 /tmp/radar-hge-venv/bin/python outputs/verificacao-radar-niveis-reservatorios-20260921/verify.py`. O nome histórico do ambiente não implica uso de HGE: só são reconstruídas entradas e reaplicados os modelos Radar congelados.
