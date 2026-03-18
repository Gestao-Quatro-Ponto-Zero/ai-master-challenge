import { Hash, Zap, DollarSign, Clock, AlertCircle, GitFork } from 'lucide-react';
import type { AIUsageOverview } from '../../services/aiUsageAnalyticsService';
import { formatTokens, formatUSD, formatLatency } from '../../services/aiUsageAnalyticsService';

interface Props {
  overview: AIUsageOverview | null;
  loading:  boolean;
}

interface CardDef {
  label:     string;
  value:     string;
  sub:       string;
  icon:      React.ElementType;
  iconBg:    string;
  iconColor: string;
}

function Skeleton() {
  return <div className="h-7 w-24 rounded bg-slate-800 animate-pulse" />;
}

function SubSkeleton() {
  return <div className="h-3.5 w-20 rounded bg-slate-800 animate-pulse mt-1" />;
}

export default function AIUsageOverviewCards({ overview, loading }: Props) {
  const cards: CardDef[] = overview
    ? [
        {
          label:      'Total de Requisições',
          value:      overview.total_requests.toLocaleString('pt-BR'),
          sub:        `${overview.error_count.toLocaleString('pt-BR')} erros · ${overview.fallback_count.toLocaleString('pt-BR')} fallbacks`,
          icon:       Hash,
          iconBg:     'bg-blue-500/20',
          iconColor:  'text-blue-400',
        },
        {
          label:      'Tokens Consumidos',
          value:      formatTokens(overview.total_tokens),
          sub:        `${overview.total_tokens.toLocaleString('pt-BR')} tokens no total`,
          icon:       Zap,
          iconBg:     'bg-amber-500/20',
          iconColor:  'text-amber-400',
        },
        {
          label:      'Custo Total',
          value:      formatUSD(overview.total_cost),
          sub:        overview.total_requests > 0 ? `média ${formatUSD(overview.total_cost / overview.total_requests)} / req` : 'Sem requisições',
          icon:       DollarSign,
          iconBg:     'bg-emerald-500/20',
          iconColor:  'text-emerald-400',
        },
        {
          label:      'Latência Média',
          value:      formatLatency(overview.avg_latency_ms),
          sub:        overview.avg_latency_ms < 1000 ? 'Dentro do normal' : overview.avg_latency_ms < 3000 ? 'Levemente elevada' : 'Latência alta detectada',
          icon:       Clock,
          iconBg:     overview.avg_latency_ms < 3000 ? 'bg-slate-700' : 'bg-amber-500/20',
          iconColor:  overview.avg_latency_ms < 3000 ? 'text-slate-500' : 'text-amber-400',
        },
        {
          label:      'Taxa de Erros',
          value:      overview.total_requests > 0
            ? `${((overview.error_count / overview.total_requests) * 100).toFixed(1)}%`
            : '0%',
          sub:        `${overview.error_count.toLocaleString('pt-BR')} requisição${overview.error_count !== 1 ? 'ões' : ''} com falha`,
          icon:       AlertCircle,
          iconBg:     overview.error_count > 0 ? 'bg-red-500/20' : 'bg-slate-700',
          iconColor:  overview.error_count > 0 ? 'text-red-400' : 'text-slate-600',
        },
        {
          label:      'Taxa de Fallback',
          value:      overview.total_requests > 0
            ? `${((overview.fallback_count / overview.total_requests) * 100).toFixed(1)}%`
            : '0%',
          sub:        `${overview.fallback_count.toLocaleString('pt-BR')} fallback${overview.fallback_count !== 1 ? 's' : ''}`,
          icon:       GitFork,
          iconBg:     'bg-slate-700',
          iconColor:  'text-slate-500',
        },
      ]
    : Array(6).fill(null);

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
      {cards.map((card, i) => {
        const Icon = card?.icon;
        return (
          <div key={i} className="bg-slate-900 border border-white/5 rounded-xl px-5 py-4">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs text-slate-500 truncate pr-1">{loading ? <span className="invisible">placeholder</span> : card?.label ?? ''}</p>
              {!loading && Icon && (
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${card!.iconBg}`}>
                  <Icon className={`w-3.5 h-3.5 ${card!.iconColor}`} />
                </div>
              )}
            </div>
            {loading || !card ? (
              <>
                <Skeleton />
                <SubSkeleton />
              </>
            ) : (
              <>
                <p className="text-xl font-bold text-white tabular-nums">{card.value}</p>
                <p className="text-[11px] text-slate-600 mt-0.5 leading-tight">{card.sub}</p>
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}
