import React, { useState, useCallback } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@radix-ui/react-tabs';
import { BarChart3, TrendingUp, LayoutDashboard } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLanguage } from './i18n/LanguageContext';
import { LanguageSwitcher } from './components/LanguageSwitcher';
import { FilterBar } from './components/FilterBar';
import { OpportunitiesTable, DealDetailModal } from './components/OpportunitiesTable';
import { DashboardStats, TimeOnPipelineChart, AccountSizeChart } from './components/Dashboard';
import { ForecastCard } from './components/ForecastCard';
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50">
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        className="bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-900 text-white shadow-lg"
      >
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-indigo-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm ring-1 ring-white/10">
                <LayoutDashboard className="w-5 h-5 text-indigo-300" />
              </div>
              <div>
                <h1 className="text-2xl font-extrabold tracking-tight">{t('header.title')}</h1>
              </div>
            </div>
            <LanguageSwitcher />
          </div>
          <p className="text-slate-400 text-sm font-medium">
            {t('header.subtitle')}
          </p>
        </div>
      </motion.header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        <Tabs defaultValue="pipeline" className="w-full">
          <TabsList className="inline-flex w-auto bg-white p-1 rounded-xl border border-gray-200 shadow-sm" role="tablist">
            <TabsTrigger
              value="pipeline"
              className="flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold text-gray-500 data-[state=active]:bg-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-150"
            >
              <BarChart3 className="w-4 h-4" aria-hidden="true" />
              {t('tabs.pipeline')}
            </TabsTrigger>
            <TabsTrigger
              value="analytics"
              className="flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold text-gray-500 data-[state=active]:bg-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-150"
            >
              <TrendingUp className="w-4 h-4" aria-hidden="true" />
              {t('tabs.analytics')}
            </TabsTrigger>
          </TabsList>

          <AnimatePresence mode="wait">
            <TabsContent key="pipeline" value="pipeline" className="space-y-6 mt-6">
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.2 }}
              >
                <FilterBar onFiltersChange={handleFiltersChange} onRefresh={handleRefresh} />
                <div className="mt-6">
                  <OpportunitiesTable
                    filters={filters}
                    refreshTrigger={refreshTrigger}
                    selectedDeal={selectedDeal}
                    onSelectDeal={setSelectedDeal}
                  />
                </div>
              </motion.div>
            </TabsContent>

            <TabsContent key="analytics" value="analytics" className="space-y-6 mt-6">
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.2 }}
              >
                <DashboardStats />
                <div className="mt-6">
                  <ForecastCard />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                  <TimeOnPipelineChart />
                  <AccountSizeChart />
                </div>
              </motion.div>
            </TabsContent>
          </AnimatePresence>
        </Tabs>
      </main>

      <AnimatePresence>
        {selectedDeal && (
          <DealDetailModal deal={selectedDeal} onClose={() => setSelectedDeal(null)} />
        )}
      </AnimatePresence>

      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6 text-center text-sm text-gray-500">
          <p className="tabular-nums">
            {t('footer.scoringFormula')}
          </p>
        </div>
      </footer>
    </div>
  );
}
