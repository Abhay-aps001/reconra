import type { NextConfig } from 'next';
const backend = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/,'');
const nextConfig: NextConfig = {
 async rewrites() { return backend ? [{source:'/api/:path*',destination:`${backend}/api/:path*`}] : []; },
};
export default nextConfig;
