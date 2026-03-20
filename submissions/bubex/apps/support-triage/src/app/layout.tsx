import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Support Triage',
  description: 'Redesign de suporte — Challenge 002',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  )
}
