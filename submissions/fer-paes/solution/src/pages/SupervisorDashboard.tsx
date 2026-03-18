import { useState, useEffect, useCallback, useRef } from 'react';
import { Activity, RefreshCw, Loader2, ListOrdered, Users, Ticket as TicketIcon } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { markStaleOperatorsOffline } from '../services/presenceService';
import {
  getOverviewMetrics, getQueueMetrics, getOperatorMetrics, getActiveTickets,
  type OverviewMetrics, type QueueMetric, type OperatorMetric, type ActiveTicketRow,
} from '../services/monitoringService';
import OverviewCards        from '../components/supervisor/OverviewCards';
import QueueMonitorPanel    from '../components/supervisor/QueueMonitorPanel';
import OperatorMonitorPanel from '../components/supervisor/OperatorMonitorPanel';
import ActiveTicketsPanel   from '../components/supervisor/ActiveTicketsPanel';

type DashboardTab = 'queues' | 'operators' | 'tickets';

const POLL_INTERVAL_MS = 5_000;

const TABS: { id: DashboardTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'queues',    label: 'Filas',            icon: ListOrdered },
  { id: 'operators', label: 'Operadores',        icon: Users       },
  { id: 'tickets',   label: 'Tickets Ativos',   icon: TicketIcon  },
];

const EMPTY_METRICS: OverviewMetrics = {
  active_tickets:            0,
  queued_tickets:            0,
  online_operators:          0,
  busy_operators:            0,
  avg_response_time_minutes: 0,
  resolved_today:            0,
};

export default function SupervisorDashboard() {
  const { user }                          = useAuth();
  const [activeTab,  setActiveTab]        = useState<DashboardTab>('queues');
  const [metrics,    setMetrics]          = useState<OverviewMetrics>(EMPTY_METRICS);
  const [queues,     setQueues]           = useState<QueueMetric[]>([]);
  const [operators,  setOperators]        = useState<OperatorMetric[]>([]);
  const [tickets,    setTickets]          = useState<ActiveTicketRow[]>([]);
  const [loading,    setLoading]          = useState(true);
  const [lastUpdate, setLastUpdate]       = useState<Date | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(async (showLoader = false) => {
    if (showLoader) setLoading(true);
    try {
      await markStaleOperatorsOffline();
      const [m, q, op, t] = await Promise.all([
        getOverviewMetrics(),
        getQueueMetrics(),
        getOperatorMetrics(),
        getActiveTickets(),
      ]);
      setMetrics(m);
      setQueues(q);
      setOperators(op);
      setTickets(t);
      setLastUpdate(new Date());
    } catch { } finally {
      if (showLoader) setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh(true);

    pollRef.current = setInterval(() => refresh(false), POLL_INTERVAL_MS);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [refresh]);

  function formatLastUpdate(d: Date | null): string {
    if (!d) return 'Nunca';
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  const tabBadge: Record<DashboardTab, number> = {
    queues:    queues.reduce((s, q) => s + q.waiting_tickets, 0),
    operators: operators.filter((op) => op.status === 'online' || op.status === 'busy').length,
    tickets:   tickets.length,
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-6 py-5 border-b border-white/5 shrink-0">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-emerald-600/15 flex items-center justify-center">
              <Activity className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-base font-semibold text-white">Painel do Supervisor</h1>
              <p className="text-xs text-slate-300">Monitoramento operacional em tempo real</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {lastUpdate && (
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400/60 animate-pulse" />
                Atualizado {formatLastUpdate(lastUpdate)}
              </div>
            )}
            <button
              onClick={() => refresh(true)}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs text-slate-400 hover:text-white hover:bg-white/8 disabled:opacity-40 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Atualizar
            </button>
          </div>
        </div>

        <OverviewCards metrics={metrics} loading={loading} />
      </div>

      {/* Tabs + content */}
      {loading ? (
        <div className="flex items-center justify-center flex-1">
          <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
        </div>
      ) : (
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Tab bar */}
          <div className="flex items-center gap-0 px-6 border-b border-white/5 shrink-0">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-2 px-4 py-3.5 text-xs font-medium border-b-2 transition-colors ${
                  activeTab === id
                    ? 'text-emerald-400 border-emerald-400'
                    : 'text-slate-300 border-transparent hover:text-white'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
                {tabBadge[id] > 0 && (
                  <span className={`min-w-[18px] h-[18px] flex items-center justify-center rounded-full text-[10px] font-semibold px-1 ${
                    activeTab === id
                      ? 'bg-emerald-500/20 text-emerald-300'
                      : 'bg-slate-700/80 text-slate-200'
                  }`}>
                    {tabBadge[id]}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-auto px-6 py-5">
            {activeTab === 'queues' && (
              <QueueMonitorPanel queues={queues} onRefresh={() => refresh(false)} />
            )}
            {activeTab === 'operators' && (
              <OperatorMonitorPanel operators={operators} />
            )}
            {activeTab === 'tickets' && (
              <ActiveTicketsPanel
                tickets={tickets}
                operators={operators}
                supervisorUserId={user?.id ?? ''}
                onRefresh={() => refresh(false)}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
