/** @type {import('next').NextConfig} */

// Detect environment
const isVercel = !!process.env.VERCEL;
const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN ||
  (isVercel ? "https://clercbackend.clerc.uk" : "http://localhost");

// This log is crucial for debugging Vercel builds.
console.log(`[Next.js Config] Build environment detected. Vercel: ${isVercel}. Backend Origin: ${BACKEND_ORIGIN}`);

if (!BACKEND_ORIGIN) {
  throw new Error("FATAL: BACKEND_ORIGIN environment variable is not set.");
}

const nextConfig = {
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },
  images: { unoptimized: true },
  async rewrites() {
    // ALL sources are now consistently prefixed with /api to avoid conflicts
    // with page routes like /documents or /company.
    const apiRewrites = [
      { source: "/api/documents/:path*", destination: `${BACKEND_ORIGIN}/documents/:path*` },
      { source: "/api/s3/:path*", destination: `${BACKEND_ORIGIN}/s3/:path*` },
      { source: "/api/company/:path*", destination: `${BACKEND_ORIGIN}/company/:path*` },
      { source: "/api/ai/:path*", destination: `${BACKEND_ORIGIN}/ai/:path*` },
      { source: "/api/predict/:path*", destination: `${BACKEND_ORIGIN}/predict/:path*` },
      { source: "/api/text-extract/:path*", destination: `${BACKEND_ORIGIN}/text-extract/:path*` },
    ];
    
    console.log("[Next.js Config] API rewrite rules configured.");
    apiRewrites.forEach(r => console.log(`- ${r.source} -> ${r.destination}`));
    
    return apiRewrites;
  },
};

export default nextConfig;