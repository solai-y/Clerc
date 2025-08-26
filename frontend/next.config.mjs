/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
      source: '/api/documents/:path*',
      has: [{ type: 'header', key: 'host', value: 'localhost:3000' }],
      destination: 'http://localhost:5002/documents/:path*',
      },
      {
        source: '/api/documents/:path*',
        // fallback for everything else (Vercel preview/prod)
        destination: 'http://44.200.148.190/documents/:path*',
      },
    ]
  },
}

export default nextConfig
