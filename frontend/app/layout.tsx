import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'CloudGuard — AI-Powered Cloud Security',
  description: 'OPMonitor-based access control misconfiguration detection',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  )
}