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
        destination: 'http://localhost:5003/documents/:path*',
      },
      {
        source: '/api/categories/:path*',
        destination: 'http://localhost:5002/categories/:path*',
      },
    ]
  },
}

export default nextConfig
