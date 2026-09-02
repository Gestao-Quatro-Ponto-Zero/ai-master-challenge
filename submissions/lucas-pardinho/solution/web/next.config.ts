import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  agentRules: false,
  output: "standalone",
  outputFileTracingRoot: path.join(process.cwd(), ".."),
  poweredByHeader: false,
};

export default nextConfig;
