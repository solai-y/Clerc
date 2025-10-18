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
    // with page routes. We also now include rules for BOTH the base path
    // (e.g., /api/documents) and nested paths (e.g., /api/documents/123).
    const apiRewrites = [
      // Documents Service
      { source: "/api/documents", destination: `${BACKEND_ORIGIN}/documents` },
      { source: "/api/documents/:path*", destination: `${BACKEND_ORIGIN}/documents/:path*` },
      
      // S3 Service
      { source: "/api/s3", destination: `${BACKEND_ORIGIN}/s3` },
      { source: "/api/s3/:path*", destination: `${BACKEND_ORIGIN}/s3/:path*` },
      
      // Company Service
      { source: "/api/company", destination: `${BACKEND_ORIGIN}/company` },
      { source: "/api/company/:path*", destination: `${BACKEND_ORIGIN}/company/:path*` },
      
      // AI Service
      { source: "/api/ai", destination: `${BACKEND_ORIGIN}/ai` },
      { source: "/api/ai/:path*", destination: `${BACKEND_ORIGIN}/ai/:path*` },
      
      // Prediction Service
      { source: "/api/predict", destination: `${BACKEND_ORIGIN}/predict` },
      { source: "/api/predict/:path*", destination: `${BACKEND_ORIGIN}/predict/:path*` },
      
      // Text Extraction Service
      { source: "/api/text-extract", destination: `${BACKEND_ORIGIN}/text-extract` },
      { source: "/api/text-extract/:path*", destination: `${BACKEND_ORIGIN}/text-extract/:path*` },
    ];
    
    console.log("[Next.js Config] API rewrite rules configured.");
    apiRewrites.forEach(r => console.log(`- ${r.source} -> ${r.destination}`));
    
    return apiRewrites;
  },
};

export default nextConfig;

