import { useState, useEffect, useCallback } from 'react';
import {
  BarChart2, Loader2, RefreshCw, AlertCircle, Eye,
  MousePointerClick, MessageCircle, Zap, ChevronRight,
} from 'lucide-react';
import {
  getAllCampaignAnalytics,
  getAnalyticsOverview,
  getCampaignMetrics,
  syncCampaignMetrics,
  type CampaignAnalyticsRow,
  type AnalyticsOverview,
  type CampaignMetrics,
} from '../services/campaignAnalyticsService';
import CampaignAnalyticsOverview from '../components/campaigns/CampaignAnalyticsOverview';
import CampaignMetricsTable      from '../components/campaigns/CampaignMetricsTable';
import CampaignPerformanceChart  from '../components/campaigns/CampaignPerformanceChart';

function DetailMetric({ label, count, rate, icon: Icon, color, bg }: {
  label: string; count: number; rate: number;
  icon: React.ComponentType<{ className?: string }>;
  color: string; bg: string;
}) {
  return (
    <div className={`rounded-xl border px-4 py-3 ${bg} border-opacity-50`}>
      <div className="flex items-center gap-2 mb-1">
        <Icon className={`w-3.5 h-3.5 ${color}`} />
        <span className={`text-xs font-medium ${color}`}>{label}</span>
      </div>
      <div className="flex items-end gap-2">
        <span className={`text-xl font-bold tabular-nums ${color}`}>
          {count.toLocaleString('pt-BR')}
        </span>
        <span className="text-xs text-gray-400 pb-0.5">{rate}%</span>
      </div>
    </div>
  );
}

export default function CampaignAnalyticsPage() {
  const [rows,       setRows]       = useState<CampaignAnalyticsRow[]>([]);
  const [overview,   setOverview]   = useState<AnalyticsOverview | null>(null);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState('');
  const [selected,   setSelected]   = useState<CampaignAnalyticsRow | null>(null);
  const [detail,     setDetail]     = useState<CampaignMetrics | null>(null);
  const [detailLoad, setDetailLoad] = useState(false);
  const [syncing,    setSyncing]    = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const [r, o] = await Promise.all([getAllCampaignAnalytics(), getAnalyticsOverview()]);
      setRows(r);
      setOverview(o);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar analytics.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!selected) { setDetail(null); return; }
    setDetailLoad(true);
    getCampaignMetrics(selected.campaign_id)
      .then(setDetail)
      .catch(() => setDetail(null))
      .finally(() => setDetailLoad(false));
  }, [selected]);

  async function handleSync() {
    if (!selected) return;
    setSyncing(true);
    try {
      await syncCampaignMetrics(selected.campaign_id);
      await load();
      const refreshed = await getCampaignMetrics(selected.campaign_id);
      setDetail(refreshed);
    } catch {
      // ignore
    } finally {
      setSyncing(false);
    }
  }

  return (
    <div className="flex-1 flex min-h-0 bg-gray-50 overflow-hidden">
      {/* Main panel */}
      <div className="flex-1 flex flex-col overflow-auto">
        {/* Header */}
        <div className="bg-white border-b border-gray-100 px-8 py-5 shrink-0">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-teal-50 flex items-center justify-center">
                <BarChart2 className="w-5 h-5 text-teal-600" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">Campaign Analytics</h1>
                <p className="text-sm text-gray-400">Performance de campanhas — envios, aberturas, cliques e conversões</p>
              </div>
            </div>
            <button
              onClick={load}
              disabled={loading}
              className="flex items-center gap-1.5 h-9 px-4 rounded-xl bg-white text-gray-600 text-sm border border-gray-200 hover:bg-gray-50 disabled:opacity-60 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Atualizar
            </button>
          </div>
        </div>

        <div className="flex-1 px-8 py-6 space-y-6 min-h-0">
          {error && (
            <div className="px-4 py-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          {/* Overview cards */}
          <CampaignAnalyticsOverview overview={overview} loading={loading} />

          {/* Chart */}
          <CampaignPerformanceChart rows={rows} loading={loading} />

          {/* Table */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-gray-400" />
              <h2 className="text-sm font-semibold text-gray-700">Performance por Campanha</h2>
              {loading && <Loader2 className="w-3.5 h-3.5 text-gray-300 animate-spin" />}
              <span className="text-xs text-gray-400">
                {rows.length} campanha{rows.length !== 1 ? 's' : ''}
              </span>
              {selected && (
                <span className="ml-auto text-xs text-sky-500 flex items-center gap-1">
                  Clique em uma linha para ver detalhes
                  <ChevronRight className="w-3 h-3" />
                </span>
              )}
            </div>
            <CampaignMetricsTable
              rows={rows}
              loading={loading}
              onSelect={setSelected}
              selected={selected?.campaign_id}
            />
          </div>
        </div>
      </div>

      {/* Detail sidebar */}
      {selected && (
        <div className="w-80 shrink-0 border-l border-gray-100 bg-white flex flex-col overflow-y-auto">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-gray-800 truncate max-w-[200px]">{selected.campaign_name}</h3>
              <p className="text-xs text-gray-400">{selected.segment_name ?? 'Sem segmento'}</p>
            </div>
            <button
              onClick={() => setSelected(null)}
              className="w-6 h-6 rounded-lg flex items-center justify-center text-gray-300 hover:text-gray-500 hover:bg-gray-100 transition-colors"
            >
              ×
            </button>
          </div>

          {detailLoad ? (
            <div className="flex-1 flex items-center justify-center">
              <Loader2 className="w-5 h-5 text-gray-300 animate-spin" />
            </div>
          ) : (
            <div className="p-5 space-y-4">
              {/* Funnel totals */}
              <div className="space-y-2">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Totais</p>
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-sky-50 rounded-xl p-3">
                    <p className="text-xs text-sky-500 mb-1">Enviados</p>
                    <p className="text-xl font-bold text-sky-600 tabular-nums">{selected.sent_count.toLocaleString('pt-BR')}</p>
                  </div>
                  <div className="bg-emerald-50 rounded-xl p-3">
                    <p className="text-xs text-emerald-500 mb-1">Entregues</p>
                    <p className="text-xl font-bold text-emerald-600 tabular-nums">{selected.delivered_count.toLocaleString('pt-BR')}</p>
                  </div>
                </div>
              </div>

              {/* Engagement metrics */}
              <div className="space-y-2">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Engajamento</p>
                <div className="space-y-2">
                  <DetailMetric
                    label="Aberturas"     count={selected.open_count}       rate={selected.open_rate}
                    icon={Eye}            color="text-blue-600"  bg="bg-blue-50"
                  />
                  <DetailMetric
                    label="Cliques"       count={selected.click_count}      rate={selected.click_rate}
                    icon={MousePointerClick} color="text-violet-600" bg="bg-violet-50"
                  />
                  <DetailMetric
                    label="Respostas"     count={selected.reply_count}      rate={selected.reply_rate}
                    icon={MessageCircle}  color="text-amber-600" bg="bg-amber-50"
                  />
                  <DetailMetric
                    label="Conversões"    count={selected.conversion_count} rate={selected.conversion_rate}
                    icon={Zap}            color="text-teal-600"  bg="bg-teal-50"
                  />
                </div>
              </div>

              {/* Mini funnel */}
              {selected.sent_count > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Funil</p>
                  <div className="bg-gray-50 rounded-xl p-3 space-y-2">
                    {[
                      { l: 'Entregues',  v: selected.delivered_count,   base: selected.sent_count,      bar: 'bg-emerald-400' },
                      { l: 'Abertos',    v: selected.open_count,        base: selected.delivered_count, bar: 'bg-blue-400'    },
                      { l: 'Clicados',   v: selected.click_count,       base: selected.delivered_count, bar: 'bg-violet-400'  },
                      { l: 'Convertidos',v: selected.conversion_count,  base: selected.delivered_count, bar: 'bg-teal-400'    },
                    ].map(({ l, v, base, bar }) => {
                      const pct = base > 0 ? Math.round(v / base * 100) : 0;
                      return (
                        <div key={l}>
                          <div className="flex justify-between text-[10px] text-gray-400 mb-0.5">
                            <span>{l}</span>
                            <span className="tabular-nums">{v.toLocaleString('pt-BR')} ({pct}%)</span>
                          </div>
                          <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div className={`h-full ${bar} rounded-full`} style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {detail?.updated_at && (
                <p className="text-[10px] text-gray-300 text-center">
                  Atualizado em {new Date(detail.updated_at).toLocaleString('pt-BR')}
                </p>
              )}

              <button
                onClick={handleSync}
                disabled={syncing}
                className="w-full h-8 rounded-xl bg-gray-50 border border-gray-100 text-xs text-gray-500 hover:bg-gray-100 transition-colors flex items-center justify-center gap-1.5 disabled:opacity-60"
              >
                <RefreshCw className={`w-3 h-3 ${syncing ? 'animate-spin' : ''}`} />
                Sincronizar métricas
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
