'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const LINKS = [
  { href: '/', label: 'Fila' },
  { href: '/testar/', label: 'Testar ticket' },
  { href: '/diagnostico/', label: 'Diagnóstico' },
  { href: '/estresse/', label: 'Estresse' },
  { href: '/como-funciona/', label: 'Como funciona' },
]

export function SiteHeader() {
  const path = usePathname() ?? '/'
  const isActive = (href: string) => (href === '/' ? path === '/' : path.startsWith(href.replace(/\/$/, '')))
  return (
    <header className="site-header">
      <div className="wrap">
        <Link href="/" className="brand">
          <span>Case AI Master · G4</span>
          <strong>Mesa de Suporte</strong>
        </Link>
        <nav className="nav" aria-label="Principal">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} aria-current={isActive(l.href) ? 'page' : undefined}>
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  )
}
