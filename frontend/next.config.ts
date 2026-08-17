import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a minimal, self-contained server bundle in .next/standalone,
  // which the Dockerfile copies instead of shipping the whole node_modules tree.
  output: "standalone",
};

export default nextConfig;
