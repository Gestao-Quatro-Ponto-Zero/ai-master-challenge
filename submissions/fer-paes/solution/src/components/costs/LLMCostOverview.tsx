import { DollarSign, TrendingUp, Hash, Layers } from 'lucide-react';
import type { CostByDay } from '../../services/costCalculatorService';

function formatCost(n: number): string {
  if (n >= 1000) return `$${n.toFixed(2)}`;
  if (n >= 1)    return `$${n.toFixed(4)}`;
  if (n >= 0.001) return `$${n.toFixed(6)}`;
  return `$${n.toFixed(8)}`;
}

interface Props {
  daily: CostByDay[];
  totalRequests: number;
}

export default function LLMCostOverview({ daily, totalRequests }: Props) {
  const today = new Date().toISOString().slice(0, 10);
  const todayRow = daily.find((d) => d.day === today);

  const monthTotal   = daily.reduce((s, d) => s + Number(d.total_cost),  0);
  const monthInput   = daily.reduce((s, d) => s + Number(d.input_cost),  0);
  const monthOutput  = daily.reduce((s, d) => s + Number(d.output_cost), 0);
  const avgPerReq    = totalRequests > 0 ? monthTotal / totalRequests : 0;
  const activeDays   = daily.filter((d) => Number(d.total_cost) > 0).length;

  const cards = [
    {
      icon: DollarSign,
      label: 'Cost Today',
      value: formatCost(todayRow ? Number(todayRow.total_cost) : 0),
      sub: todayRow
        ? `${formatCost(Number(todayRow.input_cost))} in · ${formatCost(Number(todayRow.output_cost))} out`
        : 'No spend yet',
      color: 'emerald',
    },
    {
      icon: TrendingUp,
      label: 'Cost This Month',
      value: formatCost(monthTotal),
      sub: `${formatCost(monthInput)} input · ${formatCost(monthOutput)} output`,
      color: 'blue',
    },
    {
      icon: Hash,
      label: 'Avg per Request',
      value: formatCost(avgPerReq),
      sub: `Across ${totalRequests.toLocaleString()} requests`,
      color: 'amber',
    },
    {
      icon: Layers,
      label: 'Active Days',
      value: String(activeDays),
      sub: 'Days with LLM spend',
      color: 'cyan',
    },
  ];

  const colorMap: Record<string, { bg: string; icon: string; value: string }> = {
    emerald: { bg: 'bg-emerald-500/10', icon: 'text-emerald-400', value: 'text-emerald-300' },
    blue:    { bg: 'bg-blue-500/10',    icon: 'text-blue-400',    value: 'text-blue-300'    },
    amber:   { bg: 'bg-amber-500/10',   icon: 'text-amber-400',   value: 'text-amber-300'   },
    cyan:    { bg: 'bg-cyan-500/10',    icon: 'text-cyan-400',    value: 'text-cyan-300'    },
  };

  return (
    <div className="grid grid-cols-4 gap-4">
      {cards.map((card) => {
        const c = colorMap[card.color];
        const Icon = card.icon;
        return (
          <div key={card.label} className="bg-slate-900 border border-white/5 rounded-xl p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className={`w-8 h-8 rounded-lg ${c.bg} flex items-center justify-center`}>
                <Icon className={`w-4 h-4 ${c.icon}`} />
              </div>
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">{card.label}</span>
            </div>
            <p className={`text-3xl font-bold ${c.value} tabular-nums`}>{card.value}</p>
            <p className="text-xs text-slate-600 mt-1">{card.sub}</p>
          </div>
        );
      })}
    </div>
  );
}
