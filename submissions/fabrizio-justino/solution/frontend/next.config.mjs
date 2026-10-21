/** @type {import('next').NextConfig} */

// O navegador só fala com o Next (/api/*) e o Next repassa pro FastAPI. Sem auth, um
// rewrite basta — não precisa de uma rota app/api/*/route.ts por endpoint.
const API_URL = (process.env.LEAD_SCORER_API_URL ?? "http://localhost:8000").replace(/\/$/, "")

const nextConfig = {
  poweredByHeader: false,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/:path*` }]
  },
}

export default nextConfig
