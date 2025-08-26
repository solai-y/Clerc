// next.config.mjs
const isLocalDev =
  process.env.VERCEL !== '1' && process.env.NODE_ENV === 'development';

/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/documents/:path*',
        destination: isLocalDev
          ? 'http://localhost:5002/documents/:path*'
          : 'http://44.200.148.190/documents/:path*',
      },
      {
        source: '/api/s3/:path*',
        destination: isLocalDev
          ? 'http://localhost:5003/s3/:path*'
          : 'http://44.200.148.190/s3/:path*',
      },
    ];
  },
};

export default nextConfig;
