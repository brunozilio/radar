# Vazões de2018: coleta e conferência

Foram recuperados três arquivos mensais públicos do ONS, de agosto, setembro e outubro/2018, identificados no catálogo preservado. A extração conserva6.621 registros de14deJulho, MonteClaro eCastroAlves, com campos textuais, arquivo e índice de origem. Fontes e recibos estão em `../auditoria-qi-radar-2018-20260922/`.

As duas semanas centrais têm336 origens horárias. Sob a hipótese declarada de atraso60min e expiração90min após a consulta, todas as6.048 buscas (18pororigem) encontram valores finitos. Não houve preenchimento, troca por componentes, alteração de zeros ou arredondamento de23:59. Neste acervo dos três meses, não há Q/Izero, negativo ou ausente, nem resíduo de defluência menos soma dos componentes superior a1m³/s. Esse teste aritmético não comprova correção física ou publicação histórica dos dados.

Agosto e setembro têm744/720 linhas porusina. Outubro tem743 porusina: falta o rótulo20/10/2018 23:59 em relação ao padrão diário recebido de01h..23h e23:59. A ausência está fora das janelas estudadas; não se corrigiu seu horário nem sua causa foi inferida.

A conferência direta dos CSVs brutos reproduziu todos os6.621 registros extraídos e verificou as6.048 consultas, proveniência e datas. Passaram36.884 verificações. Timestamps permanecem literais, sem certificação de fuso, latência de publicação, regime ou qualidade hidráulica. Nenhum treino ou inferência foi executado; cobertura não é assertividade.
