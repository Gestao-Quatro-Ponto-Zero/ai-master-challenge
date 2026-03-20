import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Social Dashboard',
  description: 'Estratégia de social media — Challenge 004',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  )
}
