/** @type {import('next').NextConfig} */

// Detect environment
const isVercel = !!process.env.VERCEL; // true on Vercel (preview/prod)
const isProd = process.env.VERCEL_ENV === "production";

// Backend origin for rewrites
const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN || (process.env.VERCEL ? "https://clercbackend.clerc.uk" : "http://localhost");

// Debug logging (will show in Vercel build logs)
console.log("Next.js Config Debug:");
console.log("- VERCEL:", process.env.VERCEL);
console.log("- VERCEL_ENV:", process.env.VERCEL_ENV);
console.log("- BACKEND_ORIGIN env:", process.env.BACKEND_ORIGIN);
console.log("- Computed BACKEND_ORIGIN:", BACKEND_ORIGIN);


const nextConfig = {
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },
  images: { unoptimized: true },

  async rewrites() {
    return [
      // --- No /api prefix (recommended; matches your current fetch('/documents?...')) ---
      { source: "/documents/:path*", destination: `${BACKEND_ORIGIN}/documents/:path*` },
      { source: "/s3/:path*",        destination: `${BACKEND_ORIGIN}/s3/:path*` },
      { source: "/company/:path*",   destination: `${BACKEND_ORIGIN}/company/:path*` },

      // --- Backward-compat (you already had /api/documents) ---
      { source: "/api/documents/:path*", destination: `${BACKEND_ORIGIN}/documents/:path*` },
    ];
  },
};

export default nextConfig;