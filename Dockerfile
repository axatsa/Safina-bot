# ---------- Build stage ----------
FROM oven/bun:1 AS build-stage

WORKDIR /app

ARG VITE_APP_API_URL
ENV VITE_APP_API_URL=$VITE_APP_API_URL

# faqat dependency fayllarni ko'chiramiz (cache optimal bo'lishi uchun)
COPY package.json bun.lockb ./

RUN bun install --frozen-lockfile

# qolgan fayllarni ko'chiramiz
COPY . .

RUN bun run build


# ---------- Runtime stage ----------
FROM nginx:stable-alpine AS runtime

COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1
