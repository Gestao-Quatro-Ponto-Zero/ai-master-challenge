import './App.css'
import { useState } from 'react'
import { DataProvider, useDataContext } from '@/context/DataContext'
import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import { MainContent } from '@/components/layout/MainContent'
import { UploadArea } from '@/components/upload/UploadArea'
import { Button } from '@/components/ui'
import { DashboardPageNew } from '@/components/pages/DashboardPageNew'
import { DealsPage } from '@/components/pages/DealsPage'
import { DealDetailPage } from '@/components/pages/DealDetailPage'
import { AccountsPage } from '@/components/pages/AccountsPage'
import { TeamPage } from '@/components/pages/TeamPage'
import type { DealScore, FilterOptions } from '@/types'

function AppContent() {
  const { state } = useDataContext()
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [selectedDeal, setSelectedDeal] = useState<DealScore | null>(null)
  const [filters, setFilters] = useState<FilterOptions>({})

  const { accounts, products, salesTeams, pipeline, isLoaded } = state

  // Show upload if not loaded
  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-hubspot-gray-100 text-hubspot-black font-sans flex flex-col items-center justify-center p-6">
        <header className="mb-12 text-center">
          <div className="flex items-center justify-center gap-4 mb-4">
            <div className="w-14 h-14 bg-hubspot-orange rounded-xl flex items-center justify-center text-white text-3xl font-black shadow-lg">H</div>
            <h1 className="text-5xl font-black text-hubspot-black tracking-tighter uppercase">Lead Scorer</h1>
          </div>
          <p className="text-hubspot-black/60 font-black uppercase tracking-[0.3em] text-xs mt-2">Intelligence Interface v2.1</p>
        </header>
        <main className="w-full max-w-5xl">
          <UploadArea />
        </main>
      </div>
    )
  }

  // Render app with navigation
  return (
    <div className="min-h-screen app-container text-hubspot-black flex font-sans">
      {/* Sidebar */}
      <Sidebar currentPage={currentPage} onPageChange={(page) => {
        setCurrentPage(page)
        setSelectedDeal(null)
      }} />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header with filters */}
        <div className="sticky top-0 z-10 bg-white border-b border-hubspot-gray-200 shadow-sm">
          <Header
            salesTeams={salesTeams}
            products={products}
            filters={filters}
            onFilterChange={setFilters}
          />
        </div>

        {/* Page Content */}
        <MainContent>
          <div className="max-w-[1400px] mx-auto p-10">
            {currentPage === 'upload' && <UploadArea />}
            {currentPage === 'dashboard' && (
              <DashboardPageNew
                pipeline={pipeline}
                accounts={accounts}
                products={products}
                salesTeams={salesTeams}
                onSelectDeal={(deal) => {
                  setSelectedDeal(deal)
                  setCurrentPage('deal-detail')
                }}
              />
            )}
            {currentPage === 'deals' && !selectedDeal && (
              <DealsPage
                pipeline={pipeline}
                accounts={accounts}
                products={products}
                filters={filters}
                salesTeams={salesTeams}
                onSelectDeal={(deal) => {
                  setSelectedDeal(deal)
                  setCurrentPage('deal-detail')
                }}
              />
            )}
            {currentPage === 'deal-detail' && selectedDeal && (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="flex items-center justify-between mb-8">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setCurrentPage('deals')
                      setSelectedDeal(null)
                    }}
                    className="font-black text-[10px] uppercase tracking-widest border-2"
                  >
                    ← Voltar para Oportunidades
                  </Button>
                </div>
                <DealDetailPage
                  deal={selectedDeal}
                  pipeline={pipeline}
                  accounts={accounts}
                  products={products}
                />
              </div>
            )}
            {currentPage === 'accounts' && (
              <AccountsPage
                pipeline={pipeline}
                accounts={accounts}
                products={products}
              />
            )}
            {currentPage === 'team' && (
              <TeamPage pipeline={pipeline} salesTeams={salesTeams} />
            )}
          </div>
        </MainContent>
      </div>
    </div>
  );
}

function App() {
  return (
    <DataProvider>
      <AppContent />
    </DataProvider>
  )
}

export default App
