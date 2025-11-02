import type { Metadata } from 'next'
import { GeistSans } from 'geist/font/sans'
import { GeistMono } from 'geist/font/mono'
import Toaster from '@/components/ui/toaster'   // ✅ default import now always works
import { AuthProvider } from '@/contexts/auth-context'
import './globals.css'

export const metadata: Metadata = {
  title: 'Clerc',
  description: 'Clerc app for document management system.',
  generator: 'Clerc',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className={GeistSans.className}>
        <AuthProvider>
          {children}
          {/* mount toaster last so it overlays everything */}
          <Toaster />
        </AuthProvider>
      </body>
    </html>
  )
}
