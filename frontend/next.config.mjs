/** @type {import('next').NextConfig} */

// Detect environment
const isVercel = !!process.env.VERCEL; // true on Vercel (preview/prod)
const isProd = process.env.VERCEL_ENV === "production";


  // rewrites mapping /documents, /s3, /company -> BACKEND_ORIGIN (you already have this pattern)
const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN || (process.env.VERCEL ? "https://clercbackend.clerc.uk" : "http://localhost");


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