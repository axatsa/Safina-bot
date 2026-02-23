# Dockerfile (frontend build)
FROM node:20-slim AS build

WORKDIR /app

# Copy package.json and pnpm-lock
COPY package.json pnpm-lock.yaml ./

# Install pnpm
RUN npm install -g pnpm

# Install dependencies
RUN pnpm install

# Copy all source
COPY . .

# Build
ARG VITE_APP_API_URL
RUN pnpm build

# ---------- Runtime stage ----------
FROM nginx:alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
