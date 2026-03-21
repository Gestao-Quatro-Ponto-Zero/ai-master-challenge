# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — Build
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-slim AS build

RUN npm install -g pnpm@10.32.1

WORKDIR /workspace

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY packages/ ./packages/
COPY apps/churn-dashboard/ ./apps/churn-dashboard/

RUN pnpm install --frozen-lockfile

RUN pnpm --filter @challenge/churn-dashboard build

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — Runtime
# Node.js minimal com app compilada + dados
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-slim AS runtime

WORKDIR /workspace

COPY --from=build /workspace/node_modules        ./node_modules
COPY --from=build /workspace/packages            ./packages
COPY --from=build /workspace/package.json        ./

COPY --from=build /workspace/apps/churn-dashboard/.next        ./apps/churn-dashboard/.next
COPY --from=build /workspace/apps/churn-dashboard/node_modules ./apps/churn-dashboard/node_modules
COPY --from=build /workspace/apps/churn-dashboard/package.json ./apps/churn-dashboard/
COPY --from=build /workspace/apps/churn-dashboard/data         ./apps/churn-dashboard/data

WORKDIR /workspace/apps/churn-dashboard

EXPOSE 3002

ENV NODE_ENV=production
ENV PORT=3002

CMD ["sh", "-c", "./node_modules/.bin/next start -p ${PORT}"]
