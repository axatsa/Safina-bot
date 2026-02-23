FROM node:20-alpine

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm
RUN pnpm install

COPY . .

ENV ESBUILD_WORKER_COUNT=1
RUN pnpm build
