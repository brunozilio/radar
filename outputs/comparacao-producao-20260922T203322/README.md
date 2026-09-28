# Auditoria de previsões em produção — 22/09/2026

Consultas somente leitura ao D1 `sofik-monitoramento-push` e R2 `sofik-monitoramento-media`, em 22/09/2026 até 20h35 BRT. Nenhum arquivo local de previsão da pesquisa foi usado como previsão de produção.

- `comparacao-antecedencia-real.md`: tabela hora a hora das três cidades, exigindo previsão já persistida pelo menos uma hora antes do alvo; inclui métricas com antecedência mínima de 1–6h.
- `comparacao-hora-a-hora.md`: tabela de todos os seis horizontes nominais do modelo, usando a última emissão de cada rodada, com previsto/erro em cada célula.
- Os arquivos JSON correspondentes trazem valores sem arredondamento, horário próprio de emissão de cada cidade, antecedência real, fonte observada e chaves originais R2.
- `todas-emissoes.json` preserva todas as revisões deduplicadas; elas não são tratadas como eventos independentes nas métricas principais.

Foram lidos 87 objetos de emissão, 24 rodadas e o último resultado, além de 1.055 medições D1. A integridade dos 111 objetos listados foi conferida comparando ETag listado com MD5 do corpo; SHA-256 de todos os corpos está no recibo. O D1 confirmou zero linhas escritas.

Observado = leitura do mesmo posto no instante EXATO do alvo, em metros. SACE/SGB prevalece no empate como no site; ANA/SNIRH é preservada em paralelo e usada quando falta SACE. Não se utiliza DCRS Barra do Guaporé como se fosse a régua de Muçum. ANA e SACE concordam em todos os pares horários de Muçum com ambas disponíveis nesta análise.

Erros com sinal positivo indicam superestimação. O padrão dominante em Muçum foi prever uma descida mais lenta do que a observada. Maior diferença da seleção por rodada: alvo 22/09 15h, emissão 09h46, previsto 15,6504446649 m contra observado 13,16 m; erro +2,4904446649 m. Sua antecedência real é aproximadamente 5h14, embora seja o alvo nominal de 6h.

Na tabela de 22/09 00h–20h com antecedência mínima real de 1h, são 21 pares: MAE 0,3271719767 m e 17/21 dentro de ±0,50 m. O sumário geral desse horizonte contém também 21/09 23h: 22 pares, MAE 0,3223128574 m e 18/22 dentro de ±0,50 m. Não misturar os denominadores.

O D1 tem retenção de aproximadamente 48h; as tabelas consultadas não preservam os códigos de qualidade do nível nem certificam datum. Os resultados são uma auditoria retrospectiva desse período, não certificação da meta de 98%. A antecedência nominal 1h nesta seleção variou de cerca de 6 a 43 minutos reais. Nenhum alvo publicado da amostra oferece 6h reais completas de antecedência.
