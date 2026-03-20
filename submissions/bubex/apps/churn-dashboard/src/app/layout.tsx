import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Churn Dashboard',
  description: 'Diagnóstico de churn — Challenge 001',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  )
}
