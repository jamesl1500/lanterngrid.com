import type { NextConfig } from 'next'

const apiUrl = process.env.API_URL ?? 'http://localhost:8000'

const nextConfig: NextConfig = {
  // Workspace packages ship TypeScript source; Next compiles them.
  transpilePackages: ['@lanterngrid/ui', '@lanterngrid/api-client'],
  typedRoutes: true,
  async rewrites() {
    // The browser talks to FastAPI through /api on the same origin, so session cookies
    // work without CORS.
    return [{ source: '/api/:path*', destination: `${apiUrl}/:path*` }]
  },
}

export default nextConfig
