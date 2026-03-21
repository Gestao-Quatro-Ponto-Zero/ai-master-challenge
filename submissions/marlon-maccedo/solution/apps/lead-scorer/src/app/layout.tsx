import type { Metadata } from 'next'
import Link from 'next/link'
import './globals.css'

export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'Lead Scorer',
  description: 'Priorização de pipeline de vendas — Challenge 003',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="bg-gray-50 text-gray-900 min-h-screen">
        <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-8">
          <span className="font-semibold text-gray-800 text-lg">Lead Scorer</span>
          <nav className="flex gap-6 text-sm">
            <Link href="/" className="text-gray-600 hover:text-gray-900 font-medium">
              Dashboard
            </Link>
            <Link href="/pipeline" className="text-gray-600 hover:text-gray-900 font-medium">
              Pipeline
            </Link>
            <Link href="/team" className="text-gray-600 hover:text-gray-900 font-medium">
              Minha Carteira
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
