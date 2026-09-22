# ANA: semântica de aprovação ainda pendente

Pesquisa delimitada concluída em 2026-09-21T23:14:25.506393+00:00.

Os dois scripts consultam `DadosHidrometeorologicosGerais`, não a operação sem sufixo. O ledger usa o texto literal `CQ_NivelFinal = Dado aprovado` e preserva revisões por recibo. Isso identifica a condição publicada pela origem; não comprova revisão humana, consistência histórica HidroWeb, precisão instrumental ou caráter definitivo.

Três consultas direcionadas não encontraram documentação específica. O [manual primário legado ANA](https://www.ana.gov.br/telemetria1ws/Telemetria1ws.pdf), atualizado em junho/2013, trata `DadosHidrometeorologicos` na seção 2.1 (página 4) e `HidroSerieHistorica` na seção 2.9 (páginas 18–21). Os campos descritos para a primeira operação não incluem CQ_NivelFinal. A existência de nivelConsistencia na outra operação não demonstra equivalência entre esses contratos. Esta é uma verificação de escopo, não uma resolução da semântica de qualidade. O manual já havia sido citado em fuso-e-referencia.md; não é descoberta documental nova. Seus bytes foram preservados nesta pasta para a auditoria pontual.

A página de ajuda da operação Gerais já arquivada contém modelos SOAP com retorno XML genérico. A pesquisa local anterior trata fuso, datum e interfaces históricas; não localizei nela dicionário de aprovação telemétrica. Portanto a lacuna continua aberta. Nenhuma proposta de converter aprovação em classe de consistência, aceitar registros não aprovados, excluir erros ou alterar placar.

Unidades, fuso, datum, qualidade, lacunas, licença, URL, horário real de coleta e SHA256 constam em source-manifest.json. Nenhuma série nova foi coletada. Documentação anterior permanece referenciada por hash em prior-evidence.json. Sem alterações em código, ledger, modelos, treinamento ou produto; sem mensagens externas ou deploy.
