Verificação independente concluída: 162 conferências, nenhuma falha.

O cenário de 15 minutos preserva as 23.538 linhas/chaves/alvos/status do experimento de proxy original e reproduz exatamente 23.250 previsões finitas em cada família (46.500 valores, erro máximo zero, tolerância 1e-10 m). Os padrões de ausência também coincidem.

Os três cenários preservam origens/alvos, conteúdo dos modelos e arrays de proxy e registros de treino. Todos os hashes declarados das entradas foram confrontados com os arquivos. Entre cenários, apenas o protocolo muda; em relação ao experimento anterior, a mudança do script de âncora é explicitamente permitida e o restante das entradas coincide.

Cada anchor_at corresponde a origin menos 15/30/45 minutos. O snapshot efetivamente executado foi inspecionado por AST para chamadas e expressões de interpolação, busca da âncora, timestamp e decaimento. As duas funções puras foram testadas para conversão de idade, pesos, fluxo constante, trajetória linear e rejeição de idades inválidas. Não foi necessário reiniciar ou repetir nenhuma execução do modelo.

verification.json contém as verificações individuais e hashes; verify.py reproduz a auditoria. executed-hydro_reservoir_mucum_experiment.py preserva o snapshot auditado. Esta conferência não reexecuta integralmente os modelos, não calcula métricas comparativas e não certifica disponibilidade histórica/causalidade operacional. Nenhum arquivo fora desta pasta foi alterado.

Comando: PYTHONDONTWRITEBYTECODE=1 /tmp/radar-hge-venv/bin/python outputs/verificacao-idade-ancora-20260921/verify.py

