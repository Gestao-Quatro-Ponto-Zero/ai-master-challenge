import { NavHeader } from '../components/nav-header'
import { MetricasClient } from './metricas-client'
import { BarChart3 } from 'lucide-react'

export default function MetricasPage() {
  return (
    <div className="min-h-screen">
      <NavHeader />
      <main className="mx-auto max-w-[1200px] px-4 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <BarChart3 className="h-8 w-8 text-primary" />
            <div>
              <h1 className="font-display text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                Performance do Modelo
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Métricas reais de avaliação do classificador no conjunto de teste
              </p>
            </div>
          </div>
        </div>
        <MetricasClient />
      </main>
    </div>
  )
}
