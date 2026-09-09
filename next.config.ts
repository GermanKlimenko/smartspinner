import type { NextConfig } from 'next';

const githubPagesBase = process.env.GITHUB_ACTIONS === 'true' ? '/smartspinner' : '';

const nextConfig: NextConfig = {
  output: 'export',
  images: { unoptimized: true },
  assetPrefix: githubPagesBase,
};

export default nextConfig;
