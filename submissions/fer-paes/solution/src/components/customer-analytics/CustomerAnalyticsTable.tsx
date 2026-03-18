import { Loader2, User, RefreshCw, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { CustomerAnalyticsRow } from '../../services/customerAnalyticsService';
import {
  formatResponseTime,
  formatLastInteraction,
  engagementLabel,
  refreshCustomerAnalytics,
} from '../../services/customerAnalyticsService';
import { useState } from 'react';

interface Props {
  data:    CustomerAnalyticsRow[];
  loading: boolean;
  onRefreshed: (customerId: string) => void;
}

function EngagementBar({ score }: { score: number }) {
  const pct = Math.min(100, Math.max(0, score));
  const color =
    pct >= 70 ? 'bg-emerald-500' :
    pct >= 40 ? 'bg-amber-400' :
    pct >= 10 ? 'bg-orange-400' :
               'bg-gray-300';
  return (
    <div className="flex items-center gap-2 min-w-[100px]">
      <div className="flex-1 h-1.5 rounded-full bg-gray-100 overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-semibold tabular-nums text-gray-700 w-8 text-right">
        {pct.toFixed(0)}
      </span>
    </div>
  );
}

export default function CustomerAnalyticsTable({ data, loading, onRefreshed }: Props) {
  const [refreshingId, setRefreshingId] = useState<string | null>(null);

  async function handleRefresh(customerId: string) {
    setRefreshingId(customerId);
    try {
      await refreshCustomerAnalytics(customerId);
      onRefreshed(customerId);
    } finally {
      setRefreshingId(null);
    }
  }

  if (loading && data.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 flex items-center justify-center py-20">
        <Loader2 className="w-5 h-5 text-gray-300 animate-spin" />
      </div>
    );
  }

  if (!loading && data.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 flex flex-col items-center justify-center py-20 gap-3">
        <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center">
          <User className="w-6 h-6 text-gray-300" />
        </div>
        <p className="text-sm text-gray-400">Nenhum dado de analytics encontrado</p>
        <p className="text-xs text-gray-300">Clique em "Recalcular Tudo" para gerar as métricas</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100">
              {['Cliente', 'Mensagens', 'Tickets', 'Resolvidos', 'T. Resposta', 'Última Interação', 'Engajamento', ''].map((h) => (
                <th
                  key={h}
                  className="text-left px-5 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider whitespace-nowrap"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {data.map((row) => {
              const { label, color } = engagementLabel(row.engagement_score);
              const isRefreshing = refreshingId === row.customer_id;
              return (
                <tr key={row.customer_id} className="hover:bg-gray-50/50 transition-colors group">
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-full bg-blue-50 flex items-center justify-center shrink-0">
                        <User className="w-3.5 h-3.5 text-blue-400" />
                      </div>
                      <div>
                        <Link
                          to={`/customers/${row.customer_id}`}
                          className="text-sm font-medium text-gray-900 hover:text-blue-600 transition-colors"
                        >
                          {row.customer_name ?? 'Sem nome'}
                        </Link>
                        {row.customer_email && (
                          <p className="text-xs text-gray-400 truncate max-w-[180px]">{row.customer_email}</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-3.5 text-sm font-semibold text-gray-900 tabular-nums">
                    {row.total_messages.toLocaleString('pt-BR')}
                  </td>
                  <td className="px-5 py-3.5 text-sm text-gray-700 tabular-nums">
                    {row.total_tickets.toLocaleString('pt-BR')}
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm text-gray-700 tabular-nums">
                        {row.resolved_tickets.toLocaleString('pt-BR')}
                      </span>
                      {row.total_tickets > 0 && (
                        <span className="text-xs text-gray-400">
                          ({((row.resolved_tickets / row.total_tickets) * 100).toFixed(0)}%)
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-5 py-3.5 text-sm text-gray-500 tabular-nums whitespace-nowrap">
                    {formatResponseTime(row.avg_response_time)}
                  </td>
                  <td className="px-5 py-3.5 text-sm text-gray-500 whitespace-nowrap">
                    {formatLastInteraction(row.last_interaction)}
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-3">
                      <EngagementBar score={row.engagement_score} />
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium border ${color}`}>
                        {label}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handleRefresh(row.customer_id)}
                        disabled={isRefreshing}
                        title="Recalcular métricas"
                        className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors disabled:opacity-50"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
                      </button>
                      <Link
                        to={`/customers/${row.customer_id}`}
                        title="Ver cliente"
                        className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {loading && data.length > 0 && (
        <div className="flex items-center justify-center py-3 border-t border-gray-100">
          <Loader2 className="w-4 h-4 text-gray-300 animate-spin" />
        </div>
      )}
    </div>
  );
}
