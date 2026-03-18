import { DollarSign, Zap, AlertTriangle, ShieldOff, TrendingUp } from 'lucide-react';
import type { LLMBudget } from '../../services/budgetManagerService';
import {
  spendPercent, tokenPercent, formatUSD, formatTokens, isExhausted, isOverAlert,
} from '../../services/budgetManagerService';

interface Props {
  budget: LLMBudget | null;
}

function ProgressBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-500 ${color}`}
        style={{ width: `${Math.min(value, 100)}%` }}
      />
    </div>
  );
}

export default function LLMBudgetOverview({ budget }: Props) {
  if (!budget) {
    return (
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {['Monthly Budget', 'Current Spend', 'Remaining', 'Token Usage'].map((label) => (
          <div key={label} className="bg-slate-900 border border-white/5 rounded-xl px-5 py-4">
            <p className="text-xs text-slate-500 mb-1">{label}</p>
            <p className="text-slate-600 text-lg font-semibold">—</p>
          </div>
        ))}
      </div>
    );
  }

  const sp       = spendPercent(budget);
  const tp       = tokenPercent(budget);
  const alert    = isOverAlert(budget);
  const exhausted = isExhausted(budget);
  const remaining = budget.monthly_budget != null
    ? Math.max(budget.monthly_budget - budget.current_spend, 0)
    : null;

  function spendColor() {
    if (exhausted) return 'bg-red-500';
    if (alert)     return 'bg-amber-500';
    return 'bg-emerald-500';
  }

  function tokenColor() {
    if (tp >= 100)                      return 'bg-red-500';
    if (tp >= budget.alert_threshold * 100) return 'bg-amber-500';
    return 'bg-blue-500';
  }

  const cards = [
    {
      label: 'Monthly Budget',
      value: budget.monthly_budget != null ? formatUSD(budget.monthly_budget) : 'Unlimited',
      sub:   `Period: ${new Date(budget.period_start).toLocaleDateString()} – ${new Date(budget.period_end).toLocaleDateString()}`,
      icon:  DollarSign,
      iconBg: 'bg-blue-500/20',
      iconColor: 'text-blue-400',
      bar:   null,
    },
    {
      label: 'Current Spend',
      value: formatUSD(budget.current_spend),
      sub:   budget.monthly_budget != null ? `${sp.toFixed(1)}% of budget used` : 'No cost cap set',
      icon:  TrendingUp,
      iconBg: alert ? 'bg-amber-500/20' : 'bg-emerald-500/20',
      iconColor: alert ? 'text-amber-400' : 'text-emerald-400',
      bar:   budget.monthly_budget != null ? { value: sp, color: spendColor() } : null,
    },
    {
      label: 'Remaining',
      value: remaining != null ? formatUSD(remaining) : 'Unlimited',
      sub:   exhausted ? 'BUDGET EXHAUSTED — requests blocked' : alert ? `Alert threshold reached (${Math.round(budget.alert_threshold * 100)}%)` : 'Within limits',
      icon:  exhausted ? ShieldOff : AlertTriangle,
      iconBg: exhausted ? 'bg-red-500/20' : alert ? 'bg-amber-500/20' : 'bg-slate-700',
      iconColor: exhausted ? 'text-red-400' : alert ? 'text-amber-400' : 'text-slate-500',
      bar:   null,
    },
    {
      label: 'Token Usage',
      value: formatTokens(budget.current_tokens),
      sub:   budget.token_limit != null ? `${tp.toFixed(1)}% of ${formatTokens(budget.token_limit)} limit` : 'No token cap set',
      icon:  Zap,
      iconBg: 'bg-blue-500/20',
      iconColor: 'text-blue-400',
      bar:   budget.token_limit != null ? { value: tp, color: tokenColor() } : null,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.label}
            className={`bg-slate-900 border rounded-xl px-5 py-4 transition-colors
              ${exhausted && card.label === 'Remaining' ? 'border-red-500/30' : alert && card.label === 'Current Spend' ? 'border-amber-500/20' : 'border-white/5'}`}
          >
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs text-slate-500">{card.label}</p>
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${card.iconBg}`}>
                <Icon className={`w-3.5 h-3.5 ${card.iconColor}`} />
              </div>
            </div>
            <p className={`text-xl font-bold tabular-nums mb-1
              ${exhausted && card.label === 'Remaining' ? 'text-red-400' : 'text-white'}`}>
              {card.value}
            </p>
            {card.bar && (
              <div className="mb-2">
                <ProgressBar value={card.bar.value} color={card.bar.color} />
              </div>
            )}
            <p className={`text-[11px] leading-tight
              ${exhausted && card.label === 'Remaining' ? 'text-red-400 font-medium' : alert && card.label === 'Current Spend' ? 'text-amber-400' : 'text-slate-600'}`}>
              {card.sub}
            </p>
          </div>
        );
      })}
    </div>
  );
}
