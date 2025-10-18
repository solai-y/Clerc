/** @type {import('next').NextConfig} */

// Detect environment
const isVercel = !!process.env.VERCEL;
const isProd = process.env.VERCEL_ENV === "production";
const isEC2 = !!process.env.EC2_DEPLOYMENT;

// Backend origin for rewrites - prioritize explicit env var, then fallback
const BACKEND_ORIGIN =
  process.env.BACKEND_ORIGIN ||
  (process.env.VERCEL ? "https://clercbackend.clerc.uk" : "http://localhost");

// Optional: tag service can be a different origin/port
const TAG_SERVICE_ORIGIN = process.env.TAG_SERVICE_ORIGIN || BACKEND_ORIGIN;

// Debug logging
console.log("Next.js Config Debug:");
console.log("- VERCEL:", process.env.VERCEL);
console.log("- VERCEL_ENV:", process.env.VERCEL_ENV);
console.log("- EC2_DEPLOYMENT:", process.env.EC2_DEPLOYMENT);
console.log("- BACKEND_ORIGIN env:", process.env.BACKEND_ORIGIN);
console.log("- TAG_SERVICE_ORIGIN env:", process.env.TAG_SERVICE_ORIGIN);
console.log("- Computed BACKEND_ORIGIN:", BACKEND_ORIGIN);
console.log("- Computed TAG_SERVICE_ORIGIN:", TAG_SERVICE_ORIGIN);
console.log("- Environment detected:", { isVercel, isProd, isEC2 });

if (!BACKEND_ORIGIN) {
  throw new Error("BACKEND_ORIGIN must be set for proper API routing");
}

const nextConfig = {
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },
  images: { unoptimized: true },

  ...(isEC2 && process.env.STATIC_EXPORT === "true" && { output: "export" }),

  async rewrites() {
    const rewrites = [
      // --- Documents ---
      { source: "/documents", destination: `${BACKEND_ORIGIN}/documents` },
      { source: "/documents/:path*", destination: `${BACKEND_ORIGIN}/documents/:path*` },

      // --- Tag service (use a prefix so it doesn't collide with /tags page) ---
      { source: "/tag-service/tags", destination: `${TAG_SERVICE_ORIGIN}/tags` },
      { source: "/tag-service/tags/:path*", destination: `${TAG_SERVICE_ORIGIN}/tags/:path*` },

      // --- Other services ---
      { source: "/s3", destination: `${BACKEND_ORIGIN}/s3` },
      { source: "/s3/:path*", destination: `${BACKEND_ORIGIN}/s3/:path*` },
      { source: "/company", destination: `${BACKEND_ORIGIN}/company` },
      { source: "/company/:path*", destination: `${BACKEND_ORIGIN}/company/:path*` },
      { source: "/ai", destination: `${BACKEND_ORIGIN}/ai` },
      { source: "/ai/:path*", destination: `${BACKEND_ORIGIN}/ai/:path*` },
      { source: "/predict", destination: `${BACKEND_ORIGIN}/predict` },
      { source: "/predict/:path*", destination: `${BACKEND_ORIGIN}/predict/:path*` },
      { source: "/text-extract", destination: `${BACKEND_ORIGIN}/text-extract` },
      { source: "/text-extract/:path*", destination: `${BACKEND_ORIGIN}/text-extract/:path*` },

      // --- Backward-compat ---
      { source: "/api/documents/:path*", destination: `${BACKEND_ORIGIN}/documents/:path*` },
    ];

    console.log("Next.js Rewrites:");
    rewrites.forEach((r) => console.log(`- ${r.source} -> ${r.destination}`));
    return rewrites;
  },
};

export default nextConfig;
