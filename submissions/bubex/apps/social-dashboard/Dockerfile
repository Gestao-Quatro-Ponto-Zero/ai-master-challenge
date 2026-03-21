# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — Build
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-slim AS build

RUN npm install -g pnpm@10.32.1

WORKDIR /workspace

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY packages/ ./packages/
COPY apps/social-dashboard/ ./apps/social-dashboard/

RUN pnpm install --frozen-lockfile

RUN pnpm --filter @challenge/social-dashboard build

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — Runtime
# Node.js minimal com app compilada + dados
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-slim AS runtime

WORKDIR /workspace

COPY --from=build /workspace/node_modules          ./node_modules
COPY --from=build /workspace/packages              ./packages
COPY --from=build /workspace/package.json          ./

COPY --from=build /workspace/apps/social-dashboard/.next        ./apps/social-dashboard/.next
COPY --from=build /workspace/apps/social-dashboard/node_modules ./apps/social-dashboard/node_modules
COPY --from=build /workspace/apps/social-dashboard/package.json ./apps/social-dashboard/
COPY --from=build /workspace/apps/social-dashboard/data         ./apps/social-dashboard/data

WORKDIR /workspace/apps/social-dashboard

EXPOSE 3004

ENV NODE_ENV=production
ENV PORT=3004

CMD ["sh", "-c", "./node_modules/.bin/next start -p ${PORT}"]
