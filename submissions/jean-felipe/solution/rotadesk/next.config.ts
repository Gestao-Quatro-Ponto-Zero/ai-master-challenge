import type { NextConfig } from "next";
import path from "path";
import { fileURLToPath } from "url";

const rootDir = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  // Na Vercel o Root Directory já isola o app — outputFileTracingRoot aqui quebrava o deploy (404).
  // turbopack.root só no dev local (monorepo com lockfiles na raiz).
  ...(process.env.VERCEL
    ? {}
    : {
        turbopack: {
          root: rootDir,
        },
      }),
};

export default nextConfig;
