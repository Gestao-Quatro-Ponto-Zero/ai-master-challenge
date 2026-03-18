import { Loader2, Trophy, User } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { TopCustomerRow } from '../../services/customerAnalyticsService';
import { formatLastInteraction, engagementLabel } from '../../services/customerAnalyticsService';

interface Props {
  data:    TopCustomerRow[];
  loading: boolean;
}

const RANK_STYLES = [
  'bg-amber-400 text-white',
  'bg-gray-300  text-white',
  'bg-orange-400 text-white',
];

export default function TopCustomersTable({ data, loading }: Props) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
      <div className="flex items-center gap-2.5 px-5 py-4 border-b border-gray-100">
        <div className="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center">
          <Trophy className="w-4 h-4 text-amber-500" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gray-900">Clientes Mais Engajados</h3>
          <p className="text-xs text-gray-400">Top 10 por pontuação de engajamento</p>
        </div>
      </div>

      {loading && data.length === 0 ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-5 h-5 text-gray-300 animate-spin" />
        </div>
      ) : data.length === 0 ? (
        <div className="py-10 text-center text-sm text-gray-400">
          Nenhum dado disponível
        </div>
      ) : (
        <div className="divide-y divide-gray-50">
          {data.map((row, idx) => {
            const { label, color } = engagementLabel(row.engagement_score);
            const rankStyle = RANK_STYLES[idx] ?? 'bg-gray-100 text-gray-500';
            return (
              <div
                key={row.customer_id}
                className="flex items-center gap-3 px-5 py-3.5 hover:bg-gray-50/50 transition-colors"
              >
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${rankStyle}`}>
                  {idx + 1}
                </div>
                <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center shrink-0">
                  <User className="w-4 h-4 text-blue-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <Link
                    to={`/customers/${row.customer_id}`}
                    className="text-sm font-medium text-gray-900 hover:text-blue-600 transition-colors truncate block"
                  >
                    {row.customer_name ?? 'Sem nome'}
                  </Link>
                  <p className="text-xs text-gray-400 truncate">
                    {row.total_messages} msg · {row.total_tickets} tickets · {formatLastInteraction(row.last_interaction)}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${color}`}>
                    {label}
                  </span>
                  <span className="text-sm font-bold text-gray-700 tabular-nums w-8 text-right">
                    {row.engagement_score.toFixed(0)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
