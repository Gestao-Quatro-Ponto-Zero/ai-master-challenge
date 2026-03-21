# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — Build
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-slim AS build

RUN npm install -g pnpm@10.32.1

WORKDIR /workspace

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY packages/ ./packages/
COPY apps/lead-scorer/ ./apps/lead-scorer/

RUN pnpm install --frozen-lockfile

RUN pnpm --filter @challenge/lead-scorer build

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — Runtime
# Node.js minimal com app compilada + dados
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-slim AS runtime

WORKDIR /workspace

COPY --from=build /workspace/node_modules       ./node_modules
COPY --from=build /workspace/packages           ./packages
COPY --from=build /workspace/package.json       ./

COPY --from=build /workspace/apps/lead-scorer/.next        ./apps/lead-scorer/.next
COPY --from=build /workspace/apps/lead-scorer/node_modules ./apps/lead-scorer/node_modules
COPY --from=build /workspace/apps/lead-scorer/package.json ./apps/lead-scorer/
COPY --from=build /workspace/apps/lead-scorer/data         ./apps/lead-scorer/data

WORKDIR /workspace/apps/lead-scorer

EXPOSE 3001

ENV NODE_ENV=production
ENV PORT=3001

CMD ["sh", "-c", "./node_modules/.bin/next start -p ${PORT}"]
