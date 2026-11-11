import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  cacheComponents: true,
  /** Rotas antigas (toggles na URL e /console) apontam para as rotas novas (ADR-0015). */
  async redirects() {
    const q = (key: string, value: string) => [{ type: "query" as const, key, value }]
    return [
      { source: "/", has: q("visao", "roi"), destination: "/painel/roi", permanent: false },
      { source: "/", has: q("visao", "operacao"), destination: "/painel/operacao", permanent: false },
      { source: "/", destination: "/painel/diagnostico", permanent: false },
      { source: "/painel", destination: "/painel/diagnostico", permanent: false },
      { source: "/como-foi-feito", has: q("secao", "decisoes"), destination: "/como-foi-feito/decisoes", permanent: false },
      { source: "/como-foi-feito", has: q("secao", "conducao"), destination: "/como-foi-feito/conducao", permanent: false },
      { source: "/como-foi-feito", destination: "/como-foi-feito/proposta", permanent: false },
      { source: "/console", has: q("aba", "fila"), destination: "/tickets?filtro=revisao", permanent: false },
      { source: "/console", destination: "/tickets", permanent: false },
    ]
  },
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
