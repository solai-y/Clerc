/** @type {import('next').NextConfig} */

// Detect environment
const isVercel = !!process.env.VERCEL; // true on Vercel (preview/prod)
const isProd = process.env.VERCEL_ENV === "production";
const isEC2 = !!process.env.EC2_DEPLOYMENT; // Set this env var for EC2 deployments

// Backend origin for rewrites - prioritize explicit env var, then fallback to platform detection
const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN ||
  (process.env.VERCEL ? "https://clercbackend.clerc.uk" : "http://localhost");

// Prediction service origin - defaults to direct connection if nginx not available
const PREDICTION_ORIGIN = process.env.PREDICTION_SERVICE_URL || `${BACKEND_ORIGIN}:5006`;

// Debug logging (will show in build logs)
console.log("Next.js Config Debug:");
console.log("- VERCEL:", process.env.VERCEL);
console.log("- VERCEL_ENV:", process.env.VERCEL_ENV);
console.log("- EC2_DEPLOYMENT:", process.env.EC2_DEPLOYMENT);
console.log("- BACKEND_ORIGIN env:", process.env.BACKEND_ORIGIN);
console.log("- Computed BACKEND_ORIGIN:", BACKEND_ORIGIN);
console.log("- PREDICTION_ORIGIN:", PREDICTION_ORIGIN);
console.log("- Environment detected:", { isVercel, isProd, isEC2 });


// Validate configuration
if (!BACKEND_ORIGIN) {
  throw new Error("BACKEND_ORIGIN must be set for proper API routing");
}

const nextConfig = {
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },
  images: { unoptimized: true },

  // Add output for static export if needed for EC2
  ...(isEC2 && process.env.STATIC_EXPORT === 'true' && { output: 'export' }),

  async rewrites() {
    const rewrites = [
      // --- Match /documents with or without paths ---
      { source: "/documents", destination: `${BACKEND_ORIGIN}/documents` },
      { source: "/documents/:path*", destination: `${BACKEND_ORIGIN}/documents/:path*` },
      
      // --- Other services ---
      { source: "/s3", destination: `${BACKEND_ORIGIN}/s3` },
      { source: "/s3/:path*", destination: `${BACKEND_ORIGIN}/s3/:path*` },
      { source: "/company", destination: `${BACKEND_ORIGIN}/company` },
      { source: "/company/:path*", destination: `${BACKEND_ORIGIN}/company/:path*` },
      { source: "/ai", destination: `${BACKEND_ORIGIN}/ai` },
      { source: "/ai/:path*", destination: `${BACKEND_ORIGIN}/ai/:path*` },
      { source: "/predict", destination: `${PREDICTION_ORIGIN}` },
      { source: "/predict/:path*", destination: `${PREDICTION_ORIGIN}/:path*` },
      { source: "/text-extract", destination: `${BACKEND_ORIGIN}/text-extract` },
      { source: "/text-extract/:path*", destination: `${BACKEND_ORIGIN}/text-extract/:path*` },

      // --- Backward-compat ---
      { source: "/api/documents/:path*", destination: `${BACKEND_ORIGIN}/documents/:path*` },
    ];
    
    console.log("Next.js Rewrites:");
    rewrites.forEach(rewrite => {
      console.log(`- ${rewrite.source} -> ${rewrite.destination}`);
    });
    
    return rewrites;
  },
};

export default nextConfig;