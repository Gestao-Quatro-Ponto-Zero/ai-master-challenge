import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  transpilePackages: ['@challenge/ui', '@challenge/data-utils'],
  serverExternalPackages: ['@duckdb/node-api'],
}

export default nextConfig
