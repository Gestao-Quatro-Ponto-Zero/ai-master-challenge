# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — Python analysis
# Roda os scripts de análise que geram diagnostic_output.json e classifier_output.json
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS analysis

WORKDIR /analysis

RUN pip install --no-cache-dir pandas numpy scipy scikit-learn

COPY apps/support-triage/data/    ./data/
COPY apps/support-triage/scripts/ ./scripts/

RUN python3 scripts/generate_diagnostic.py \
 && python3 scripts/generate_classifier.py

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — Node.js build
# Instala dependências do workspace pnpm e builda o Next.js
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-slim AS build

RUN npm install -g pnpm@10.32.1

WORKDIR /workspace

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY packages/ ./packages/
COPY apps/support-triage/ ./apps/support-triage/

# JSONs gerados pelo stage de análise
COPY --from=analysis /analysis/data/diagnostic_output.json  ./apps/support-triage/data/
COPY --from=analysis /analysis/data/classifier_output.json  ./apps/support-triage/data/

RUN pnpm install --frozen-lockfile

RUN pnpm --filter @challenge/support-triage build

# ─────────────────────────────────────────────────────────────────────────────
# Stage 3 — Runtime
# Node.js minimal com app compilada + dados
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-slim AS runtime

WORKDIR /workspace

# node_modules do workspace (inclui DuckDB binaries nativos)
COPY --from=build /workspace/node_modules        ./node_modules
COPY --from=build /workspace/packages            ./packages
COPY --from=build /workspace/package.json        ./

# App compilada
COPY --from=build /workspace/apps/support-triage/.next        ./apps/support-triage/.next
COPY --from=build /workspace/apps/support-triage/node_modules ./apps/support-triage/node_modules
COPY --from=build /workspace/apps/support-triage/package.json ./apps/support-triage/
# Dados: CSVs (DuckDB em tempo real) + JSONs (análise Python)
COPY --from=build /workspace/apps/support-triage/data ./apps/support-triage/data

WORKDIR /workspace/apps/support-triage

EXPOSE 3003

ENV NODE_ENV=production
ENV PORT=3003

CMD ["./node_modules/.bin/next", "start", "-p", "3003"]
