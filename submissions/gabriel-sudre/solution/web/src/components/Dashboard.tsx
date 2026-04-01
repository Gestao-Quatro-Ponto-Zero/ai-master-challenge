import { useState, useEffect, createContext, useContext } from 'react'
import { api } from '../lib/api'
import { useTheme } from '../hooks/useTheme'
import { Sidebar } from './Sidebar'
import { FloatingChat } from './FloatingChat'
import { DashboardPage } from './DashboardPage'
import { PipelinePage } from './PipelinePage'
import { HistoryPage } from './HistoryPage'

interface AppData {
  metrics: any
  deals: any[]
  history: any[]
  filters: any
  ranking: any[]
  health: any
  reload: () => void
}

export const DataContext = createContext<AppData | null>(null)
export function useData() {
  return useContext(DataContext)!
}

interface Props {
  profile: { email: string; role: string; manager_name?: string | null }
  onSignOut: () => void
}

const PAGE_TITLES: Record<string, string> = {
  dashboard: 'Dashboard',
  pipeline: 'Pipeline',
  history: 'Histórico',
}

export function Dashboard({ profile, onSignOut }: Props) {
  const [activePage, setActivePage] = useState('dashboard')
  const [data, setData] = useState<AppData | null>(null)
  const [loading, setLoading] = useState(true)
  const { theme, toggle: toggleTheme } = useTheme()

  function loadData() {
    setLoading(true)
    api.init()
      .then((res) => setData({
        metrics: res.metrics,
        deals: res.deals,
        history: res.history,
        filters: res.filters,
        ranking: res.ranking,
        health: res.health,
        reload: loadData,
      }))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadData()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)]">
        <div className="text-center">
          <div className="w-10 h-10 rounded-full border-2 border-[var(--g4-gold)] border-t-transparent animate-spin mx-auto mb-4" />
          <p className="text-[var(--text-secondary)] text-sm font-medium">Carregando dados...</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)]">
        <p className="text-[var(--danger)]">Erro ao carregar dados. Recarregue a página.</p>
      </div>
    )
  }

  return (
    <DataContext.Provider value={data}>
      <div className="min-h-screen bg-[var(--bg-primary)]">
        <Sidebar
          activePage={activePage}
          onNavigate={setActivePage}
          profile={profile}
          onSignOut={onSignOut}
          theme={theme}
          onToggleTheme={toggleTheme}
        />

        <main className="ml-56 min-h-screen">
          <header className="sticky top-0 z-30 border-b border-[var(--border)] bg-[var(--bg-primary)]/90 backdrop-blur-md">
            <div className="px-8 py-5 flex items-center justify-between">
              <h2 className="text-xl font-bold text-[var(--g4-navy)] tracking-tight">{PAGE_TITLES[activePage]}</h2>
              <div className="w-8 h-0.5 bg-[var(--g4-gold)] rounded-full" />
            </div>
          </header>

          <div className="p-8">
            {activePage === 'dashboard' && <DashboardPage />}
            {activePage === 'pipeline' && <PipelinePage />}
            {activePage === 'history' && <HistoryPage />}
          </div>
        </main>

        <FloatingChat />
      </div>
    </DataContext.Provider>
  )
}
