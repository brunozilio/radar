# Radar Taquari — projeto original recuperado

## Modelo de previsão de Muçum

O painel **Modelo de previsão** publica somente as próximas **6 horas** do modelo estatístico existente,
identificado como **experimental**, com uma explicação acessível no próprio site.
O Radar é o único modelo ativo no site e no acompanhamento horário. O HGE/ARNO
foi retirado dos cálculos, relatórios ativos e pacote de execução; os recibos
históricos permanecem preservados. Não há comprovação de98% de precisão.

O Cron Trigger da Cloudflare executa `*/15 * * * *` e chama, com autenticação
interna, `/api/internal/projection-refresh`. O processo calcula no Container,
sem depender de uma aba aberta ou de um computador local. Cada hora de referência
abre uma rodada; os cálculos de15em15min atualizam essa rodada. A consulta de uma
rodada anterior retorna sua última revisão salva, preservando os horários-alvo
originais. Não se inventam rodadas para horas sem cálculo bem-sucedido.

`/api/projection` serve o último resultado e a lista de rodadas; `?round=ISO_UTC`
consulta uma rodada específica. R2 conserva `projection/rounds/`, cada emissão
em `projection/issues/`, o histórico incremental e a última auditoria completa.
Falhas de coleta, dados inválidos, alvos já vencidos, timeout ou falha de
persistência preservam a previsão anterior. A tela sinaliza atualização atrasada.

O empacotador `npm run projection:package` copia somente código e insumos públicos
necessários para `projection-runtime/`, com hashes. O Docker inclui Python3.12
e as dependências fixadas. Corte de treinamento e hiperparâmetros permanecem
iguais aos do modelo estatístico horário existente; a referência continua horária.
A coleta e os cálculos usam armazenamento separado da automação de pesquisa local.
Os 6 artefatos em `model-artifacts/forecast-6h-v1` foram treinados com referência de
21/09/2026 às21h BRT e corte de alvos anterior a21/09. O cron usa inferência com
esses artefatos congelados e hashes verificados, sem retreinar ou aumentar os
recursos do Container. A versão aparece na resposta e na auditoria de cada emissão.
São seis alvos horários contados a partir da referência da rodada; o horário real
de emissão também é preservado. Nenhuma previsão além de6h é publicada na API ou tela.

Validação isolada do cálculo, sem gravar em serviços externos:

```sh
npm run projection:package
PROJECTION_PYTHON=/caminho/python MONITORA_DATA_DIR=/tmp/projection-test node --experimental-strip-types -e 'import("./lib/projection-server.ts").then(m => m.refreshProjection())'
```

Projeto independente reconstruído a partir dos artefatos que permaneceram no
deploy original da Cloudflare.

## Conteúdo recuperado

- `app/`: frontend original e rotas HTTP do Next.js;
- `lib/`: regras de rios, chuva, barragens, alertas, mídia e persistência;
- `scripts/worker.ts`: servidor de coleta, processamento, WebSocket e tarefas
  em segundo plano;
- `cloudflare/index.js`: bundle exato do Worker de borda, incluindo D1, R2,
  Durable Object, Container e Web Push;
- `database/public-monitoring-data.sql`: backup das leituras públicas, sem
  assinaturas, endpoints ou chaves push;
- `public/`: PWA, ícones, imagem social e service worker originais.

Os arquivos de produto vieram diretamente da imagem do Container. O
`Dockerfile`, o `wrangler.jsonc` e os arquivos de configuração de desenvolvimento
foram reconstituídos porque esses arquivos não estavam copiados na imagem.

## Executar localmente

Requer Node.js 22.13 ou superior.

```bash
npm ci
npm run dev
```

O site fica disponível em `http://localhost:3000`. Para validar uma versão de
produção:

```bash
npm run build
npm start
```

## Previsão de Encantado

O painel de previsão permite alternar entre **Muçum** e **Encantado**. Encantado
usa um modelo próprio (`encantado-6h-v1`), com seis alvos horários na régua ANA
`86720000`. O modelo aprende a variação do nível a partir das medições de
Encantado e Muçum e de suas tendências nas últimas oito horas. Não converte a
régua de Muçum em Encantado nem reaproveita a previsão de Muçum. Chuva prevista
e operação de barragens não são entradas diretas deste modelo.

A consulta `/api/projection?station=encantado` retorna a previsão da cidade;
sem `station`, a API mantém Muçum como padrão. O parâmetro `round` continua
disponível. Rodadas anteriores à inclusão de Encantado retornam `projection:
null` para essa cidade. Os documentos existentes permanecem compatíveis.

O mesmo cálculo agendado executa a inferência congelada de Encantado, com uma
coleta adicional da ANA. Observações acima de 90 minutos de idade na referência,
histórico recente incompleto, níveis fora do intervalo observado no treino ou
falhas de integridade impedem a nova emissão. Falhas de Encantado preservam sua
última emissão com o horário original e um sinal de atraso, mantendo Muçum.

Os artefatos e hashes ficam em `model-artifacts/encantado-6h-v1`; a receita de
treino é `scripts/hydro_train_encantado.py`. A avaliação cronológica separa
treino em 2025, validação de janeiro a junho de 2026 e teste de julho até
20/09/2026. O treino final usa somente alvos anteriores a 21/09/2026. Cenários
de atraso de até 90 minutos são repetidos em todos os períodos; essas repetições
não representam observações independentes, e não comprovam os horários reais
de publicação históricos.

No teste, o erro absoluto médio foi de 0,047 m em 1 hora a 0,302 m em 6 horas,
inferior à persistência em todos os horizontes. Em variações de pelo menos
0,5 m, os erros médios foram de 0,259 m a 0,473 m. Isso não é garantia de erro
futuro. O modelo é experimental e ainda não foi avaliado nas cheias extremas de
2023/2024. A documentação de identificação da estação está no
[repositório oficial do SGB](https://rigeo.sgb.gov.br/items/c6e68994-46da-46d0-a4d1-53700ea45921).

Validação local, sem publicar:

```sh
python -m unittest discover -s scripts -p 'test_hydro_encantado.py'
npm test
npm run projection:package
npm run build
```

## Santa Tereza na previsão e Encantado nos níveis do rio

O seletor de previsão também inclui **Santa Tereza**, com seis alvos horários
na régua da cidade (`86472600`). A entrada a montante é a Linha José Júlio
(`86472000`); o modelo não usa a régua de Muçum como alvo. Os artefatos próprios
estão em `model-artifacts/santa-tereza-6h-v1` e entram no mesmo pacote de
inferência. A API aceita `?station=santa-tereza`, inclusive com `round`.
Cada cidade conserva sua própria última emissão e seu aviso de atraso quando
o cálculo falha, sem trocar os valores ou horários entre estações.

O modelo foi avaliado com a mesma divisão cronológica e os mesmos cenários de
atraso de Encantado. As métricas e os hashes dos insumos estão em
`outputs/santa-tereza-model-v1/validation.json`. É uma previsão experimental,
sem avaliação nas cheias extremas de 2023/2024. Para reproduzir o treino local:

```sh
python scripts/hydro_train_encantado.py --station santa-tereza
```

**Encantado** aparece também em “Níveis do rio”, com leitura, horário, fonte,
tendência e gráfico histórico. A coleta consulta a ANA (`86720000`) e o ponto 2
do SACE (`taquari_2_cota.csv`), selecionando a observação mais recente. A
identidade do ponto foi conferida no
[GeoJSON público do SACE](https://sace.sgb.gov.br/taquari/api/geojson/point).
O cartão usa a régua de Encantado e não define novos limiares de alerta.
São agora seis estações ANA/SACE na coleta dos níveis, além da Rede RS.

## Fontes de alertas

Os alertas ativos para Muçum são coletados de duas fontes oficiais:

- avisos meteorológicos do INMET, filtrados pelo geocódigo IBGE `4312609`;
- avisos da Defesa Civil do RS, analisados pelo conteúdo completo da publicação
  e pela vigência exibida no card oficial quando necessário.

A indisponibilidade de uma fonte não interrompe a coleta da outra. A API
identifica a origem, preserva o link oficial e só oferece imagem quando ela foi
armazenada para aquele aviso.

## Radar de Concórdia

As imagens do radar `CHP` são obtidas do SIFAP da Defesa Civil de Santa
Catarina. Como o servidor oficial não entrega toda a cadeia TLS, o Container
inclui apenas os certificados intermediários públicos da Let’s Encrypt
necessários para completar e validar essa cadeia. A validação TLS permanece
ativa; nenhuma conexão usa `NODE_TLS_REJECT_UNAUTHORIZED=0`.

## Cloudflare

O `wrangler.jsonc` descreve o Worker público, o Container e os bindings D1/R2
do ambiente `radar.brunozilio.com`. Os identificadores de recursos não são
credenciais. Os valores de `PUSH_INTERNAL_SECRET`, `VAPID_PRIVATE_KEY` e
`VAPID_PUBLIC_KEY` ficam somente na Cloudflare e nunca devem ser adicionados ao
repositório.

Validação e deploy:

```bash
npm test
npm run lint
npm run cloudflare:dry-run
npm run cloudflare:deploy
```

O Dockerfile executa o build do Next.js dentro da própria imagem, portanto o
deploy também funciona a partir de um clone limpo. Para instalar este projeto
em outra conta Cloudflare, crie novos recursos D1/R2 e configure os três secrets
com `wrangler secret put` antes de publicar.

Os valores originais dos secrets não podem ser exportados da Cloudflare. O
bundle, os metadados e os dados públicos recuperáveis permanecem preservados;
assinaturas, endpoints e chaves push não fazem parte do backup versionado.

## Níveis dos rios: ANA + SACE

As seis estações fluviométricas consultam ANA/SNIRH e SACE/SGB em paralelo a
cada minuto. Cada fonte é armazenada assim que responde, e a API e os gráficos
escolhem a medição pelo horário observado, nunca pelo horário da consulta.
Em horários iguais, o SACE tem prioridade determinística; cada instante aparece
uma única vez no gráfico. A tela identifica a fonte da leitura atual.

As séries ficam separadas nas tabelas já persistidas: SACE em `sace_readings`
e ANA em `river_readings`, com o código da estação e fonte `ANA/SNIRH`. Falhas,
respostas vazias e níveis/horários inválidos não apagam as últimas leituras.
Os sensores diferentes da Rede RS continuam independentes.

O serviço público da ANA pode ter atraso; não há garantia de que uma fonte
sempre anteceda a outra. O endpoint compatível `/api/sace-mucum` também retorna
a medição mais recente entre as duas fontes e identifica sua origem.

## Disponibilidade de radar e satélite

Radar Porto Alegre, Radar Concórdia e satélite têm carregamento e reprodução
independentes: horários diferentes ou falhas de um produto não ocultam os outros.
Durante respostas vazias ou falhas transitórias, a tela preserva o último lote
válido, respeitando o limite de atualização de 90 minutos e o horário real da
imagem. As APIs selecionam os quadros mais recentes antes de limitar o lote.

A coleta do satélite prioriza as últimas três horas, da mais recente para a
mais antiga. Downloads falhos são isolados por quadro, e cada imagem nova é
publicada imediatamente, sem aguardar o restante do lote ou o outro provedor.
INMET e CPTEC continuam independentes. O radar também tolera falhas individuais
na consulta e no download de imagens.

O satélite também consulta o setor sul da América do Sul da NOAA/GOES-19,
canal infravermelho 13. A API escolhe a sequência do provedor mais recente,
sem misturar projeções. Imagens NOAA mostram a identificação da fonte e não
recebem a sobreposição geográfica calibrada para INMET/CPTEC.
