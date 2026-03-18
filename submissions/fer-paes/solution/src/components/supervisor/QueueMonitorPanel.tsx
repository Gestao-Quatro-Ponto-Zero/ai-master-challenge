import { useState } from 'react';
import {
  Play, Loader2, CheckCircle, AlertCircle,
  TrendingDown, Shuffle, Brain, User as UserIcon, ListOrdered,
} from 'lucide-react';
import { triggerDistribution, type DistributionResult } from '../../services/ticketAssignmentService';
import type { QueueMetric } from '../../services/monitoringService';

interface Props {
  queues:   QueueMetric[];
  onRefresh: () => void;
}

const STRATEGY_META: Record<string, { label: string; icon: React.ComponentType<{ className?: string }>; className: string }> = {
  least_loaded: { label: 'Least Loaded', icon: TrendingDown, className: 'bg-emerald-900/50 text-emerald-300 border-emerald-500/20' },
  round_robin:  { label: 'Round Robin',  icon: Shuffle,      className: 'bg-blue-900/50 text-blue-300 border-blue-500/20'         },
  skill_based:  { label: 'Skill Based',  icon: Brain,        className: 'bg-amber-900/50 text-amber-300 border-amber-500/20'       },
  manual:       { label: 'Manual',       icon: UserIcon,     className: 'bg-slate-700/60 text-slate-400 border-slate-600/30'       },
};

function StrategyBadge({ strategy }: { strategy: string }) {
  const meta = STRATEGY_META[strategy] ?? STRATEGY_META.manual;
  const Icon = meta.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-medium ${meta.className}`}>
      <Icon className="w-3 h-3" />
      {meta.label}
    </span>
  );
}

export default function QueueMonitorPanel({ queues, onRefresh }: Props) {
  const [running, setRunning] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, DistributionResult>>({});

  async function handleDistribute(queueId: string) {
    setRunning(queueId);
    try {
      const result = await triggerDistribution(queueId);
      setResults((prev) => ({ ...prev, [queueId]: result }));
      onRefresh();
    } catch { } finally { setRunning(null); }
  }

  if (queues.length === 0) {
    return (
      <div className="flex items-center gap-2.5 text-xs text-slate-600 bg-slate-900/40 border border-white/5 rounded-2xl px-5 py-5">
        <AlertCircle className="w-4 h-4 text-slate-700" />
        No queues configured. Create queues in the Queues settings.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {/* Summary row */}
      <div className="flex items-center gap-4 px-1 mb-3">
        <div className="flex items-center gap-1.5">
          <ListOrdered className="w-3.5 h-3.5 text-slate-600" />
          <span className="text-xs text-slate-600">{queues.length} queues total</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-amber-400 font-medium">{queues.reduce((s, q) => s + q.waiting_tickets, 0)}</span>
          <span className="text-xs text-slate-600">tickets waiting</span>
        </div>
      </div>

      <div className="bg-slate-900/60 border border-white/6 rounded-2xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/5">
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-600">Queue</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-600">Strategy</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-slate-600">Waiting</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-slate-600">Operators</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-slate-600">Action</th>
            </tr>
          </thead>
          <tbody>
            {queues.map((q) => {
              const isRunning = running === q.id;
              const res       = results[q.id];
              const isManual  = q.strategy === 'manual';

              return (
                <>
                  <tr key={q.id} className="border-b border-white/4 last:border-0 hover:bg-white/2 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${q.is_active ? 'bg-emerald-400' : 'bg-slate-600'}`} />
                        <span className="text-xs font-medium text-white capitalize">
                          {q.name.replace(/_/g, ' ')}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <StrategyBadge strategy={q.strategy} />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-sm font-semibold tabular-nums ${q.waiting_tickets > 0 ? 'text-amber-300' : 'text-slate-600'}`}>
                        {q.waiting_tickets}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-xs text-slate-400">{q.assigned_operators}</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {!isManual ? (
                        <button
                          onClick={() => handleDistribute(q.id)}
                          disabled={isRunning || q.waiting_tickets === 0}
                          className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-medium transition-colors ${
                            isRunning
                              ? 'bg-blue-600/20 text-blue-400 cursor-default'
                              : q.waiting_tickets === 0
                                ? 'bg-slate-800 text-slate-600 cursor-not-allowed'
                                : 'bg-blue-600 text-white hover:bg-blue-500'
                          }`}
                        >
                          {isRunning
                            ? <Loader2 className="w-3 h-3 animate-spin" />
                            : <Play className="w-3 h-3" />
                          }
                          {isRunning ? 'Running…' : 'Distribute'}
                        </button>
                      ) : (
                        <span className="text-xs text-slate-700">Manual only</span>
                      )}
                    </td>
                  </tr>
                  {res && (
                    <tr key={`${q.id}-res`} className="bg-slate-900/30">
                      <td colSpan={5} className="px-4 py-2">
                        <div className={`flex items-center gap-3 text-xs ${res.errors.length > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                          {res.errors.length === 0
                            ? <CheckCircle className="w-3.5 h-3.5 shrink-0" />
                            : <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                          }
                          {res.assigned} assigned · {res.skipped} skipped
                          {res.errors.length > 0 && ` · ${res.errors.length} error${res.errors.length > 1 ? 's' : ''}`}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
