// next.config.mjs

const isLocalDev = (process.env.VERCEL !== '1') && process.env.NODE_ENV === 'development';

const nextConfig = {
  async rewrites() {
    return [
      {
        // Frontend calls /api/documents → rewritten server-side
        source: '/api/documents/:path*',
        destination: isLocalDev
          ? 'http://localhost:5002/documents/:path*'
          : 'http://44.200.148.190/documents/:path*',
      },
      {
        // Frontend calls /api/documents → rewritten server-side
        source: '/api/s3/:path*',
        destination: isLocalDev
          ? 'http://localhost:5002/s3/:path*'
          : 'http://44.200.148.190/s3/:path*',
      },
    ];
  },
};

export default nextConfig;
