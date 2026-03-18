import { X, Ticket as TicketIcon, CheckCircle2, Clock, Timer, TrendingUp, Star } from 'lucide-react';
import type { OperatorMetricRow } from '../../services/metricsService';
import { formatDuration } from '../../services/metricsService';

interface Props {
  operator: OperatorMetricRow;
  onClose:  () => void;
}

interface StatItem {
  label:   string;
  value:   string;
  icon:    React.ComponentType<{ className?: string }>;
  color:   string;
  detail?: string;
}

function Avatar({ name, email }: { name: string; email: string }) {
  const label    = name || email;
  const initials = label.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase() || '?';
  const colors   = ['bg-blue-600', 'bg-emerald-600', 'bg-amber-600', 'bg-rose-600', 'bg-cyan-600'];
  const color    = colors[(initials.charCodeAt(0) ?? 0) % colors.length];
  return (
    <div className={`w-10 h-10 rounded-full ${color} flex items-center justify-center shrink-0`}>
      <span className="text-white text-sm font-bold">{initials}</span>
    </div>
  );
}

function RatioBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0;
  return (
    <div className="flex items-center gap-2 mt-1.5">
      <div className="flex-1 h-1.5 bg-slate-700/60 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-600 tabular-nums w-8 text-right">{pct}%</span>
    </div>
  );
}

export default function OperatorMetricsCard({ operator: op, onClose }: Props) {
  const responseColor  = op.avg_first_response_time === 0 ? 'text-slate-600'
    : op.avg_first_response_time <= 10  ? 'text-emerald-400'
    : op.avg_first_response_time <= 30  ? 'text-amber-400'
    : 'text-rose-400';

  const resolutionColor = op.avg_resolution_time === 0 ? 'text-slate-600'
    : op.avg_resolution_time <= 120 ? 'text-emerald-400'
    : op.avg_resolution_time <= 480 ? 'text-amber-400'
    : 'text-rose-400';

  const stats: StatItem[] = [
    {
      label:   'Tickets Handled',
      value:   String(op.tickets_handled),
      icon:    TicketIcon,
      color:   'text-blue-400',
      detail:  op.tickets_handled === 0 ? 'No tickets in period' : `in selected period`,
    },
    {
      label:   'Tickets Resolved',
      value:   String(op.tickets_resolved),
      icon:    CheckCircle2,
      color:   'text-emerald-400',
      detail:  `${op.resolution_rate}% resolution rate`,
    },
    {
      label:   'Avg First Response',
      value:   formatDuration(op.avg_first_response_time),
      icon:    Clock,
      color:   responseColor,
      detail:  op.avg_first_response_time === 0 ? 'No data' : op.avg_first_response_time <= 10 ? 'Excellent' : op.avg_first_response_time <= 30 ? 'Good' : 'Needs improvement',
    },
    {
      label:   'Avg Resolution Time',
      value:   formatDuration(op.avg_resolution_time),
      icon:    Timer,
      color:   resolutionColor,
      detail:  op.avg_resolution_time === 0 ? 'No data' : op.avg_resolution_time <= 120 ? 'Excellent' : op.avg_resolution_time <= 480 ? 'Good' : 'Needs improvement',
    },
    {
      label:   'Resolution Rate',
      value:   `${op.resolution_rate}%`,
      icon:    TrendingUp,
      color:   op.resolution_rate >= 80 ? 'text-emerald-400' : op.resolution_rate >= 50 ? 'text-amber-400' : 'text-rose-400',
    },
    {
      label:   'CSAT Score',
      value:   op.csat_score != null ? op.csat_score.toFixed(1) : '—',
      icon:    Star,
      color:   op.csat_score == null ? 'text-slate-600' : op.csat_score >= 4 ? 'text-emerald-400' : op.csat_score >= 3 ? 'text-amber-400' : 'text-rose-400',
      detail:  op.csat_score == null ? 'Not yet available' : 'out of 5.0',
    },
  ];

  return (
    <div className="bg-slate-900 border border-white/8 rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <Avatar name={op.full_name} email={op.email} />
          <div>
            <p className="text-sm font-semibold text-white">{op.full_name || op.email}</p>
            {op.full_name && <p className="text-xs text-slate-600">{op.email}</p>}
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-600 hover:text-white hover:bg-white/8 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-3 gap-px bg-white/5">
        {stats.map(({ label, value, icon: Icon, color, detail }) => (
          <div key={label} className="bg-slate-900/80 px-4 py-3.5">
            <div className="flex items-center gap-1.5 mb-1.5">
              <Icon className={`w-3.5 h-3.5 shrink-0 ${color}`} />
              <p className="text-xs text-slate-600">{label}</p>
            </div>
            <p className={`text-xl font-bold tabular-nums ${color}`}>{value}</p>
            {detail && <p className="text-xs text-slate-700 mt-0.5">{detail}</p>}
          </div>
        ))}
      </div>

      {/* Resolution rate bar */}
      <div className="px-5 py-4 border-t border-white/5">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs text-slate-600">Resolution Progress</span>
          <span className="text-xs text-slate-500">{op.tickets_resolved} / {op.tickets_handled}</span>
        </div>
        <RatioBar
          value={op.tickets_resolved}
          max={op.tickets_handled}
          color={op.resolution_rate >= 80 ? 'bg-emerald-500' : op.resolution_rate >= 50 ? 'bg-amber-400' : 'bg-rose-500'}
        />
      </div>
    </div>
  );
}
