# ---------- Build stage ----------
FROM node:20-bullseye-slim AS build-stage

WORKDIR /app

ARG VITE_APP_API_URL
ENV VITE_APP_API_URL=$VITE_APP_API_URL

COPY package.json bun.lockb ./

# bun o‘rniga npm ishlatamiz container ichida
RUN npm install

COPY . .

RUN npm run build


# ---------- Runtime stage ----------
FROM nginx:stable-alpine AS runtime

COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1
