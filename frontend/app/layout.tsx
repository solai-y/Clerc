import type { Metadata } from "next"
import Link from "next/link"
import { GeistSans } from "geist/font/sans"
import { GeistMono } from "geist/font/mono"
import { Toaster } from "@/components/ui/toaster"
import { AuthProvider } from "@/contexts/auth-context"
import "./globals.css"

export const metadata: Metadata = {
  title: "v0 App",
  description: "Created with v0",
  generator: "v0.dev",
}

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className={GeistSans.className}>
        <AuthProvider>
          {/* Top navigation */}
          <header className="border-b bg-background/60 backdrop-blur">
            <div className="container mx-auto max-w-6xl px-4">
              <div className="flex h-14 items-center justify-between">
                <Link href="/" className="font-semibold tracking-tight">
                  Clerc
                </Link>
                <nav className="flex items-center gap-5 text-sm">
                  <Link href="/" className="hover:underline">
                    Documents
                  </Link>
                  <Link href="/tags" className="hover:underline">
                    Tags
                  </Link>
                </nav>
              </div>
            </div>
          </header>

          {/* Page content */}
          <main className="min-h-[calc(100vh-3.5rem)]">{children}</main>

          <Toaster />
        </AuthProvider>
      </body>
    </html>
  )
}
