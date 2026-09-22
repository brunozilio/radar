# Vazões ONS para as reservas de 2021 e 2022

Cinco GETs públicos HTTP 200, sem retry, coletaram os CSVs de abril/maio de
2021 e abril/maio/junho de 2022. URLs e licença do catálogo ONS, horários,
headers e hashes permanecem em collection-plan.json/source-manifest.json.
Os arquivos completos foram preservados; somente 14 de Julho, Monte Claro
e Castro Alves foram extraídas para os CSVs de trabalho, com todos os campos
literais e proveniência. São 10.941 registros selecionados.

O verificador separado em ../verificacao-ons-reserva-2021-2022-20260922/
releu 556.183 registros dos CSVs brutos e reconciliou integralmente os
10.941 registros selecionados. Também conferiu todas as 39.744 consultas
de Q/I: 18 consultas por origem, incluindo os recuos de Q usados pelo modelo,
em 744 origens de maio de 2021 e 1.464 de maio–junho de 2022.

Todas essas consultas têm valor finito sob o contrato congelado de atraso
de 60 minutos e idade máxima de 90 minutos após a consulta. Isso não
certifica publicação em tempo real ou exatidão física dos valores. Há um
zero de afluência de 14 de Julho em 26/05/2021 às 17h, que entra na consulta
da origem seguinte; outro zero de afluência de Castro Alves, em 24/04/2021,
fica fora das origens de avaliação. Nenhum zero foi substituído ou rejeitado.
O limiar de resíduo de componentes >1 m³/s é diagnóstico, não QC oficial.

O padrão literal dos arquivos contém horas 01–23 e 23:59. Três posições
desse padrão estão ausentes: Castro Alves em 30/04/2021 às 14h, Monte Claro
em 24/04/2022 às 07h e Castro Alves em 14/04/2022 às 22h. Nenhuma altera as
39.744 consultas das origens reservadas. Não transformamos 23:59 em meia-noite
nem declaramos esse padrão como convenção temporal certificada.

Não houve treinamento, inferência, avaliação de erros ou promoção. As
janelas reservadas continuam fora do ajuste. O candidato e o controle
foram fixados separadamente antes de qualquer inferência; será necessário
conferir e congelar também as matrizes de entrada antes da comparação.
