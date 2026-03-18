import { useState, useEffect, useCallback } from 'react';
import { BarChart2, RefreshCw, Search, Loader2, Users } from 'lucide-react';
import {
  getCustomerAnalyticsSummary,
  getCustomerAnalyticsList,
  getTopCustomersByEngagement,
  refreshAllCustomerAnalytics,
  type CustomerAnalyticsSummary,
  type CustomerAnalyticsRow,
  type TopCustomerRow,
} from '../services/customerAnalyticsService';
import CustomerAnalyticsOverview  from '../components/customer-analytics/CustomerAnalyticsOverview';
import CustomerAnalyticsTable     from '../components/customer-analytics/CustomerAnalyticsTable';
import TopCustomersTable          from '../components/customer-analytics/TopCustomersTable';
import CustomerEngagementChart    from '../components/customer-analytics/CustomerEngagementChart';

export default function CustomerAnalytics() {
  const [summary,    setSummary]    = useState<CustomerAnalyticsSummary | null>(null);
  const [rows,       setRows]       = useState<CustomerAnalyticsRow[]>([]);
  const [topCustomers, setTopCustomers] = useState<TopCustomerRow[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState('');
  const [search,     setSearch]     = useState('');
  const [recalculating, setRecalculating] = useState(false);
  const [lastUpdated,   setLastUpdated]   = useState<Date | null>(null);

  const load = useCallback(async (q: string) => {
    setLoading(true);
    setError('');
    try {
      const [sum, list, top] = await Promise.all([
        getCustomerAnalyticsSummary(),
        getCustomerAnalyticsList(q),
        getTopCustomersByEngagement(10),
      ]);
      setSummary(sum);
      setRows(list);
      setTopCustomers(top);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar analytics.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => load(search), search ? 400 : 0);
    return () => clearTimeout(t);
  }, [search, load]);

  async function handleRecalculateAll() {
    setRecalculating(true);
    setError('');
    try {
      const count = await refreshAllCustomerAnalytics();
      await load(search);
      setError('');
      console.info(`Recalculados ${count} clientes.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao recalcular analytics.');
    } finally {
      setRecalculating(false);
    }
  }

  async function handleRowRefreshed(customerId: string) {
    const [sum, list, top] = await Promise.all([
      getCustomerAnalyticsSummary(),
      getCustomerAnalyticsList(search),
      getTopCustomersByEngagement(10),
    ]).catch(() => [summary, rows, topCustomers]);
    if (sum)  setSummary(sum  as CustomerAnalyticsSummary);
    if (list) setRows(list    as CustomerAnalyticsRow[]);
    if (top)  setTopCustomers(top as TopCustomerRow[]);
    void customerId;
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-gray-50 overflow-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 px-8 py-5 shrink-0">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
              <BarChart2 className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">Analytics de Clientes</h1>
              <p className="text-sm text-gray-400">
                Métricas de comportamento e engajamento
                {lastUpdated && (
                  <span className="text-gray-300 ml-2">
                    · atualizado às {lastUpdated.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                )}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => load(search)}
              disabled={loading}
              className="w-9 h-9 flex items-center justify-center rounded-xl border border-gray-200 text-gray-400 hover:text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
              title="Atualizar"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={handleRecalculateAll}
              disabled={recalculating || loading}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 active:scale-95 transition-all shadow-sm shadow-blue-200"
            >
              {recalculating ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              {recalculating ? 'Recalculando...' : 'Recalcular Tudo'}
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 px-8 py-6 space-y-6">
        {error && (
          <div className="px-4 py-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm">
            {error}
          </div>
        )}

        {/* Overview cards */}
        <CustomerAnalyticsOverview summary={summary} loading={loading} />

        {/* Chart + Top customers */}
        <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
          <div className="xl:col-span-2">
            <CustomerEngagementChart data={rows} loading={loading} />
          </div>
          <div className="xl:col-span-3">
            <TopCustomersTable data={topCustomers} loading={loading} />
          </div>
        </div>

        {/* Analytics table */}
        <div>
          <div className="flex items-center justify-between mb-3 gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-gray-400" />
              <h2 className="text-sm font-semibold text-gray-700">Analytics por Cliente</h2>
              {rows.length > 0 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-blue-50 border border-blue-100 text-xs font-medium text-blue-600">
                  {rows.length}
                </span>
              )}
            </div>

            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar por nome ou e-mail..."
                className="pl-9 pr-4 py-2 rounded-xl border border-gray-200 text-sm text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all w-64"
              />
            </div>
          </div>

          <CustomerAnalyticsTable
            data={rows}
            loading={loading}
            onRefreshed={handleRowRefreshed}
          />
        </div>
      </div>
    </div>
  );
}
