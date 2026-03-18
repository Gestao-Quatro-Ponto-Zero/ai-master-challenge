import {
  Ticket as TicketIcon, ListOrdered, Wifi, Clock, CheckCircle2, Zap,
} from 'lucide-react';
import type { OverviewMetrics } from '../../services/monitoringService';

interface Props {
  metrics: OverviewMetrics;
  loading: boolean;
}

function formatResponseTime(mins: number): string {
  if (mins === 0) return '—';
  if (mins < 60)  return `${mins}m`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

interface CardConfig {
  label:    string;
  value:    string | number;
  icon:     React.ComponentType<{ className?: string }>;
  color:    string;
  bgColor:  string;
  detail?:  string;
}

export default function OverviewCards({ metrics, loading }: Props) {
  const cards: CardConfig[] = [
    {
      label:   'Active Tickets',
      value:   metrics.active_tickets,
      icon:    TicketIcon,
      color:   'text-blue-400',
      bgColor: 'bg-blue-500/10 border-blue-500/15',
      detail:  `${metrics.queued_tickets} queued`,
    },
    {
      label:   'Queued',
      value:   metrics.queued_tickets,
      icon:    ListOrdered,
      color:   metrics.queued_tickets > 10 ? 'text-rose-400' : 'text-amber-400',
      bgColor: metrics.queued_tickets > 10 ? 'bg-rose-500/10 border-rose-500/15' : 'bg-amber-500/10 border-amber-500/15',
      detail:  metrics.queued_tickets > 10 ? 'High volume' : 'Waiting',
    },
    {
      label:   'Online Operators',
      value:   metrics.online_operators,
      icon:    Wifi,
      color:   'text-emerald-400',
      bgColor: 'bg-emerald-500/10 border-emerald-500/15',
      detail:  `${metrics.busy_operators} busy`,
    },
    {
      label:   'Avg Response Time',
      value:   formatResponseTime(metrics.avg_response_time_minutes),
      icon:    Clock,
      color:   metrics.avg_response_time_minutes > 60 ? 'text-rose-400' : metrics.avg_response_time_minutes > 20 ? 'text-amber-400' : 'text-emerald-400',
      bgColor: 'bg-slate-800/80 border-white/6',
      detail:  'last 24h',
    },
    {
      label:   'Resolved Today',
      value:   metrics.resolved_today,
      icon:    CheckCircle2,
      color:   'text-emerald-400',
      bgColor: 'bg-emerald-500/8 border-emerald-500/12',
    },
    {
      label:   'Busy Operators',
      value:   metrics.busy_operators,
      icon:    Zap,
      color:   metrics.busy_operators > 0 ? 'text-amber-400' : 'text-slate-400',
      bgColor: 'bg-slate-800/60 border-white/5',
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {cards.map(({ label, value, icon: Icon, color, bgColor, detail }) => (
        <div
          key={label}
          className={`flex flex-col justify-between border rounded-2xl px-4 py-3.5 transition-opacity ${bgColor} ${loading ? 'opacity-60' : ''}`}
        >
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs text-slate-300">{label}</p>
            <Icon className={`w-3.5 h-3.5 shrink-0 ${color}`} />
          </div>
          <p className={`text-2xl font-bold tabular-nums ${color}`}>{value}</p>
          {detail && <p className="text-xs text-slate-400 mt-0.5">{detail}</p>}
        </div>
      ))}
    </div>
  );
}
