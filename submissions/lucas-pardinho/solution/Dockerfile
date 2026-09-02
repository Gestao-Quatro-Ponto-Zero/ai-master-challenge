# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS analytics

WORKDIR /work
COPY analytics ./analytics
COPY data/raw ./data/raw

RUN python analytics/pipeline.py \
      --data-dir data/raw \
      --normalized-dir data/normalized \
      --output-dir generated


FROM node:22-alpine AS web-dependencies

WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci


FROM node:22-alpine AS web-builder

WORKDIR /app/web
ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production \
    GENERATED_DATA_DIR=/app/generated \
    ALLOW_SAMPLE_DATA=false

COPY --from=web-dependencies /app/web/node_modules ./node_modules
COPY web ./
COPY --from=analytics /work/generated /app/generated

RUN npm run build


FROM node:22-alpine AS runner

WORKDIR /app/web
ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000 \
    GENERATED_DATA_DIR=/app/generated \
    ALLOW_SAMPLE_DATA=false

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 --ingroup nodejs nextjs

COPY --from=web-builder --chown=nextjs:nodejs /app/web/.next/standalone ./standalone
COPY --from=web-builder --chown=nextjs:nodejs /app/web/.next/static ./standalone/web/.next/static
COPY --from=analytics --chown=nextjs:nodejs /work/generated /app/generated

USER nextjs
EXPOSE 3000

WORKDIR /app/web/standalone/web
CMD ["node", "server.js"]
