import { useState, useEffect, useCallback } from 'react';
import { Ticket, CheckCircle2, Clock, BarChart3, RefreshCw, XCircle } from 'lucide-react';
import { getTicketStats, formatResponseTime, type TicketStats } from '../../services/ticketStatsService';

const REFRESH_INTERVAL_MS = 30_000;

interface StatCardProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | number;
  sub?: string;
  accent: string;
  iconBg: string;
  loading?: boolean;
}

function StatCard({ icon: Icon, label, value, sub, accent, iconBg, loading }: StatCardProps) {
  return (
    <div className={`bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden relative group transition-shadow hover:shadow-md`}>
      <div className={`absolute inset-x-0 top-0 h-0.5 ${accent}`} />
      <div className="px-5 py-4 flex items-start gap-4">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${iconBg}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">{label}</p>
          {loading ? (
            <div className="h-7 w-16 bg-gray-100 rounded-lg animate-pulse" />
          ) : (
            <p className="text-2xl font-bold text-gray-900 tabular-nums leading-none">{value}</p>
          )}
          {sub && !loading && (
            <p className="text-xs text-gray-400 mt-1">{sub}</p>
          )}
        </div>
      </div>
    </div>
  );
}

interface TicketStatsProps {
  className?: string;
}

export default function TicketStats({ className }: TicketStatsProps) {
  const [stats, setStats] = useState<TicketStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchStats = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true);
    setError(null);
    try {
      const data = await getTicketStats();
      setStats(data);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stats');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(() => fetchStats(), REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchStats]);

  const resolvedRate =
    stats && stats.total_tickets > 0
      ? Math.round(((stats.resolved_tickets + stats.closed_tickets) / stats.total_tickets) * 100)
      : 0;

  const cards: StatCardProps[] = [
    {
      icon: BarChart3,
      label: 'Total Tickets',
      value: loading ? '—' : (stats?.total_tickets ?? 0),
      sub: 'all time',
      accent: 'bg-slate-400',
      iconBg: 'bg-slate-500',
    },
    {
      icon: Ticket,
      label: 'Open Tickets',
      value: loading ? '—' : (stats?.open_tickets ?? 0),
      sub: 'awaiting response',
      accent: 'bg-blue-400',
      iconBg: 'bg-blue-500',
    },
    {
      icon: CheckCircle2,
      label: 'Resolved',
      value: loading ? '—' : (stats?.resolved_tickets ?? 0),
      sub: loading ? undefined : `${resolvedRate}% resolution rate`,
      accent: 'bg-emerald-400',
      iconBg: 'bg-emerald-500',
    },
    {
      icon: Clock,
      label: 'Avg First Response',
      value: loading ? '—' : formatResponseTime(stats?.avg_response_time_seconds ?? null),
      sub: 'first operator reply',
      accent: 'bg-amber-400',
      iconBg: 'bg-amber-500',
    },
  ];

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-gray-700">Ticket Overview</h2>
        <div className="flex items-center gap-3">
          {lastUpdated && !loading && (
            <span className="text-xs text-gray-400">
              Updated {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
          <button
            onClick={() => fetchStats(true)}
            disabled={refreshing || loading}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors disabled:opacity-40"
            title="Refresh stats"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600 mb-3">
          <XCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {cards.map((card) => (
          <StatCard key={card.label} {...card} loading={loading} />
        ))}
      </div>
    </div>
  );
}
