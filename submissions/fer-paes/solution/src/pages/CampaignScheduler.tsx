import { useState, useEffect, useCallback } from 'react';
import { Clock, Plus, Loader2, CalendarClock, RefreshCw, Zap, AlertCircle, CheckCircle2 } from 'lucide-react';
import {
  getSchedules,
  getDueSchedules,
  type CampaignSchedule,
  type ScheduleType,
} from '../services/campaignSchedulerService';
import CampaignSchedulesTable from '../components/scheduler/CampaignSchedulesTable';
import ScheduleCreateModal    from '../components/scheduler/ScheduleCreateModal';

type FilterType = 'all' | ScheduleType | 'inactive';

const TYPE_TABS: { value: FilterType; label: string }[] = [
  { value: 'all',            label: 'Todos'        },
  { value: 'once',           label: 'Envio Único'  },
  { value: 'recurring',      label: 'Recorrentes'  },
  { value: 'event_triggered',label: 'Por Evento'   },
  { value: 'inactive',       label: 'Inativos'     },
];

function StatCard({
  label,
  value,
  icon:  Icon,
  color,
  sub,
}: {
  label:  string;
  value:  number | string;
  icon:   React.ComponentType<{ className?: string }>;
  color:  string;
  sub?:   string;
}) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 px-5 py-4 flex items-center gap-3">
      <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${color}`}>
        <Icon className="w-4 h-4 text-current" />
      </div>
      <div>
        <p className="text-xs text-gray-400">{label}</p>
        <p className="text-xl font-bold text-gray-900 tabular-nums">{value}</p>
        {sub && <p className="text-xs text-gray-400">{sub}</p>}
      </div>
    </div>
  );
}

export default function CampaignScheduler() {
  const [schedules,    setSchedules]    = useState<CampaignSchedule[]>([]);
  const [dueSchedules, setDueSchedules] = useState<CampaignSchedule[]>([]);
  const [loading,      setLoading]      = useState(true);
  const [error,        setError]        = useState('');
  const [activeFilter, setActiveFilter] = useState<FilterType>('all');
  const [showCreate,   setShowCreate]   = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const [all, due] = await Promise.all([getSchedules(), getDueSchedules()]);
      setSchedules(all);
      setDueSchedules(due);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar agendamentos.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, []);

  const filtered = schedules.filter((s) => {
    if (activeFilter === 'all')     return true;
    if (activeFilter === 'inactive') return !s.is_active;
    return s.schedule_type === activeFilter && s.is_active;
  });

  const stats = {
    total:      schedules.length,
    active:     schedules.filter((s) => s.is_active).length,
    once:       schedules.filter((s) => s.schedule_type === 'once'            && s.is_active).length,
    recurring:  schedules.filter((s) => s.schedule_type === 'recurring'       && s.is_active).length,
    event:      schedules.filter((s) => s.schedule_type === 'event_triggered' && s.is_active).length,
    due:        dueSchedules.length,
  };

  const nextDue = schedules
    .filter((s) => s.is_active && s.next_run_at)
    .sort((a, b) => new Date(a.next_run_at!).getTime() - new Date(b.next_run_at!).getTime())[0];

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-gray-50 overflow-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 px-8 py-5 shrink-0">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
              <Clock className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">Agendador de Campanhas</h1>
              <p className="text-sm text-gray-400">Agende campanhas para execução automática, recorrente ou por evento</p>
            </div>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-1.5 h-9 px-4 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Novo agendamento
          </button>
        </div>
      </div>

      <div className="flex-1 px-8 py-6 space-y-5 min-h-0">
        {error && (
          <div className="px-4 py-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm">
            {error}
          </div>
        )}

        {/* Due alert */}
        {stats.due > 0 && (
          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-amber-50 border border-amber-100">
            <AlertCircle className="w-4 h-4 text-amber-500 shrink-0" />
            <div>
              <p className="text-sm font-medium text-amber-700">
                {stats.due} agendamento{stats.due > 1 ? 's' : ''} pendente{stats.due > 1 ? 's' : ''} de execução
              </p>
              <p className="text-xs text-amber-600">
                O worker de execução processará esses agendamentos automaticamente via Edge Function.
              </p>
            </div>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="Total de agendamentos"  value={stats.total}     icon={Clock}       color="bg-blue-50 text-blue-600"     />
          <StatCard label="Envio único"             value={stats.once}      icon={CalendarClock}color="bg-sky-50 text-sky-600"       />
          <StatCard label="Recorrentes"             value={stats.recurring} icon={RefreshCw}   color="bg-violet-50 text-violet-600" />
          <StatCard label="Por evento"              value={stats.event}     icon={Zap}         color="bg-amber-50 text-amber-600"   />
        </div>

        {/* Next execution info */}
        {nextDue && (
          <div className="bg-white rounded-2xl border border-gray-100 px-5 py-4 flex items-center gap-4">
            <div className="w-9 h-9 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            </div>
            <div>
              <p className="text-xs text-gray-400">Próxima execução agendada</p>
              <p className="text-sm font-semibold text-gray-800">{nextDue.campaign_name}</p>
            </div>
            <div className="ml-auto text-right">
              <p className="text-xs text-gray-400">Data/hora</p>
              <p className="text-sm font-mono font-medium text-gray-700">
                {new Date(nextDue.next_run_at!).toLocaleString('pt-BR')}
              </p>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex items-center gap-1 bg-white rounded-xl border border-gray-100 p-1 w-fit flex-wrap">
          {TYPE_TABS.map((tab) => {
            const count =
              tab.value === 'all'             ? schedules.length
              : tab.value === 'inactive'       ? schedules.filter((s) => !s.is_active).length
              : schedules.filter((s) => s.schedule_type === tab.value && s.is_active).length;
            return (
              <button
                key={tab.value}
                onClick={() => setActiveFilter(tab.value)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  activeFilter === tab.value
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                {tab.label}
                {count > 0 && (
                  <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${
                    activeFilter === tab.value
                      ? 'bg-white/20 text-white'
                      : 'bg-gray-100 text-gray-500'
                  }`}>
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Table */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-gray-400" />
            <h2 className="text-sm font-semibold text-gray-700">Agendamentos</h2>
            {loading && <Loader2 className="w-3.5 h-3.5 text-gray-300 animate-spin ml-1" />}
            <span className="text-xs text-gray-400 ml-1">
              {filtered.length} resultado{filtered.length !== 1 ? 's' : ''}
            </span>
          </div>
          <CampaignSchedulesTable
            schedules={filtered}
            loading={loading}
            onRefresh={load}
          />
        </div>
      </div>

      {showCreate && (
        <ScheduleCreateModal
          onClose={() => setShowCreate(false)}
          onCreated={async () => { setShowCreate(false); await load(); }}
        />
      )}
    </div>
  );
}
