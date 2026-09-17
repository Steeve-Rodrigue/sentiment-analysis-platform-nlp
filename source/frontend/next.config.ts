import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // "standalone" is only for the Docker image (see Dockerfile, which
  // copies .next/standalone). On Vercel (process.env.VERCEL is set
  // automatically on every build there) it must stay off -- it makes
  // Next.js skip writing .next/next-server.js.nft.json, which Vercel's
  // own build pipeline needs and fails without (ENOENT during
  // "Running onBuildComplete from Vercel").
  ...(process.env.VERCEL ? {} : { output: "standalone" as const }),
};

export default nextConfig;
