import { Users, Activity, TrendingUp, Ticket } from 'lucide-react';
import type { CustomerAnalyticsSummary } from '../../services/customerAnalyticsService';

interface Props {
  summary: CustomerAnalyticsSummary | null;
  loading: boolean;
}

interface CardDef {
  label:     string;
  value:     string;
  sub:       string;
  icon:      React.ComponentType<{ className?: string }>;
  iconBg:    string;
  iconColor: string;
}

function Skeleton() {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5 animate-pulse">
      <div className="flex items-start justify-between mb-4">
        <div className="w-10 h-10 rounded-xl bg-gray-100" />
      </div>
      <div className="h-7 bg-gray-100 rounded w-20 mb-2" />
      <div className="h-4 bg-gray-100 rounded w-32" />
    </div>
  );
}

export default function CustomerAnalyticsOverview({ summary, loading }: Props) {
  const cards: CardDef[] = summary
    ? [
        {
          label:     'Total de Clientes',
          value:     summary.total_customers.toLocaleString('pt-BR'),
          sub:       'clientes cadastrados',
          icon:      Users,
          iconBg:    'bg-blue-50',
          iconColor: 'text-blue-600',
        },
        {
          label:     'Clientes Ativos',
          value:     summary.active_customers.toLocaleString('pt-BR'),
          sub:       'interação nos últimos 30 dias',
          icon:      Activity,
          iconBg:    'bg-emerald-50',
          iconColor: 'text-emerald-600',
        },
        {
          label:     'Engajamento Médio',
          value:     summary.avg_engagement_score.toFixed(1),
          sub:       'pontuação média (0–100)',
          icon:      TrendingUp,
          iconBg:    'bg-amber-50',
          iconColor: 'text-amber-600',
        },
        {
          label:     'Tickets por Cliente',
          value:     summary.avg_tickets_per_customer.toFixed(1),
          sub:       'média de tickets por cliente',
          icon:      Ticket,
          iconBg:    'bg-rose-50',
          iconColor: 'text-rose-600',
        },
      ]
    : Array(4).fill(null);

  if (loading && !summary) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {Array(4).fill(null).map((_, i) => <Skeleton key={i} />)}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      {(cards as (CardDef | null)[]).map((card, i) => {
        if (!card) return <Skeleton key={i} />;
        const Icon = card.icon;
        return (
          <div
            key={card.label}
            className="bg-white rounded-2xl border border-gray-100 p-5 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-4">
              <div className={`w-10 h-10 rounded-xl ${card.iconBg} flex items-center justify-center`}>
                <Icon className={`w-5 h-5 ${card.iconColor}`} />
              </div>
            </div>
            <p className="text-2xl font-bold text-gray-900 tabular-nums mb-1">{card.value}</p>
            <p className="text-xs text-gray-400 font-medium">{card.label}</p>
            <p className="text-xs text-gray-300 mt-0.5">{card.sub}</p>
          </div>
        );
      })}
    </div>
  );
}
