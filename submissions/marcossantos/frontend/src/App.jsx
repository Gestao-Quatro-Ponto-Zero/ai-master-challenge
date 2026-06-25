// App.jsx
import { useState } from 'react'
import Sidebar     from './components/Sidebar.jsx'
import TopBar      from './components/TopBar.jsx'
import DealsTable  from './components/DealsTable.jsx'
import DetailPanel from './components/DetailPanel.jsx'
import { usePipeline, useFilters, useSummary } from './hooks/useApi.js'

export default function App() {
  const [filters, setFilters] = useState({
    agent: '', manager: '', region: '', stage: '', product: ''
  })
  const [selectedDeal, setSelectedDeal] = useState(null)

  // Dados da API
  const { filters: filterOptions } = useFilters()
  const { data, loading, error }   = usePipeline(filters)
  const summary                    = useSummary(filters)

  const deals = data?.deals || []

  function handleSelectDeal(deal) {
    // Toggle: clica no mesmo deal = fecha o painel
    setSelectedDeal(prev =>
      prev?.opportunity_id === deal.opportunity_id ? null : deal
    )
  }

  return (
    <div className="app-layout">
      {/* Sidebar com filtros */}
      <Sidebar
        filters={filters}
        setFilters={setFilters}
        filterOptions={filterOptions}
        summary={summary}
      />

      {/* Área principal */}
      <div className="main-area">
        {/* KPI bar */}
        <TopBar summary={summary} filters={filters} />

        {/* Tabela */}
        <div className="table-container">
          <div className="table-header-row">
            <span className="table-title">
              Deals prioritizados por score
            </span>
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
      </div>

      {/* Painel de detalhe (slide-in) */}
      {selectedDeal && (
        <DetailPanel
          deal={selectedDeal}
          onClose={() => setSelectedDeal(null)}
        />
      )}
    </div>
  )
}