import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Docker needs standalone output, but Vercel uses its own build adapter.
  output: process.env.VERCEL ? undefined : "standalone",
};

export default nextConfig;
