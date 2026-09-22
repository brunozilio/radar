# Matrizrecente — âncoraMuçum exata1h eQCestrito

**13535 checks passaram.** Foram conferidas12912 origens×120colunas, de01/04/2025 até20/09/2026 23h, contra as fontes strict/latest já seladas e a base original. A matriz contém12835bases finitas,12836níveis truth aprovados e28756NaNs. Todas as colunas6..119 coincidem **exatamente** com as120colunas observadas da referência congelada; nenhuma diferença numérica ou arredondamento nesta comparação.

Muçum foi reconstruído diretamente de `strict-latest/ana-86510000.npz`: somente timestamps dehora inteira são usados nos preditores, consulta exataO−1h, semcarregamento ou salto de valor inválido. A colunaMu0,5h é sempreNaN; dH1/2/4/8 seguem os extremos horários e divisão nominal correspondente. As primeiras24colunas também foram reconstruídas das quatro fontes de nível, com atrasos/expiração especificados. Truthpermanece leitura horária exataQCestrito e coincide comtruthoriginal; a mudança da âncora não altera alvos.

O grid15min, campos raw e demais campos presentes no quarter-hour foram comparados ao snapshotoriginal: apenas MuH atrasado difere porcontrato. Q/I e chuva ficaram exatos; a integração regional não foi reexecutada nesta auditoria, pois asfontes estritas haviam sido rastreadas aos XMLs e os derivados presentes coincidem exatamente com o snapshot. Não confundir fidelidade numérica com demonstração de publicação histórica ou datum.

`feature-catalog.csv` registra nomes/ordem/cobertura; `mucum-source-traces.csv` traz todas as12912 consultas. Os hashes dasfontes/caches reconstruídos anteriormente e dos manifests foram conferidos; a auditoria não modifica essesartefatos.

## Suporte à comparação pareada, semfit

Foram reconstituídas24máscaras recentes(fase×h) e24máscaras2018(janela×h), salvas em `expected-training-masks.npz`. `training-support.csv` contém24planos com número e soma depesos deamostras recentes/adicionais, configurações, corte e última data-alvo. `evaluation-target-support.csv` preserva os24denominadores/ausências e total102084linhas agendadas. Os targets de2018 são deslocados dentro de cada janela; osrecentes dentro da sua própria série. Não há ponte sobre ohiato, filtro complete24 ou máscara favorável decheia.

`code-review.md` registra a revisão estática do script/protocolo de48ajustes planejados. Não foi encontrado bloqueio concreto de alinhamento, causalidade temporal ou assimetria entre famílias. As assertivas adicionais dehashauditoria2018/configuração/contagens foram lidas. A aprovação deauditoria é conferida pelo coordenador; o script exige oarquivo e preserva seuhash, mas não interpreta sozinho oJSON `passed`.

Este relatório não verifica modelos ainda não ajustados nem prova quaisvetores serão efetivamente consumidos pelo otimizador. Ajustes/predições futuros precisam deauditoria deartefatos própria. A matriz é nova receita decontrole, não reprodução exata dos modelos operacionais anteriores. Os mesmos contratos devem ser aplicados ao controle eao candidato com2018. Nenhumfit, inferência, consulta de rede ou alteração operacional nesta auditoria; meta98% não aferida.

`verification.json` contémchecks/hashes; `verify.py` reproduz a análise sem importar código operacional. Manifesto/check final sela osartefatos desta pasta. Aspequenas correções do próprio verificador durante suaexecução não alteraram fontes oumatriz. Arquivos finais e estáveis após oaviso deconclusão.
