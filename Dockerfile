# ---------- Build stage ----------
FROM node:20-bullseye-slim AS build-stage

# workdir
WORKDIR /app

# pnpm va Node settings
RUN corepack enable
ENV NODE_OPTIONS="--max-old-space-size=4096"

# Build-time environment variable
ARG VITE_APP_API_URL
ENV VITE_APP_API_URL=$VITE_APP_API_URL

# Dependency fayllarni copy qilamiz (cache optimal)
COPY package.json pnpm-lock.yaml ./

# pnpm install with cache
RUN --mount=type=cache,id=pnpm-store,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile

# Source code copy qilamiz, node_modules va dist .dockerignore orqali exclude qilinishi kerak
COPY . .

# Build the project
RUN pnpm build

# ---------- Runtime stage ----------
FROM nginx:stable-alpine AS runtime

# Dist fayllarni nginx html folderiga ko'chiramiz
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Port ochish
EXPOSE 80

# Optional healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1
