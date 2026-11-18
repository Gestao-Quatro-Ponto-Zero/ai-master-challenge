# RavenStack churn app — production image for Railway.
#
# Install + build with Bun (respects bun.lock), but SERVE under Node: better-sqlite3 is a
# native addon that does not load under the Bun runtime (it does compile a Node-ABI binary
# at install time, which `next start` under Node then loads fine). The RavenStack database
# is read from WAREHOUSE_PATH; how it ships with the deploy is ISA ISC-24.
FROM node:22-slim AS base
WORKDIR /app

# better-sqlite3 build toolchain (prebuilt binary is used when available; this is the fallback)
# + bun for a lockfile-deterministic install.
#
# Hardened 2026-07-04 after a build-day failure: an UNPINNED `bun.sh/install`
# pulled a fresh bun whose install-script env broke prebuilt-binary detection
# (libc came up blank), and the gyp fallback ran via `bunx node-gyp@latest`,
# which no longer supports Node 20. Three independent fixes:
#   1. node:22 base — current better-sqlite3 prebuilds + node-gyp@latest both support it,
#   2. bun PINNED — the deps layer builds the same way every time,
#   3. node-gyp preinstalled on PATH — bun uses it instead of bunx@latest if the
#      source fallback ever fires again.
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 make g++ ca-certificates curl unzip \
 && rm -rf /var/lib/apt/lists/* \
 && npm install -g node-gyp@11 \
 && curl -fsSL https://bun.sh/install | bash -s "bun-v1.2.19" \
 && ln -s /root/.bun/bin/bun /usr/local/bin/bun

# Dependencies first (better layer caching).
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

# App + build.
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN bun run build

ENV NODE_ENV=production
ENV PORT=3000
EXPOSE 3000

# Serve under Node (not Bun) so the native warehouse driver loads. The `next` bin's shebang
# is `#!/usr/bin/env node`, so this runs on Node.
CMD ["node_modules/.bin/next", "start"]
