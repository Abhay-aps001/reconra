import type { NextConfig } from 'next';

export function resolveBackendBaseUrl(
  configuredUrl = process.env.NEXT_PUBLIC_API_BASE_URL,
  environment = process.env.NODE_ENV,
) {
  if (configuredUrl) return configuredUrl.replace(/\/$/, '');
  return environment === 'development' ? 'http://127.0.0.1:8000' : undefined;
}

const nextConfig: NextConfig = {
  async rewrites() {
    const backend = resolveBackendBaseUrl();
    return backend
      ? [{ source: '/api/:path*', destination: `${backend}/api/:path*` }]
      : [];
  },
};
export default nextConfig;
