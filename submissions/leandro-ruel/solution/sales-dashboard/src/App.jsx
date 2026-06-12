import React, { useState, useCallback } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@radix-ui/react-tabs';
import { BarChart3, TrendingUp } from 'lucide-react';
import { useLanguage } from './i18n/LanguageContext';
import { LanguageSwitcher } from './components/LanguageSwitcher';
import { FilterBar } from './components/FilterBar';
import { OpportunitiesTable, DealDetailModal } from './components/OpportunitiesTable';
import { DashboardStats, TimeOnPipelineChart, AccountSizeChart } from './components/Dashboard';
import './index.css';

export default function App() {
  const { t } = useLanguage();
  const [filters, setFilters] = useState({
    sales_agent: '',
    deal_stage: '',
    product: '',
    account: '',
    min_score: '',
  });

  const [selectedDeal, setSelectedDeal] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleFiltersChange = useCallback((newFilters) => {
    setFilters(newFilters);
  }, []);

  const handleRefresh = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-slate-900 to-slate-800 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <BarChart3 className="w-8 h-8" />
              <h1 className="text-3xl font-bold">{t('header.title')}</h1>
            </div>
            <LanguageSwitcher />
          </div>
          <p className="text-slate-300 text-sm">
            {t('header.subtitle')}
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Tabs */}
        <Tabs defaultValue="pipeline" className="w-full">
          <TabsList className="grid w-full max-w-md grid-cols-2 bg-white p-1 rounded-lg border border-gray-200 shadow">
            <TabsTrigger
              value="pipeline"
              className="rounded px-4 py-2 text-sm font-medium text-gray-700 data-[state=active]:bg-blue-600 data-[state=active]:text-white transition-all"
            >
              📋 {t('tabs.pipeline')}
            </TabsTrigger>
            <TabsTrigger
              value="analytics"
              className="rounded px-4 py-2 text-sm font-medium text-gray-700 data-[state=active]:bg-blue-600 data-[state=active]:text-white transition-all"
            >
              <TrendingUp className="w-4 h-4 mr-2 inline" />
              {t('tabs.analytics')}
            </TabsTrigger>
          </TabsList>

          {/* Pipeline Tab */}
          <TabsContent value="pipeline" className="space-y-6 mt-6">
            <FilterBar onFiltersChange={handleFiltersChange} onRefresh={handleRefresh} />
            <OpportunitiesTable
              filters={filters}
              refreshTrigger={refreshTrigger}
              selectedDeal={selectedDeal}
              onSelectDeal={setSelectedDeal}
            />
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-6 mt-6">
            <DashboardStats />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <TimeOnPipelineChart />
              <AccountSizeChart />
            </div>
          </TabsContent>
        </Tabs>
      </main>

      {/* Deal Detail Modal */}
      {selectedDeal && (
        <DealDetailModal deal={selectedDeal} onClose={() => setSelectedDeal(null)} />
      )}

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6 text-center text-sm text-gray-600">
          <p>
            💡 <strong>{t('language')}:</strong> {t('footer.scoringFormula')}
          </p>
        </div>
      </footer>
    </div>
  );
}
