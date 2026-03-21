import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  transpilePackages: ['@challenge/ui'],
  serverExternalPackages: [
    '@duckdb/node-api',
    '@duckdb/node-bindings',
    '@duckdb/node-bindings-linux-x64',
  ],
}

export default nextConfig
