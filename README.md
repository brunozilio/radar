# Radar Taquari — projeto original recuperado

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
