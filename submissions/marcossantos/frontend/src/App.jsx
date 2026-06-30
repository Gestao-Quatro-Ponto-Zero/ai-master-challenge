// App.jsx
import { useState } from 'react'
import { useAuth }       from './context/AuthContext'
import LoginPage         from './components/LoginPage'
import Sidebar           from './components/Sidebar'
import TopBar            from './components/TopBar'
import DealsTable        from './components/DealsTable'
import DetailPanel       from './components/DetailPanel'
import AlertsPanel       from './components/AlertsPanel'
import AnalyticsPage     from './components/analytics/AnalyticsPage'
import { usePipeline, useFilters, useSummary, useAlerts } from './hooks/useApi'

function Dashboard() {
  const [view, setView]                 = useState('pipeline')
  const [filters, setFilters]           = useState({ agent: '', manager: '', region: '', stage: '', product: '' })
  const [selectedDeal, setSelectedDeal] = useState(null)
  const [showAlerts,   setShowAlerts]   = useState(false)

  const { filters: filterOptions } = useFilters()
  const { data, loading, error }   = usePipeline(filters)
  const summary                    = useSummary(filters)
  const { data: alertsData, dismiss, dismissAll, refresh: refreshAlerts } = useAlerts()

  const deals = data?.deals || []

  function handleSelectDeal(deal) {
    setShowAlerts(false)
    setSelectedDeal(prev => prev?.opportunity_id === deal.opportunity_id ? null : deal)
  }

  function handleAlertsClick() {
    setSelectedDeal(null)
    setShowAlerts(prev => !prev)
  }

  function handleViewChange(v) {
    setView(v)
    setSelectedDeal(null)
    setShowAlerts(false)
  }

  return (
    <div className="app-layout">
      <Sidebar
        filters={filters}
        setFilters={setFilters}
        filterOptions={filterOptions}
        summary={summary}
        view={view}
        onViewChange={handleViewChange}
      />
      <div className="main-area">
        {view === 'pipeline' && (
          <TopBar
            summary={summary}
            filters={filters}
            alertsData={alertsData}
            onAlertsClick={handleAlertsClick}
          />
        )}
        {view === 'pipeline' && (
          <div className="table-container">
            <div className="table-header-row">
              <span className="table-title">Deals prioritizados por score</span>
              {!loading && deals.length > 0 && (
                <span className="table-count">{deals.length} deals</span>
              )}
            </div>
            <DealsTable
              deals={deals}
              loading={loading}
              error={error}
              selectedId={selectedDeal?.opportunity_id}
              onSelect={handleSelectDeal}
            />
          </div>
        )}
        {view === 'analytics' && <AnalyticsPage />}
      </div>
      {selectedDeal && !showAlerts && (
        <DetailPanel deal={selectedDeal} onClose={() => setSelectedDeal(null)} />
      )}
      {showAlerts && (
        <AlertsPanel
          alertsData={alertsData}
          onDismiss={dismiss}
          onDismissAll={dismissAll}
          onRefresh={refreshAlerts}
          onClose={() => setShowAlerts(false)}
        />
      )}
    </div>
  )
}

export default function App() {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <Dashboard /> : <LoginPage />
}