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
    const rewrites = [
      // --- Match /documents with or without paths ---
      { source: "/documents", destination: `${BACKEND_ORIGIN}/documents` },
      { source: "/documents/:path*", destination: `${BACKEND_ORIGIN}/documents/:path*` },
      
      // --- Other services ---
      { source: "/s3", destination: `${BACKEND_ORIGIN}/s3` },
      { source: "/s3/:path*", destination: `${BACKEND_ORIGIN}/s3/:path*` },
      { source: "/company", destination: `${BACKEND_ORIGIN}/company` },
      { source: "/company/:path*", destination: `${BACKEND_ORIGIN}/company/:path*` },

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