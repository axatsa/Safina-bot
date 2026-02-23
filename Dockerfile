FROM node:20-bullseye-slim AS build-stage

WORKDIR /app
RUN corepack enable
ENV NODE_OPTIONS="--max-old-space-size=2048"

ARG VITE_APP_API_URL
ENV VITE_APP_API_URL=$VITE_APP_API_URL

COPY package.json pnpm-lock.yaml ./

RUN --mount=type=cache,id=pnpm-store,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile

COPY . .

RUN pnpm build


FROM nginx:stable-alpine AS runtime
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
