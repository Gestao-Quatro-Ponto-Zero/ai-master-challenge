FROM node:22.13.1-alpine AS build
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html vite.config.ts tsconfig.json tailwind.config.js postcss.config.js ./
COPY src ./src
RUN npm run build

FROM nginx:1.27.4-alpine
COPY nginx-main.conf /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN mkdir -p /tmp/nginx && chown nginx:nginx /tmp/nginx
COPY --from=build /web/dist /usr/share/nginx/html
EXPOSE 5173
HEALTHCHECK --interval=20s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:5173/ || exit 1
USER nginx
ENTRYPOINT ["nginx", "-g", "daemon off;"]
