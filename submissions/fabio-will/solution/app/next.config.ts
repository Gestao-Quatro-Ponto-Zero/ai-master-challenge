import type { NextConfig } from 'next'

// Static export: no server, no API keys, nothing leaves the browser.
const nextConfig: NextConfig = {
  output: 'export',
  reactStrictMode: true,
  poweredByHeader: false,
  images: { unoptimized: true },
  trailingSlash: true,
  // Inline the (small) CSS into each page so it does not block the first render.
  experimental: { inlineCss: true },
}

export default nextConfig
