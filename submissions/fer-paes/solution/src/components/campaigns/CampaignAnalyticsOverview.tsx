import { Loader2, Send, CheckCircle2, Eye, MousePointerClick, MessageCircle, Zap, Megaphone } from 'lucide-react';
import type { AnalyticsOverview } from '../../services/campaignAnalyticsService';

interface CardProps {
  label:   string;
  value:   string | number;
  sub?:    string;
  icon:    React.ComponentType<{ className?: string }>;
  color:   string;
  bg:      string;
  border:  string;
}

function OverviewCard({ label, value, sub, icon: Icon, color, bg, border }: CardProps) {
  return (
    <div className={`bg-white rounded-2xl border ${border} px-5 py-4 flex items-start gap-4`}>
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${bg}`}>
        <Icon className={`w-5 h-5 ${color}`} />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-gray-400 font-medium">{label}</p>
        <p className={`text-2xl font-bold tabular-nums ${color}`}>{value}</p>
        {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

interface Props {
  overview: AnalyticsOverview | null;
  loading:  boolean;
}

export default function CampaignAnalyticsOverview({ overview, loading }: Props) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="bg-white rounded-2xl border border-gray-100 px-5 py-4 flex items-center gap-3 animate-pulse">
            <div className="w-10 h-10 rounded-xl bg-gray-100 shrink-0" />
            <div className="space-y-2 flex-1">
              <div className="h-3 bg-gray-100 rounded-full w-16" />
              <div className="h-6 bg-gray-100 rounded-full w-12" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  const o = overview ?? {
    total_campaigns: 0, total_sent: 0, total_delivered: 0,
    total_opens: 0, total_clicks: 0, total_replies: 0, total_conversions: 0,
    avg_open_rate: 0, avg_click_rate: 0, avg_conversion_rate: 0,
  };

  const cards: CardProps[] = [
    {
      label: 'Campanhas',     value: o.total_campaigns,
      icon: Megaphone,        color: 'text-gray-600', bg: 'bg-gray-50',     border: 'border-gray-100',
    },
    {
      label: 'Total Enviados', value: o.total_sent.toLocaleString('pt-BR'),
      sub: `${o.total_delivered.toLocaleString('pt-BR')} entregues`,
      icon: Send,             color: 'text-sky-600',     bg: 'bg-sky-50',     border: 'border-sky-100',
    },
    {
      label: 'Taxa de Abertura', value: `${o.avg_open_rate}%`,
      sub: `${o.total_opens.toLocaleString('pt-BR')} aberturas`,
      icon: Eye,              color: 'text-blue-600',    bg: 'bg-blue-50',    border: 'border-blue-100',
    },
    {
      label: 'Taxa de Clique',   value: `${o.avg_click_rate}%`,
      sub: `${o.total_clicks.toLocaleString('pt-BR')} cliques`,
      icon: MousePointerClick,color: 'text-violet-600',  bg: 'bg-violet-50',  border: 'border-violet-100',
    },
    {
      label: 'Taxa de Conversão',value: `${o.avg_conversion_rate}%`,
      sub: `${o.total_conversions.toLocaleString('pt-BR')} conversões`,
      icon: Zap,              color: 'text-teal-600',    bg: 'bg-teal-50',    border: 'border-teal-100',
    },
  ];

  const replyCard: CardProps = {
    label: 'Total Respostas', value: o.total_replies.toLocaleString('pt-BR'),
    icon: MessageCircle,      color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-100',
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {cards.map((c) => <OverviewCard key={c.label} {...c} />)}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <OverviewCard {...replyCard} />
        {/* delivery funnel mini-viz */}
        {o.total_sent > 0 && (
          <div className="col-span-1 sm:col-span-2 bg-white rounded-2xl border border-gray-100 px-5 py-4">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Funil de Engajamento</p>
            {[
              { label: 'Enviados',   count: o.total_sent,        color: 'bg-sky-400'    },
              { label: 'Entregues',  count: o.total_delivered,   color: 'bg-emerald-400'},
              { label: 'Abertos',    count: o.total_opens,       color: 'bg-blue-400'   },
              { label: 'Clicados',   count: o.total_clicks,      color: 'bg-violet-400' },
              { label: 'Convertidos',count: o.total_conversions, color: 'bg-teal-400'   },
            ].map(({ label, count, color }) => {
              const pct = o.total_sent > 0 ? Math.round(count / o.total_sent * 100) : 0;
              return (
                <div key={label} className="flex items-center gap-3 mb-1.5">
                  <p className="text-xs text-gray-400 w-24 shrink-0 text-right">{label}</p>
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className={`h-full ${color} rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
                  </div>
                  <span className="text-xs font-medium text-gray-500 tabular-nums w-12">{count.toLocaleString('pt-BR')}</span>
                  <span className="text-xs text-gray-300 w-10 tabular-nums">{pct}%</span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
