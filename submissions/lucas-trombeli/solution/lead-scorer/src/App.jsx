import { useState } from 'react';
import { useData } from './hooks/useData';
import { Sidebar } from './components/Layout/Sidebar';
import { Header } from './components/Layout/Header';
import { Dashboard } from './components/Dashboard/Dashboard';
import { PipelineTable } from './components/Pipeline/PipelineTable';
import { AgentLeaderboard } from './components/Agents/AgentLeaderboard';
import './index.css';

function App() {
  const [currentView, setCurrentView] = useState('pipeline');
  const data = useData();

  if (data.loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
        <div className="loading-text">Loading pipeline data...</div>
      </div>
    );
  }

  if (data.error) {
    return (
      <div className="error-screen">
        <h2>Failed to load data</h2>
        <p>{data.error}</p>
      </div>
    );
  }

  return (
    <div className="app-layout">
      <Sidebar currentView={currentView} onNavigate={setCurrentView} />
      <main className="main-content">
        <Header
          currentView={currentView}
          filters={data.filters}
          filterOptions={data.filterOptions}
          onFilterChange={data.updateFilter}
          onResetFilters={data.resetFilters}
          totalDeals={data.scoredDeals.length}
          filteredCount={data.filteredDeals.length}
        />
        {currentView === 'dashboard' && (
          <Dashboard analytics={data.analytics} />
        )}
        {currentView === 'pipeline' && (
          <PipelineTable deals={data.filteredDeals} />
        )}
        {currentView === 'agents' && (
          <AgentLeaderboard
            agents={data.analytics?.agentLeaderboard || []}
          />
        )}
      </main>
    </div>
  );
}

export default App;
