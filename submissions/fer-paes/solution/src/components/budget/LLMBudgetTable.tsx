import { Pencil, Trash2, RotateCcw, CheckCircle, XCircle, AlertTriangle, ShieldOff } from 'lucide-react';
import type { LLMBudget } from '../../services/budgetManagerService';
import { spendPercent, tokenPercent, formatUSD, formatTokens, isExhausted, isOverAlert } from '../../services/budgetManagerService';

interface Props {
  budgets:  LLMBudget[];
  onEdit:   (b: LLMBudget) => void;
  onDelete: (b: LLMBudget) => void;
  onReset:  (b: LLMBudget) => void;
}

function MiniBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="w-full h-1 rounded-full bg-slate-800 overflow-hidden">
      <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(value, 100)}%` }} />
    </div>
  );
}

function statusBadge(budget: LLMBudget) {
  if (!budget.is_active) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-slate-700 text-slate-400 border border-white/10">
        <XCircle className="w-3 h-3" /> Inactive
      </span>
    );
  }
  const now = new Date();
  const start = new Date(budget.period_start);
  const end   = new Date(budget.period_end);
  if (now < start) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20">
        Upcoming
      </span>
    );
  }
  if (now > end) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-slate-700 text-slate-400 border border-white/10">
        Expired
      </span>
    );
  }
  if (isExhausted(budget)) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-red-500/10 text-red-400 border border-red-500/20">
        <ShieldOff className="w-3 h-3" /> Exhausted
      </span>
    );
  }
  if (isOverAlert(budget)) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20">
        <AlertTriangle className="w-3 h-3" /> Alert
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
      <CheckCircle className="w-3 h-3" /> Active
    </span>
  );
}

export default function LLMBudgetTable({ budgets, onEdit, onDelete, onReset }: Props) {
  if (budgets.length === 0) {
    return (
      <div className="py-16 text-center text-slate-600 text-sm">
        No budgets configured yet. Create your first budget to start controlling LLM spend.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-white/5">
            {['Name / Scope', 'Period', 'Cost Budget', 'Token Limit', 'Status', ''].map((h) => (
              <th key={h} className="text-left px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {budgets.map((b) => {
            const sp = spendPercent(b);
            const tp = tokenPercent(b);
            return (
              <tr key={b.id} className="hover:bg-white/[0.02] transition-colors">
                <td className="px-5 py-4">
                  <p className="text-white text-sm font-medium">{b.name}</p>
                  <p className="text-slate-600 text-xs mt-0.5">
                    {b.organization_id ? `Org: ${b.organization_id.slice(0, 8)}…` : 'Global'}
                  </p>
                </td>
                <td className="px-5 py-4">
                  <p className="text-slate-400 text-xs">
                    {new Date(b.period_start).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    {' — '}
                    {new Date(b.period_end).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </p>
                </td>
                <td className="px-5 py-4 min-w-[140px]">
                  {b.monthly_budget != null ? (
                    <div>
                      <div className="flex items-baseline justify-between mb-1">
                        <span className="text-white text-sm tabular-nums">{formatUSD(b.current_spend)}</span>
                        <span className="text-slate-600 text-xs">/ {formatUSD(b.monthly_budget)}</span>
                      </div>
                      <MiniBar
                        value={sp}
                        color={sp >= 100 ? 'bg-red-500' : sp >= b.alert_threshold * 100 ? 'bg-amber-500' : 'bg-emerald-500'}
                      />
                      <p className="text-[10px] text-slate-600 mt-0.5">{sp.toFixed(1)}% used</p>
                    </div>
                  ) : (
                    <span className="text-slate-600 text-xs">Unlimited</span>
                  )}
                </td>
                <td className="px-5 py-4 min-w-[140px]">
                  {b.token_limit != null ? (
                    <div>
                      <div className="flex items-baseline justify-between mb-1">
                        <span className="text-white text-sm tabular-nums">{formatTokens(b.current_tokens)}</span>
                        <span className="text-slate-600 text-xs">/ {formatTokens(b.token_limit)}</span>
                      </div>
                      <MiniBar
                        value={tp}
                        color={tp >= 100 ? 'bg-red-500' : tp >= b.alert_threshold * 100 ? 'bg-amber-500' : 'bg-blue-500'}
                      />
                      <p className="text-[10px] text-slate-600 mt-0.5">{tp.toFixed(1)}% used</p>
                    </div>
                  ) : (
                    <span className="text-slate-600 text-xs">Unlimited</span>
                  )}
                </td>
                <td className="px-5 py-4">{statusBadge(b)}</td>
                <td className="px-5 py-4">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => onEdit(b)}
                      title="Edit"
                      className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-colors"
                    >
                      <Pencil className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => onReset(b)}
                      title="Reset usage counters"
                      className="p-1.5 rounded-lg text-slate-500 hover:text-amber-400 hover:bg-white/5 transition-colors"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => onDelete(b)}
                      title="Delete"
                      className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-white/5 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
