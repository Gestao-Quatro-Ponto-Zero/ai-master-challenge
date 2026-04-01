import { useState, useEffect, useRef, useCallback } from 'react'
import { cn } from '@/lib/utils'

import LeftCard from '../components/LeftCard'
import ProjectCard, { type ProjectCardRef } from '../components/ProjectCard'
import SellerCard from '../components/SellerCard'
import RegionalProductsAnalysis from '../components/RegionalProductsAnalysis'
import SellerAnalysisDrilldown from '../components/SellerAnalysisDrilldown'
import TransferAnalysisCards from '../components/TransferAnalysisCards'
import TransferFeed from '../components/TransferFeed'
import GlobalAlertsPanel from '../components/GlobalAlertsPanel'
import MacroAnalysisDashboard from '../components/MacroAnalysisDashboard'
import { useManagers } from '../hooks/useManagers'
import { useSellers } from '../hooks/useSellers'

export default function Home() {
  const { data: managers = [] } = useManagers()
  const { data: sellers = [] } = useSellers()
  const [selectedManager, setSelectedManager] = useState<string>('')
  const dashboardCardRef = useRef<ProjectCardRef>(null)
  const [dashboardSlideIndex, setDashboardSlideIndex] = useState(0)
  const [transfersScopeUi, setTransfersScopeUi] = useState<'squad' | 'geral'>('geral')
  const [macroScopeUi, setMacroScopeUi] = useState<'squad' | 'geral'>('geral')

  const goToDashboardSection = useCallback((index: number) => {
    document.getElementById('card-dashboard')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    window.setTimeout(() => {
      dashboardCardRef.current?.scrollToPage(index)
    }, 220)
  }, [])

  useEffect(() => {
    document.title = 'Manager view'
  }, [])

  useEffect(() => {
    if (managers.length > 0 && !selectedManager) {
      setSelectedManager(managers[0].manager)
    }
  }, [managers, selectedManager])

  useEffect(() => {
    if (!selectedManager && macroScopeUi === 'squad') setMacroScopeUi('geral')
  }, [selectedManager, macroScopeUi])

  const squadSellers = sellers.filter((s) => s.manager === selectedManager)

  return (
    <main className="bg-gray-100 text-neutral-900 h-screen overflow-y-auto scroll-smooth snap-y snap-mandatory scroll-pt-4">
      <section className="px-4 pt-4 pb-16 lg:pb-4">
        <div className="grid h-full grid-cols-1 gap-4 lg:grid-cols-[420px_1fr]">

          {/* LEFT: sticky hero card */}
          <aside className="lg:sticky lg:top-4 lg:h-[calc(100svh-2rem)]">
            <LeftCard
              selectedManager={selectedManager}
              managers={managers}
              onManagerChange={setSelectedManager}
              dashboardSlideIndex={dashboardSlideIndex}
              onDashboardSectionClick={goToDashboardSection}
            />
          </aside>

          {/* RIGHT: project cards stacked vertically */}
          <div className="min-w-0 space-y-4">
            <ProjectCard
              ref={dashboardCardRef}
              id="card-dashboard"
              label="Dashboard"
              gradientFrom="#0f172a"
              gradientTo="#bb935b"
              scrollHint
              onDashboardSlideChange={setDashboardSlideIndex}
              showFullscreenToggle
              pages={[
                {
                  index: '01',
                  title: 'Macro Analysis',
                  content: (
                    <div className="h-full min-h-0 w-full overflow-y-auto p-8">
                      <MacroAnalysisDashboard
                        managerName={selectedManager}
                        scope={macroScopeUi}
                        onScopeChange={setMacroScopeUi}
                      />
                    </div>
                  ),
                },
                {
                  index: '02',
                  title: 'Products & Regional Analysis',
                  content: (
                    <div className="flex min-h-0 w-full flex-1 flex-col overflow-hidden">
                      <RegionalProductsAnalysis managerName={selectedManager} />
                    </div>
                  ),
                },
                {
                  index: '03',
                  title: 'Transfer Analysis',
                  content: <TransferAnalysisCards managerName={selectedManager} />,
                },
              ]}
            />

            <ProjectCard id="card-transfers" label="Transfers" gradientFrom="#0f172a" gradientTo="#7c3aed" singlePage scrollHint>
              <div className="flex flex-col gap-6 p-8 h-full min-h-0">
                <p className="text-sm text-neutral-500">
                  Deals do seu Squad recomendados para transferência
                </p>
                <div
                  className="inline-flex w-fit shrink-0 rounded-xl border border-neutral-200 bg-neutral-50/80 p-1 gap-0.5 shadow-sm"
                  role="group"
                  aria-label="Escopo de transferências"
                >
                  <button
                    type="button"
                    disabled={!selectedManager}
                    title={!selectedManager ? 'Selecione um manager no painel à esquerda' : undefined}
                    onClick={() => setTransfersScopeUi('squad')}
                    className={cn(
                      'min-w-[88px] rounded-lg px-4 py-2 text-sm font-medium transition-colors',
                      transfersScopeUi === 'squad'
                        ? 'bg-white text-neutral-900 shadow-sm'
                        : 'text-neutral-500 hover:text-neutral-800',
                      !selectedManager && 'cursor-not-allowed opacity-45 hover:text-neutral-500',
                    )}
                  >
                    Squad
                  </button>
                  <button
                    type="button"
                    onClick={() => setTransfersScopeUi('geral')}
                    className={cn(
                      'min-w-[88px] rounded-lg px-4 py-2 text-sm font-medium transition-colors',
                      transfersScopeUi === 'geral'
                        ? 'bg-white text-neutral-900 shadow-sm'
                        : 'text-neutral-500 hover:text-neutral-800',
                    )}
                  >
                    Geral
                  </button>
                </div>

                <TransferFeed managerName={selectedManager} scope={transfersScopeUi} />
              </div>
            </ProjectCard>

            <ProjectCard id="card-seller-analysis" label="Seller Analysis" gradientFrom="#0f172a" gradientTo="#0d9488" singlePage>
              <SellerAnalysisDrilldown managerName={selectedManager} />
            </ProjectCard>

            <ProjectCard id="card-alertas" label="Alertas" gradientFrom="#0f172a" gradientTo="#b45309" singlePage>
              <div className="flex h-full min-h-0 flex-col gap-6 p-8">
                <div className="shrink-0">
                  <h2 className="text-lg font-semibold text-neutral-900 tracking-tight">Alertas</h2>
                  <p className="text-sm text-neutral-500 mt-0.5">
                    Avisos e recomendações automáticas do pipeline
                  </p>
                </div>
                <div className="flex min-h-0 flex-1 flex-col">
                  <GlobalAlertsPanel managerName={selectedManager} />
                </div>
              </div>
            </ProjectCard>

            <ProjectCard id="card-squad" label="Squad" description="Clique nos cards para acessar a view do Vendedor" gradientFrom="#0f172a" gradientTo="#0369a1" singlePage>
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6 p-8">
                {squadSellers.map((seller) => (
                  <SellerCard
                    key={seller.sales_agent}
                    name={seller.sales_agent}
                    title="Seller"
                    region={seller.regional_office}
                    prospect={seller.prospecting}
                    engaging={seller.active_deals}
                    won={seller.won_deals}
                    lost={seller.closed_deals - seller.won_deals}
                    onClick={() => window.open(`/sellers/${encodeURIComponent(seller.sales_agent)}`, '_blank')}
                  />
                ))}
              </div>
            </ProjectCard>

          </div>

        </div>
      </section>
    </main>
  )
}
