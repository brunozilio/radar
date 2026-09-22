# Verificação independente — matrizes reservadas 2021/2022

Todas as 264.960 células foram reconstruídas a partir das séries ANA e dos CSVs ONS literais, sem importar builders ou helpers operacionais. Níveis e Q/I coincidem exatamente. A chuva foi recalculada por soma direta da sobreposição de intervalos encerrados; tolerância 2e-10 e máscaras NaN idênticas.

Maior diferença absoluta: 6.394884621840902e-13. Passaram 484 verificações. Também foram conferidos os arrays de 15 minutos, atrasos, ordem das 120 colunas, bases, truth explicitamente aprovado e rastros de origem.

Ano 2021: 744 origens, 20357 células NaN, 744 bases finitas, 744 níveis contemporâneos aprovados e 13392 consultas Q/I; 1 origem(ns) com algum zero preservado.
Pares base/alvo h1/h6/h12: 743/738/732.
Ano 2022: 1464 origens, 35596 células NaN, 1458 bases finitas, 1463 níveis contemporâneos aprovados e 26352 consultas Q/I; 0 origem(ns) com algum zero preservado.
Pares base/alvo h1/h6/h12: 1457/1452/1446.

Alvos são exatos e permanecem dentro da janela de cada ano: os últimos h ficam fora do conjunto de avaliação por fronteira, sem cruzar anos. As duas cópias de diagnósticos Q/I coincidem com as fontes. Os 39.744 rastros Q/I e os 8.832 rastros de nível foram conferidos; flags não alteram valores. A ausência de campos auxiliares não criou filtro adicional.

A auditoria não carregou modelos nem executou inferência, treino, cálculo de erros ou consultas externas. A igualdade numérica não certifica disponibilidade histórica, fuso, datum ou regime físico. ANA ALL-QC foi conferida contra XML na coleta; aqui os hashes foram verificados e a seleção/integração foi reconstruída. ONS usa CSVs literais previamente auditados e hashes originais, sem nova decodificação do arquivo de origem.
