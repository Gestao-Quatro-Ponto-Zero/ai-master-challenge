import type { NextConfig } from "next";

const config: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // Os dados ficam em data/ e são lidos no servidor: precisam ir junto no pacote publicado.
  outputFileTracingIncludes: { "/**": ["./data/**/*"] },
};

export default config;
