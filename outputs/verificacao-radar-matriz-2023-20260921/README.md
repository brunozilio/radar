# Auditoria independente da matriz observada de 2023

Todas as 86.400 células dos 120 campos foram reconstruídas: 17.280 de níveis, 15.120 de Q/I e 54.000 de chuva. Níveis e Q/I coincidem exatamente; chuva coincide até 2e-10 mm, inclusive máscaras de NaN. São 720 origens, 506 bases, 505 níveis contemporâneos e 23.799 células ausentes. Os 2.880 rastros de níveis e os hashes dos insumos conferem.

A chuva foi integrada por sobreposição de intervalos completos, diretamente das séries ANA ALL-QC, sem helpers operacionais. A última linha ausente não é ignorada na consulta de níveis; atrasos e expiração seguem o protocolo. Q/I mantém 23:59 literal, atraso de 60 min e expiração de 90 min após a consulta.

Os pares h1/h6/h12 são 503/493/481. O par extra de 12h é 01/09 00h → 12h: base aprovada de 0,86 m exatamente em 31/08 23h45, agora incluída pelo aquecimento de agosto; alvo aprovado de 1,43 m. Não decorre da tolerância asof e não foi imputado.

Limites: a normalização ALL-QC foi auditada anteriormente contra XML; aqui verificamos hashes, seleção, integração e proveniência específica do par extra. Atrasos históricos continuam presumidos, fuso/datum e comparabilidade operacional não certificados. Nenhum treino, consulta nova ou promoção.
