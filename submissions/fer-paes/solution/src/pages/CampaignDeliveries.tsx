import { useState, useEffect, useCallback } from 'react';
import { Send, Loader2, Filter, RefreshCw, RotateCcw, AlertCircle, ChevronDown } from 'lucide-react';
import {
  getDeliveries,
  getCampaignDeliveryStats,
  retryFailedDeliveries,
  type CampaignDelivery,
  type DeliveryStats,
  type DeliveryStatus,
  type DeliveryChannel,
  DELIVERY_STATUSES,
  DELIVERY_CHANNELS,
  STATUS_META,
  CHANNEL_META,
} from '../services/campaignDeliveryService';
import { getCampaigns, type Campaign } from '../services/campaignService';
import CampaignDeliveriesTable    from '../components/campaigns/CampaignDeliveriesTable';
import CampaignDeliveryStats      from '../components/campaigns/CampaignDeliveryStats';

export default function CampaignDeliveries() {
  const [deliveries,    setDeliveries]    = useState<CampaignDelivery[]>([]);
  const [campaigns,     setCampaigns]     = useState<Campaign[]>([]);
  const [stats,         setStats]         = useState<DeliveryStats | null>(null);
  const [loading,       setLoading]       = useState(true);
  const [statsLoading,  setStatsLoading]  = useState(false);
  const [error,         setError]         = useState('');
  const [retrying,      setRetrying]      = useState(false);
  const [retryMsg,      setRetryMsg]      = useState('');

  const [filterCampaign, setFilterCampaign] = useState('');
  const [filterStatus,   setFilterStatus]   = useState<DeliveryStatus | ''>('');
  const [filterChannel,  setFilterChannel]  = useState<DeliveryChannel | ''>('');

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const [dels, cps] = await Promise.all([
        getDeliveries({
          campaign_id: filterCampaign || undefined,
          status:      (filterStatus  as DeliveryStatus)  || undefined,
          channel:     (filterChannel as DeliveryChannel) || undefined,
          limit:       200,
        }),
        getCampaigns(),
      ]);
      setDeliveries(dels);
      setCampaigns(cps);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar entregas.');
    } finally {
      setLoading(false);
    }
  }, [filterCampaign, filterStatus, filterChannel]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!filterCampaign) { setStats(null); return; }
    setStatsLoading(true);
    getCampaignDeliveryStats(filterCampaign)
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setStatsLoading(false));
  }, [filterCampaign]);

  async function handleRetry() {
    if (!filterCampaign) return;
    setRetrying(true); setRetryMsg('');
    try {
      const count = await retryFailedDeliveries(filterCampaign);
      setRetryMsg(`${count} entrega${count !== 1 ? 's' : ''} recolocada${count !== 1 ? 's' : ''} na fila.`);
      await load();
    } catch (err) {
      setRetryMsg(err instanceof Error ? err.message : 'Erro ao reenviar.');
    } finally {
      setRetrying(false);
    }
  }

  const failedCount = deliveries.filter((d) => d.status === 'failed').length;

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-gray-50 overflow-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 px-8 py-5 shrink-0">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-50 flex items-center justify-center">
              <Send className="w-5 h-5 text-sky-600" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">Motor de Entregas</h1>
              <p className="text-sm text-gray-400">Rastreamento de entregas de campanhas por cliente e canal</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {filterCampaign && failedCount > 0 && (
              <button
                onClick={handleRetry}
                disabled={retrying}
                className="flex items-center gap-1.5 h-9 px-4 rounded-xl bg-red-50 text-red-600 text-sm font-medium hover:bg-red-100 border border-red-100 disabled:opacity-60 transition-colors"
              >
                {retrying
                  ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  : <RotateCcw className="w-3.5 h-3.5" />
                }
                Reenviar falhas ({failedCount})
              </button>
            )}
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
      </div>

      <div className="flex-1 px-8 py-6 space-y-5 min-h-0">
        {error && (
          <div className="px-4 py-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}

        {retryMsg && (
          <div className="px-4 py-3 rounded-xl bg-emerald-50 border border-emerald-100 text-emerald-700 text-sm">
            {retryMsg}
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-2xl border border-gray-100 px-5 py-4">
          <div className="flex items-center gap-2 mb-3">
            <Filter className="w-3.5 h-3.5 text-gray-400" />
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Filtros</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Campaign filter */}
            <div className="relative">
              <select
                value={filterCampaign}
                onChange={(e) => setFilterCampaign(e.target.value)}
                className="w-full h-9 pl-3 pr-8 rounded-xl border border-gray-200 text-sm text-gray-700 bg-white appearance-none focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-400 transition-all"
              >
                <option value="">Todas as campanhas</option>
                {campaigns.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
            </div>

            {/* Status filter */}
            <div className="relative">
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as DeliveryStatus | '')}
                className="w-full h-9 pl-3 pr-8 rounded-xl border border-gray-200 text-sm text-gray-700 bg-white appearance-none focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-400 transition-all"
              >
                <option value="">Todos os status</option>
                {DELIVERY_STATUSES.map((s) => (
                  <option key={s} value={s}>{STATUS_META[s].label}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
            </div>

            {/* Channel filter */}
            <div className="relative">
              <select
                value={filterChannel}
                onChange={(e) => setFilterChannel(e.target.value as DeliveryChannel | '')}
                className="w-full h-9 pl-3 pr-8 rounded-xl border border-gray-200 text-sm text-gray-700 bg-white appearance-none focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-400 transition-all"
              >
                <option value="">Todos os canais</option>
                {DELIVERY_CHANNELS.map((ch) => (
                  <option key={ch} value={ch}>{CHANNEL_META[ch].label}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
            </div>
          </div>
        </div>

        {/* Stats — only when campaign is selected */}
        {(filterCampaign || statsLoading) && (
          <CampaignDeliveryStats stats={stats} loading={statsLoading} />
        )}

        {/* Table */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Send className="w-4 h-4 text-gray-400" />
            <h2 className="text-sm font-semibold text-gray-700">Registro de Entregas</h2>
            {loading && <Loader2 className="w-3.5 h-3.5 text-gray-300 animate-spin ml-1" />}
            <span className="text-xs text-gray-400 ml-1">
              {deliveries.length} registro{deliveries.length !== 1 ? 's' : ''}
            </span>
          </div>
          <CampaignDeliveriesTable
            deliveries={deliveries}
            loading={loading}
          />
        </div>
      </div>
    </div>
  );
}
