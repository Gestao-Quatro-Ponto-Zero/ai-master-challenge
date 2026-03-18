import { AlertCircle, Wifi, WifiOff, Zap, Coffee } from 'lucide-react';
import type { OperatorMetric } from '../../services/monitoringService';
import type { OperatorStatus } from '../../types';

interface Props {
  operators: OperatorMetric[];
}

const STATUS_CFG: Record<string, {
  dot:          string;
  text:         string;
  badgeBg:      string;
  badgeBorder:  string;
  icon:         React.ComponentType<{ className?: string }>;
  label:        string;
}> = {
  online:  { dot: 'bg-emerald-400', text: 'text-emerald-300', badgeBg: 'bg-emerald-500/10', badgeBorder: 'border-emerald-500/20', icon: Wifi,    label: 'Online'  },
  busy:    { dot: 'bg-rose-400',    text: 'text-rose-300',    badgeBg: 'bg-rose-500/10',    badgeBorder: 'border-rose-500/20',    icon: Zap,     label: 'Busy'    },
  away:    { dot: 'bg-amber-400',   text: 'text-amber-300',   badgeBg: 'bg-amber-500/10',   badgeBorder: 'border-amber-500/20',   icon: Coffee,  label: 'Away'    },
  offline: { dot: 'bg-slate-600',   text: 'text-slate-500',   badgeBg: 'bg-slate-800/50',   badgeBorder: 'border-slate-700/30',   icon: WifiOff, label: 'Offline' },
};

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const secs = Math.floor(diff / 1000);
  if (secs < 60)  return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  return `${Math.floor(mins / 60)}h ago`;
}

function Avatar({ name, email }: { name: string; email: string }) {
  const label    = name || email;
  const initials = label.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase() || '?';
  const colors   = ['bg-blue-600', 'bg-emerald-600', 'bg-amber-600', 'bg-rose-600', 'bg-slate-600'];
  const color    = colors[(initials.charCodeAt(0) ?? 0) % colors.length];
  return (
    <div className={`w-7 h-7 rounded-full ${color} flex items-center justify-center shrink-0`}>
      <span className="text-white text-xs font-semibold">{initials}</span>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CFG[status] ?? STATUS_CFG.offline;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-lg border text-xs font-medium ${cfg.badgeBg} ${cfg.badgeBorder} ${cfg.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${cfg.dot}`} />
      {cfg.label}
    </span>
  );
}

function LoadBar({ active, max }: { active: number; max: number }) {
  const pct   = max > 0 ? Math.min(100, Math.round((active / max) * 100)) : 0;
  const color = pct >= 90 ? 'bg-rose-500' : pct >= 60 ? 'bg-amber-400' : 'bg-emerald-400';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-700/60 rounded-full overflow-hidden min-w-[60px]">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-500 tabular-nums w-10 text-right">{active}/{max}</span>
    </div>
  );
}

export default function OperatorMonitorPanel({ operators }: Props) {
  if (operators.length === 0) {
    return (
      <div className="flex items-center gap-2.5 text-xs text-slate-600 bg-slate-900/40 border border-white/5 rounded-2xl px-5 py-5">
        <AlertCircle className="w-4 h-4 text-slate-700" />
        No operators found. Create operators in the Operators settings.
      </div>
    );
  }

  const statusOrder: Record<string, number> = { online: 0, busy: 1, away: 2, offline: 3 };
  const sorted = [...operators].sort((a, b) =>
    (statusOrder[a.status] ?? 4) - (statusOrder[b.status] ?? 4),
  );

  const counts: Record<string, number> = { online: 0, busy: 0, away: 0, offline: 0 };
  operators.forEach((op) => { counts[op.status] = (counts[op.status] ?? 0) + 1; });

  return (
    <div className="space-y-3">
      {/* Status summary */}
      <div className="grid grid-cols-4 gap-2">
        {(['online', 'busy', 'away', 'offline'] as OperatorStatus[]).map((s) => {
          const cfg  = STATUS_CFG[s];
          const Icon = cfg.icon;
          return (
            <div key={s} className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl border ${cfg.badgeBg} ${cfg.badgeBorder}`}>
              <Icon className={`w-3.5 h-3.5 shrink-0 ${cfg.text}`} />
              <div>
                <p className={`text-base font-bold tabular-nums ${cfg.text}`}>{counts[s] ?? 0}</p>
                <p className={`text-xs ${cfg.text} opacity-70`}>{cfg.label}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Operator table */}
      <div className="bg-slate-900/60 border border-white/6 rounded-2xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/5">
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-600">Operator</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-600">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-600">Last Active</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-600 w-44">Ticket Load</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((op) => (
              <tr key={op.id} className="border-b border-white/4 last:border-0 hover:bg-white/2 transition-colors">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2.5">
                    <Avatar name={op.full_name} email={op.email} />
                    <div className="min-w-0">
                      <p className="text-xs font-medium text-white truncate">{op.full_name || op.email}</p>
                      {op.full_name && <p className="text-xs text-slate-600 truncate">{op.email}</p>}
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={op.status} />
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs text-slate-600">
                    {op.last_seen ? timeAgo(op.last_seen) : '—'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <LoadBar active={op.active_tickets} max={op.max_tickets} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
