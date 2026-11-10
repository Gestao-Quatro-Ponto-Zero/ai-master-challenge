import { defineConfig } from "vitest/config";
import { fileURLToPath } from "node:url";

const caminho = (p: string) => fileURLToPath(new URL(p, import.meta.url));

export default defineConfig({
  resolve: { alias: { "@": caminho("./src"), "server-only": caminho("./tests/vazio.ts") } },
  test: { include: ["tests/**/*.test.ts"], environment: "node" },
});
