FROM --platform=$BUILDPLATFORM node:20-bullseye-slim AS build-stage

WORKDIR /app
RUN corepack enable

ARG VITE_APP_API_URL
ENV VITE_APP_API_URL=$VITE_APP_API_URL

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:stable-alpine AS runtime
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]  
