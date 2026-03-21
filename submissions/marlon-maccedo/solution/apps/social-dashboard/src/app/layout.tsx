import type { Metadata } from 'next'
import Link from 'next/link'
import './globals.css'

export const metadata: Metadata = {
  title: 'Social Dashboard',
  description: 'Estratégia de social media — Challenge 004',
}

const NAV = [
  { href: '/overview',     label: 'Visão Geral' },
  { href: '/performance',  label: 'Performance' },
  { href: '/sponsorship',  label: 'Patrocínios' },
  { href: '/audience',     label: 'Audiência' },
  { href: '/strategy',     label: 'Estratégia' },
]

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="bg-gray-50 min-h-screen">
        <nav className="bg-white border-b border-gray-200 sticky top-0 z-10">
          <div className="max-w-screen-xl mx-auto px-6 flex items-center gap-6 h-14">
            <span className="font-bold text-gray-900 text-sm shrink-0">Social Dashboard</span>
            <div className="flex items-center gap-1">
              {NAV.map(({ href, label }) => (
                <Link
                  key={href}
                  href={href}
                  className="px-3 py-1.5 rounded-lg text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
                >
                  {label}
                </Link>
              ))}
            </div>
          </div>
        </nav>
        <main className="px-6 py-8 max-w-screen-xl mx-auto">
          {children}
        </main>
      </body>
    </html>
  )
}
