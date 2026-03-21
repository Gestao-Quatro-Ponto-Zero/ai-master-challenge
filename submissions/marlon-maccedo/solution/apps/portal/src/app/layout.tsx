import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI Master Challenge — Portfólio',
  description: '4 desafios de negócio resolvidos com uso estratégico de IA — G4 Educação',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="bg-gray-50 text-gray-900 min-h-screen">{children}</body>
    </html>
  )
}
