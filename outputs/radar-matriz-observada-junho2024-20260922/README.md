# Matriz experimental observada — junho de 2024

Preparados168 horários de origem de15–21/06/2024, com três dias anteriores para formar variáveis. A matriz contém120 variáveis fixas: níveis e tendências, vazões e tendências, chuva regional e cobertura. As20.160células incluem5.071ausências preservadas. Todos os168níveis-base e alvos no próprio horário são aprovados; nenhuma origem tem as24variáveis de nível completas, pois Linha eCarreiro permanecem ausentes.

A âncora Muçum usa O−15min, idade máxima15min; o aquecimento real acrescenta uma origem válida frente à sondagem de sete dias. Há167/162/156pares disponíveis em1/6/12h, respectivamente, sempre dentro da janela;126alvos≥7m emcada horizonte. Isso mede disponibilidade para um futuro experimento, não acertos de previsão.

Chuvas regionais mantêm pesos e atrasos fixos, exigindo cobertura≥0,5. Prata-Turvo eAltoAntas têm valores emtodos os168horários para asjanelas1/3/6/12/24/48h. Carreiro não atinge esse limiar emnenhuma dessas janelas; suas chuvas regionais ficamNaN. BaixoAntas tem0/5/104/101/93/78origens disponíveis; Tainhas129/128/126/124/119/109. Níveis ausentes não foram convertidos emzero. Os horários :29/:59 de86125000 e intervalos longos deoutros postos permanecem literais antes daintegração.

Vazões são usadas como publicadas, sem corrigir divergências pela soma decomponentes nem descartar linhas retrospectivamente. As37divergências de14deJulho na semana permanecem documentadas naauditoriaONS. Esta política deverá ser igual no controle recente e no candidato acrescido dejunho. Oregime pós-avaria, acontinuidade da régua, o fuso e apublicação histórica seguem sem certificação.

A verificação independente reconstruiu todas as20.160células, bases, alvos,672rastros de nível e3.024consultasONS:8.797checks passaram. Níveis e vazões coincidem exatamente; apenas aritmética dechuva apresenta diferença máxima8,89e−14, dentro da tolerância numérica2e−10. Isso não assegura invariância dequalquer treino futuro deárvores.

Controle preparado em `outputs/radar-matriz-recente-ancora-15min-20260922/`:12.912×120, com1.549.440células idênticas à referência anterior após ocorte predefinido21/09/2026. FiltrosQCanteriores não foram aplicados assimetricamente. Não houve treino, inferência, emissão ou promoção. Um protocolo separado deexperimento ainda é necessário, com mesmosalvos eavaliação em todos oshorizontes. Dados eperíodos jáinspecionados são desenvolvimento, não um teste independente novo.
