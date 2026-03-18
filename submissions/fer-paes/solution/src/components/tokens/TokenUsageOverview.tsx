import { Zap, TrendingUp, Hash, Activity } from 'lucide-react';
import type { TokenUsageByDay } from '../../services/tokenUsageTrackerService';

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

interface Props {
  daily: TokenUsageByDay[];
  totalRequests: number;
}

export default function TokenUsageOverview({ daily, totalRequests }: Props) {
  const today = new Date().toISOString().slice(0, 10);
  const todayRow = daily.find((d) => d.day === today);

  const monthTotal = daily.reduce((s, d) => s + Number(d.total_tokens), 0);
  const monthInput = daily.reduce((s, d) => s + Number(d.input_tokens), 0);
  const monthOutput = daily.reduce((s, d) => s + Number(d.output_tokens), 0);
  const avgPerRequest = totalRequests > 0 ? Math.round(monthTotal / totalRequests) : 0;

  const cards = [
    {
      icon: Zap,
      label: 'Tokens Today',
      value: formatTokens(todayRow ? Number(todayRow.total_tokens) : 0),
      sub: todayRow
        ? `${formatTokens(Number(todayRow.input_tokens))} in · ${formatTokens(Number(todayRow.output_tokens))} out`
        : 'No data yet',
      color: 'blue',
    },
    {
      icon: TrendingUp,
      label: 'Tokens This Month',
      value: formatTokens(monthTotal),
      sub: `${formatTokens(monthInput)} in · ${formatTokens(monthOutput)} out`,
      color: 'emerald',
    },
    {
      icon: Hash,
      label: 'Avg per Request',
      value: formatTokens(avgPerRequest),
      sub: `Based on ${totalRequests.toLocaleString()} requests`,
      color: 'amber',
    },
    {
      icon: Activity,
      label: 'Active Days',
      value: String(daily.filter((d) => d.total_tokens > 0).length),
      sub: `Out of last 30 days`,
      color: 'cyan',
    },
  ];

  const colorMap: Record<string, { bg: string; icon: string; value: string }> = {
    blue:   { bg: 'bg-blue-500/10',   icon: 'text-blue-400',   value: 'text-blue-300'   },
    emerald:{ bg: 'bg-emerald-500/10', icon: 'text-emerald-400', value: 'text-emerald-300' },
    amber:  { bg: 'bg-amber-500/10',  icon: 'text-amber-400',  value: 'text-amber-300'  },
    cyan:   { bg: 'bg-cyan-500/10',   icon: 'text-cyan-400',   value: 'text-cyan-300'   },
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
