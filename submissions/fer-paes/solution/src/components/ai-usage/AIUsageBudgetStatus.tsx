import { Wallet, ShieldOff, AlertTriangle, CheckCircle, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { LLMBudget } from '../../services/budgetManagerService';
import { spendPercent, tokenPercent, formatUSD, formatTokens, isExhausted, isOverAlert } from '../../services/budgetManagerService';

interface Props {
  budget: LLMBudget | null;
}

export default function AIUsageBudgetStatus({ budget }: Props) {
  if (!budget) {
    return (
      <div className="bg-slate-900 border border-white/5 rounded-xl px-5 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-slate-700 flex items-center justify-center">
            <Wallet className="w-4 h-4 text-slate-500" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-400">Nenhum orçamento ativo</p>
            <p className="text-xs text-slate-600 mt-0.5">Requisições LLM sem limite de gasto</p>
          </div>
        </div>
        <Link to="/llm-budgets" className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-white transition-colors">
          Configurar <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    );
  }

  const sp         = spendPercent(budget);
  const tp         = tokenPercent(budget);
  const exhausted  = isExhausted(budget);
  const overAlert  = isOverAlert(budget);
  const remaining  = budget.monthly_budget != null ? Math.max(budget.monthly_budget - budget.current_spend, 0) : null;

  const StatusIcon = exhausted ? ShieldOff : overAlert ? AlertTriangle : CheckCircle;
  const statusColor = exhausted ? 'text-red-400' : overAlert ? 'text-amber-400' : 'text-emerald-400';
  const barColor    = exhausted ? 'bg-red-500'   : overAlert ? 'bg-amber-500'   : 'bg-emerald-500';

  return (
    <div className={`bg-slate-900 border rounded-xl px-5 py-4 ${exhausted ? 'border-red-500/30' : overAlert ? 'border-amber-500/20' : 'border-white/5'}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Wallet className="w-4 h-4 text-slate-400" />
          <p className="text-sm font-semibold text-white">{budget.name}</p>
        </div>
        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-1 text-xs ${statusColor}`}>
            <StatusIcon className="w-3.5 h-3.5" />
            <span>{exhausted ? 'Esgotado — requisições bloqueadas' : overAlert ? 'Limite de alerta atingido' : 'Dentro dos limites'}</span>
          </div>
          <Link to="/llm-budgets" className="flex items-center gap-1 text-xs text-slate-500 hover:text-white transition-colors">
            Gerenciar <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {budget.monthly_budget != null && (
          <div>
            <div className="flex items-baseline justify-between mb-1.5">
              <span className="text-xs text-slate-500">Custo</span>
              <span className="text-xs text-slate-400 tabular-nums">
                {formatUSD(budget.current_spend)} / {formatUSD(budget.monthly_budget)}
                {remaining != null && <span className="text-slate-600 ml-1">({formatUSD(remaining)} restante)</span>}
              </span>
            </div>
            <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
              <div className={`h-full rounded-full transition-all ${barColor}`} style={{ width: `${Math.min(sp, 100)}%` }} />
            </div>
            <p className="text-[10px] text-slate-600 mt-1">{sp.toFixed(1)}% utilizado</p>
          </div>
        )}

        {budget.token_limit != null && (
          <div>
            <div className="flex items-baseline justify-between mb-1.5">
              <span className="text-xs text-slate-500">Tokens usados</span>
              <span className="text-xs text-slate-400 tabular-nums">
                {formatTokens(budget.current_tokens)} / {formatTokens(budget.token_limit)}
              </span>
            </div>
            <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${tp >= 100 ? 'bg-red-500' : tp >= budget.alert_threshold * 100 ? 'bg-amber-500' : 'bg-blue-500'}`}
                style={{ width: `${Math.min(tp, 100)}%` }}
              />
            </div>
            <p className="text-[10px] text-slate-600 mt-1">{tp.toFixed(1)}% utilizado</p>
          </div>
        )}
      </div>
    </div>
  );
}
