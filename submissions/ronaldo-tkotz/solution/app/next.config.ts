import type { NextConfig } from "next";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Pin the workspace root to THIS directory. A stray lockfile higher up the tree
// (~/package-lock.json) makes Next infer the wrong root, which mis-traces files on
// the Railway build. Anchoring to the config's own dir keeps dev + build consistent.
const projectRoot = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  // The warehouse driver is a native Node addon — keep it out of the bundle and
  // let server code `require` it directly. (better-sqlite3 is auto-externalised
  // by Next, but we declare it so the contract is explicit and self-documenting.)
  serverExternalPackages: ["better-sqlite3"],
  // On a Vercel build from GitHub (D48) the repo is cloned whole and Vercel sets the tracing root to
  // the repo root itself; pinning it to this folder there makes it look for .next at the repo root.
  ...(process.env.VERCEL ? {} : { turbopack: { root: projectRoot }, outputFileTracingRoot: projectRoot }),
  // The read-only RavenStack database ships inside every server function (ISC-24, D46.4).
  outputFileTracingIncludes: { "/**": ["./data/ravenstack.db"] },
};

export default nextConfig;
