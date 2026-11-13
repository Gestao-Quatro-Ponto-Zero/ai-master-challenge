import { NavHeader } from './components/nav-header'
import { TriagePageClient } from './components/triage-page-client'
import { Shield } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <NavHeader />
      <main className="mx-auto max-w-[1200px] px-4 py-8">
        {/* Hero */}
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <Shield className="h-8 w-8 text-primary" />
            <div>
              <h1 className="font-display text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                Triagem Inteligente de Suporte
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Classificação automatizada de chamados com Machine Learning — protótipo demonstrável
              </p>
            </div>
          </div>
          <div className="mt-3 inline-flex items-center gap-1.5 rounded-md border border-amber-200 bg-amber-50 px-3 py-1.5 dark:border-amber-800/50 dark:bg-amber-950/20">
            <span className="text-xs font-semibold uppercase tracking-wider text-amber-700 dark:text-amber-400">
              ⚠ Protótipo — Não usar em produção
            </span>
          </div>
        </div>

        {/* Content */}
        <TriagePageClient />
      </main>
    </div>
  )
}
