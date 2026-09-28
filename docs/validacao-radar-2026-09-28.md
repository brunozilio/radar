# Validação do Radar — 28/09/2026

Verificação feita entre 13h20 e 13h45 (horário de Brasília) no código local e em
`https://radar.brunozilio.com`. Os valores ao vivo abaixo são um retrato desse
período, não um estado permanente.

Atualização às 14h23: a versão `129eab1d-b669-4006-b8da-4d6f6a662ae1`
foi implantada. A página pública deixou de renderizar a seção de câmeras;
as correções da leitura atual da Rede RS e do aviso de previsão desatualizada
foram incluídas. As observações abaixo descrevem a auditoria anterior à publicação.

Alterações locais do mapa de chuva apareceram no workspace durante a auditoria.
Elas foram preservadas e entraram no build final, mas os testes de interface no
site em produção não verificam esses ajustes ainda não publicados.

## Resultado

- `npm test`: 74 testes passaram, incluindo a nova regressão para horários com
  fusos diferentes na Rede RS.
- `npm run lint`, `npx tsc --noEmit` e `npm run build`: concluídos. O build ainda
  emite dois avisos de rastreamento amplo de arquivos em `projection-server.ts`.
- Na produção, carregaram a página, as APIs de níveis, chuva, barragens,
  alertas, previsão, radares e satélite. As imagens consultadas retornaram HTTP
  200 com tipo de mídia apropriado. O manifesto, o service worker de push e a
  chave pública de notificações também responderam.
- Na interface, abrir/fechar alertas, mudar as janelas de níveis e chuva,
  consultar um marcador do mapa, ampliar o radar e o mapa de chuva e abrir a
  explicação da previsão funcionaram.
- Uma conferência de invariantes ao vivo encontrou zero violações entre sete
  sensores de rio, três usinas, quatro alertas ativos, cinco alvos da previsão
  e os lotes de 13/11/7 imagens dos dois radares e do satélite: horários válidos
  e ordenados, valores finitos, vigência dos alertas e horizonte de até seis
  horas.
- Requisições inválidas de estação, rodada e mídia foram recusadas; o endpoint
  interno de recálculo recusou uma chamada sem autenticação.

## Conferência das informações

- As seis réguas SACE/ANA da API foram comparadas às séries oficiais. Em
  13h15, a [ANA](https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais)
  registrava 519 cm em Muçum e 434 cm em Encantado, valores exibidos pela API;
  seus registros eram mais recentes que os CSVs do
  [SACE](https://sace.sgb.gov.br/api/dados/taquari_3_cota.csv). Os quatro
  sensores restantes coincidiam em horário e nível com seus CSVs SACE.
- As defluências das três usinas às 13h coincidiam com a CERAN:
  [Castro Alves](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHCA.php)
  672,01 m³/s, [Monte Claro](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHMC.php)
  1.325,14 m³/s e [14 de Julho](https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHQJ.php)
  793,81 m³/s.
- Os limites exibidos para a régua de Muçum (atenção 5 m, alerta 9 m,
  inundação 18 m) coincidem com [publicação do SGB](https://rigeo.sgb.gov.br/items/6ddd986f-ea37-4187-9abd-660cf1dfb257).
- O [aviso 55862 do INMET](https://avisos.inmet.gov.br/55862) tinha severidade
  “Perigo”, vigência até 28/09 às 23h59 e incluía Muçum (geocódigo 4312609),
  conforme exibido no Radar.

## Achados e correções locais

1. `/api/defesa-civil?mode=current` escolhia a maior *string* de horário. Às
   13h22, isso devolveu a leitura das 13h15 em UTC em vez da leitura mais
   recente, das 13h22 em `-03:00`, já visível em `/api/river-levels`. A consulta
   local agora compara os instantes normalizados e ignora leituras futuras.
2. Depois de 30 minutos sem nova emissão, `/api/projection` marcava a previsão
   como `stale`, mas a interface não mostrava aviso. O painel local agora exibe
   que o último cálculo pode estar desatualizado.
3. O README descrevia previsões de Encantado e Santa Tereza como atuais. Foi
   acrescentado um aviso de estado atual: a previsão pública é só de Muçum;
   as outras cidades continuam em “Níveis do rio”.

As correções acima estão apenas no workspace. O site em produção ainda depende
de uma publicação posterior para recebê-las.

## Pendências observadas

- As duas incorporações em “Câmeras ao vivo” mostraram no YouTube “Vídeo
  indisponível / A gravação dessa transmissão ao vivo não está disponível”.
  Os links ou as transmissões precisam ser revistos.
- As fontes de satélite INMET e CPTEC informavam HTTP 403 na coleta. A NOAA
  estava saudável e as imagens de satélite continuavam disponíveis.
- O PDF do Plano de Contingência de Muçum retornou HTTP 403 a esta sessão,
  assim como a página inicial do município. Não foi possível concluir se o
  bloqueio é geral ou restrito ao ambiente da auditoria.
- Não foi feita inscrição em notificações push nem disparo de alerta de teste;
  entrega real, permissões do navegador e instalação da PWA permanecem sem
  verificação completa. Não houve teste de tela móvel nesta sessão.

## Checagem retrospectiva da previsão

Foram lidas as 12 rodadas hidrométricas mais recentes com seis horas já
observáveis, comparando os alvos horários com a régua 86510000 em
`/api/river-levels?hours=48`. Houve 60 pares; as rodadas e alvos se sobrepõem,
portanto não representam 60 eventos independentes.

| Antecedência nominal | Pares | Erro absoluto médio | Viés médio (previsto − observado) | Maior erro absoluto |
| --- | ---: | ---: | ---: | ---: |
| H+2 | 12 | 0,058 m | −0,030 m | 0,115 m |
| H+3 | 12 | 0,116 m | −0,080 m | 0,246 m |
| H+4 | 12 | 0,206 m | −0,146 m | 0,437 m |
| H+5 | 12 | 0,307 m | −0,228 m | 0,648 m |
| H+6 | 12 | 0,419 m | −0,316 m | 0,816 m |

Nesse recorte de subida, a previsão tendeu a subestimar o nível, sobretudo nos
horizontes maiores. É uma avaliação curta, retrospectiva e sem garantia de
desempenho futuro; não justifica alterar o modelo sem validação adicional.
