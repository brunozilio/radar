# Reconstituído a partir do histórico OCI da imagem original.
# syntax=docker/dockerfile:1

# Compile no host nativo (inclusive em Macs ARM) e gere a imagem final para a
# arquitetura solicitada pela Cloudflare. O artefato .next é independente da
# arquitetura; as dependências nativas de runtime são instaladas no estágio final.
FROM --platform=$BUILDPLATFORM node:22.23.1-bookworm-slim AS builder

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

COPY package.json package-lock.json ./
RUN npm ci

COPY app ./app
COPY lib ./lib
COPY public ./public
COPY scripts ./scripts
COPY next-env.d.ts next.config.ts postcss.config.mjs tsconfig.json ./

RUN npm run build

FROM node:22.23.1-bookworm-slim AS runtime

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    LIVE_WS_PORT=3001 \
    MONITORAMENTO_HOST=0.0.0.0 \
    MONITORA_DATA_DIR=/app/.data

COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force

COPY --from=builder --chown=node:node /app/.next ./.next
COPY --chown=node:node app ./app
COPY --chown=node:node lib ./lib
COPY --chown=node:node public ./public
COPY --chown=node:node scripts ./scripts
COPY --chown=node:node certs/lets-encrypt-gen-y-rsa-chain.pem ./certs/lets-encrypt-gen-y-rsa-chain.pem
ENV NODE_EXTRA_CA_CERTS=/app/certs/lets-encrypt-gen-y-rsa-chain.pem
COPY --chown=node:node next.config.ts ./next.config.ts
COPY --chown=node:node tsconfig.json ./tsconfig.json

RUN mkdir -p /app/.data/media && chown -R node:node /app/.data

USER node
EXPOSE 3000
CMD ["npm", "start"]
