import type { Metadata } from 'next'
import Link from 'next/link'
import './globals.css'

/** Garante leitura de env em runtime (Railway) em vez de otimizações que fixam valores no build. */
export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'Churn Dashboard',
  description: 'Diagnóstico de churn — Challenge 001',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="bg-gray-50 text-gray-900 min-h-screen">
        <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-8">
          <span className="font-semibold text-gray-800 text-lg">Churn Dashboard</span>
          <nav className="flex gap-6 text-sm">
            <Link href="/overview" className="text-gray-600 hover:text-gray-900 font-medium">
              Visão Geral
            </Link>
            <Link href="/diagnostic" className="text-gray-600 hover:text-gray-900 font-medium">
              Diagnóstico
            </Link>
            <Link href="/segments" className="text-gray-600 hover:text-gray-900 font-medium">
              Contas em Risco
            </Link>
            <Link href="/recommendations" className="text-gray-600 hover:text-gray-900 font-medium">
              Recomendações
            </Link>
          </nav>
        </header>
        <main className="px-6 py-8 max-w-screen-xl mx-auto">
          {children}
        </main>
      </body>
    </html>
  )
}
