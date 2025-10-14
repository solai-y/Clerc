/** @type {import('next').NextConfig} */

// Detect environment
const isVercel = !!process.env.VERCEL;
const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN ||
  (isVercel ? "https://clercbackend.clerc.uk" : "http://localhost");

console.log("Next.js Config: BACKEND_ORIGIN is", BACKEND_ORIGIN);

if (!BACKEND_ORIGIN) {
  throw new Error("BACKEND_ORIGIN must be set for proper API routing");
}

const nextConfig = {
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },
  images: { unoptimized: true },

  async rewrites() {
    // ALL sources are now consistently prefixed with /api to avoid conflicts
    // with page routes like /documents or /company.
    const rewrites = [
      { source: "/api/documents/:path*", destination: `${BACKEND_ORIGIN}/documents/:path*` },
      { source: "/api/documents", destination: `${BACKEND_ORIGIN}/documents` },
      { source: "/api/s3/:path*", destination: `${BACKEND_ORIGIN}/s3/:path*` },
      { source: "/api/s3", destination: `${BACKEND_ORIGIN}/s3` },
      { source: "/api/company/:path*", destination: `${BACKEND_ORIGIN}/company/:path*` },
      { source: "/api/company", destination: `${BACKEND_ORIGIN}/company` },
      { source: "/api/ai/:path*", destination: `${BACKEND_ORIGIN}/ai/:path*` },
      { source: "/api/ai", destination: `${BACKEND_ORIGIN}/ai` },
      { source: "/api/predict/:path*", destination: `${BACKEND_ORIGIN}/predict/:path*` },
      { source: "/api/predict", destination: `${BACKEND_ORIGIN}/predict` },
      { source: "/api/text-extract/:path*", destination: `${BACKEND_ORIGIN}/text-extract/:path*` },
      { source: "/api/text-extract", destination: `${BACKEND_ORIGIN}/text-extract` },
    ];
    
    console.log("Next.js Rewrites have been configured.");
    return rewrites;
  },
};

export default nextConfig;
