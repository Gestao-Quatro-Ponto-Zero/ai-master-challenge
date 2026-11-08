# Build do frontend (modo API real) e servidor Caddy com os arquivos estáticos.
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ENV VITE_API_MODE=http VITE_API_BASE_URL=/api/v1 NODE_OPTIONS=--max-old-space-size=768
RUN npm run build

FROM caddy:2-alpine
COPY --from=build /app/dist /srv
