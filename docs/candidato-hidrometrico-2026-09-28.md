# Candidato offline: níveis de Muçum e Santa Tereza

Hipótese registrada antes da avaliação: os dados de vazão e as defasagens do modelo público reduzem muito a cobertura histórica e deixam pouquíssimas cheias no ajuste. Um modelo menor, alimentado apenas por níveis aprovados de Muçum e Santa Tereza, pode aprender melhor subidas fortes com os episódios de abril/maio e junho de 2024.

## Receita fixa

- Alvo: nível exato de Muçum 1–6 horas após a origem. Sem interpolação de observações.
- Entradas: níveis de Muçum e Santa Tereza na origem; variações de Muçum em 1, 2 e 6 horas; variações de Santa Tereza em 1 e 3 horas. Exigir todos os horários exatos.
- Ajuste: ridge sobre a variação do nível, com padronização no treino. Escolher `alpha` em {1, 10, 100, 1000} exclusivamente pela validação, usando a função de pontuação de `hydro_propagation_model.py`. Reajustar treino + validação após a escolha.
- Treino: observações de 2024 disponíveis nos arquivos brutos locais e 01/04/2025–01/10/2025. Validação: após embargo de 33 h, até 01/07/2026. Teste cronológico: após novo embargo, até 21/09/2026. O episódio 21–23/09/2026 é diagnóstico separado.
- Comparação pareada com as previsões congeladas do modelo público nos horários comuns; reportar também a cobertura natural do candidato.

Os dados de 2024 foram baixados retrospectivamente e podem ter revisões. O histórico e os episódios recentes já foram examinados por este projeto. Teste e diagnóstico não certificam desempenho prospectivo nem autorizam promoção. Só uma melhora consistente em cheias, sem regressão relevante no restante, justificaria implementar uma versão *shadow* para novas emissões.
