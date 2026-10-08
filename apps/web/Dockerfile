# syntax=docker/dockerfile:1.7
# Targets: dev (vite dev server), web (prod: Caddy + built static files).

ARG NODE_IMAGE=node:24-alpine
ARG CADDY_IMAGE=caddy:2-alpine
ARG PNPM_VERSION=10.34.6

# ---------- deps ----------
FROM ${NODE_IMAGE} AS base
ARG PNPM_VERSION
ENV PNPM_HOME=/pnpm \
    PATH=/pnpm:$PATH
RUN npm install -g pnpm@${PNPM_VERSION} && mkdir -p /pnpm/store && chown -R node:node /pnpm
WORKDIR /app
RUN chown node:node /app
USER node
COPY --chown=node:node package.json pnpm-lock.yaml ./
RUN --mount=type=cache,target=/pnpm/store,uid=1000,gid=1000 \
    pnpm install --frozen-lockfile --store-dir /pnpm/store --package-import-method copy

# ---------- dev ----------
FROM base AS dev
EXPOSE 5173
CMD ["pnpm", "dev"]

# ---------- build ----------
FROM base AS build
COPY --chown=node:node . .
RUN pnpm build

# ---------- web (prod, default target) ----------
FROM ${CADDY_IMAGE} AS web
# Official caddy binary has cap_net_bind_service, so it can bind :80/:443 as non-root.
RUN addgroup -S -g 10001 caddy \
 && adduser -S -u 10001 -G caddy -H -s /sbin/nologin caddy \
 && chown -R caddy:caddy /data /config
COPY --from=build /app/dist /srv
USER caddy
