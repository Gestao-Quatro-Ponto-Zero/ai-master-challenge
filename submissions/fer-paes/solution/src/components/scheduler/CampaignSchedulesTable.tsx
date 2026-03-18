import { useState } from 'react';
import { Loader2, Clock, CalendarClock, RefreshCw, Zap, Trash2, PowerOff, Power } from 'lucide-react';
import type { CampaignSchedule, ScheduleType } from '../../services/campaignSchedulerService';
import {
  SCHEDULE_TYPE_META, EVENT_TYPES, parseCronHuman,
  disableSchedule, enableSchedule, deleteSchedule,
} from '../../services/campaignSchedulerService';
import ScheduleStatusBadge from './ScheduleStatusBadge';

const TYPE_ICONS: Record<ScheduleType, React.ComponentType<{ className?: string }>> = {
  once:            CalendarClock,
  recurring:       RefreshCw,
  event_triggered: Zap,
};

function eventLabel(val: string | null) {
  if (!val) return '—';
  return EVENT_TYPES.find((e) => e.value === val)?.label ?? val;
}

function ScheduleRow({
  schedule,
  onRefresh,
}: {
  schedule:  CampaignSchedule;
  onRefresh: () => void;
}) {
  const [acting, setActing] = useState<string | null>(null);
  const meta  = SCHEDULE_TYPE_META[schedule.schedule_type];
  const Icon  = TYPE_ICONS[schedule.schedule_type];

  async function handleToggle(e: React.MouseEvent) {
    e.stopPropagation();
    setActing('toggle');
    try {
      if (schedule.is_active) await disableSchedule(schedule.id);
      else                    await enableSchedule(schedule.id);
      onRefresh();
    } catch { /* noop */ }
    finally { setActing(null); }
  }

  async function handleDelete(e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm('Excluir este agendamento?')) return;
    setActing('delete');
    try { await deleteSchedule(schedule.id); onRefresh(); }
    catch { /* noop */ }
    finally { setActing(null); }
  }

  function scheduleDetail() {
    if (schedule.schedule_type === 'once') {
      return schedule.run_at
        ? new Date(schedule.run_at).toLocaleString('pt-BR')
        : '—';
    }
    if (schedule.schedule_type === 'recurring') {
      return schedule.cron_expression
        ? parseCronHuman(schedule.cron_expression)
        : '—';
    }
    return eventLabel(schedule.event_type);
  }

  return (
    <tr className="hover:bg-gray-50/50 transition-colors">
      <td className="px-5 py-3.5">
        <div>
          <p className="text-sm font-semibold text-gray-800">{schedule.campaign_name}</p>
          <p className="text-xs text-gray-400 capitalize">{schedule.campaign_channel}</p>
        </div>
      </td>
      <td className="px-5 py-3.5">
        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border ${meta.color} ${meta.bg} ${meta.border}`}>
          <Icon className="w-3 h-3" />
          {meta.label}
        </span>
      </td>
      <td className="px-5 py-3.5 text-sm text-gray-600 max-w-[200px]">
        <p className="truncate">{scheduleDetail()}</p>
        {schedule.schedule_type === 'recurring' && schedule.cron_expression && (
          <p className="text-xs font-mono text-gray-400">{schedule.cron_expression}</p>
        )}
      </td>
      <td className="px-5 py-3.5 text-xs text-gray-400 whitespace-nowrap tabular-nums">
        {schedule.next_run_at
          ? new Date(schedule.next_run_at).toLocaleString('pt-BR', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' })
          : '—'}
      </td>
      <td className="px-5 py-3.5 text-xs text-gray-400 whitespace-nowrap tabular-nums">
        {schedule.last_run_at
          ? new Date(schedule.last_run_at).toLocaleString('pt-BR', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' })
          : '—'}
      </td>
      <td className="px-5 py-3.5">
        <div className="flex items-center gap-2">
          <ScheduleStatusBadge isActive={schedule.is_active} />
          <span className="text-xs text-gray-400 tabular-nums">{schedule.execution_count}x</span>
        </div>
      </td>
      <td className="px-5 py-3.5">
        <div className="flex items-center gap-1">
          <button
            onClick={handleToggle}
            disabled={acting !== null}
            title={schedule.is_active ? 'Desativar' : 'Ativar'}
            className={`w-7 h-7 flex items-center justify-center rounded-lg disabled:opacity-40 transition-colors ${
              schedule.is_active
                ? 'text-gray-400 hover:text-amber-600 hover:bg-amber-50'
                : 'text-gray-400 hover:text-emerald-600 hover:bg-emerald-50'
            }`}
          >
            {acting === 'toggle'
              ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
              : schedule.is_active
                ? <PowerOff className="w-3.5 h-3.5" />
                : <Power className="w-3.5 h-3.5" />
            }
          </button>
          <button
            onClick={handleDelete}
            disabled={acting !== null}
            title="Excluir agendamento"
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 disabled:opacity-40 transition-colors"
          >
            {acting === 'delete'
              ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
              : <Trash2 className="w-3.5 h-3.5" />
            }
          </button>
        </div>
      </td>
    </tr>
  );
}

interface Props {
  schedules: CampaignSchedule[];
  loading:   boolean;
  onRefresh: () => void;
}

export default function CampaignSchedulesTable({ schedules, loading, onRefresh }: Props) {
  if (loading && schedules.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 flex items-center justify-center py-20">
        <Loader2 className="w-5 h-5 text-gray-300 animate-spin" />
      </div>
    );
  }

  if (!loading && schedules.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 flex flex-col items-center justify-center py-20 gap-3">
        <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center">
          <Clock className="w-6 h-6 text-gray-300" />
        </div>
        <p className="text-sm text-gray-400">Nenhum agendamento criado</p>
        <p className="text-xs text-gray-300">Agende campanhas para execução automática</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-100">
            {['Campanha', 'Tipo', 'Configuração', 'Próxima Exec.', 'Última Exec.', 'Status', 'Ações'].map((h) => (
              <th key={h} className="text-left px-5 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {schedules.map((s) => (
            <ScheduleRow key={s.id} schedule={s} onRefresh={onRefresh} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
