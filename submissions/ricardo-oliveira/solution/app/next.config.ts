import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Modelo clássico de renderização: as páginas leem a sessão e a planilha a cada pedido.
  cacheComponents: false,
  async redirects() {
    // A tela de login saiu; quem tiver o link antigo cai na escolha do vendedor.
    return [{ source: "/login", destination: "/", permanent: false }];
  },
  turbopack: {
    root: process.cwd(),
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
