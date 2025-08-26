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
        destination: 'http://localhost:5002/documents/:path*',
      },
      {
        source: '/api/documents/:path*',
        destination: 'http://44.200.148.190/documents/:path*',
      },
    ]
  },
}

export default nextConfig
