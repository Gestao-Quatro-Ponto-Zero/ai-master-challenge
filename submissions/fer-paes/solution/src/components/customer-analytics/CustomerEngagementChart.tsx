import { Loader2, TrendingUp } from 'lucide-react';
import type { CustomerAnalyticsRow } from '../../services/customerAnalyticsService';

interface Props {
  data:    CustomerAnalyticsRow[];
  loading: boolean;
}

const BANDS = [
  { label: 'Inativo (0)',       min: 0,  max: 10,  color: 'bg-gray-300',   textColor: 'text-gray-500'   },
  { label: 'Baixo (10–39)',     min: 10, max: 40,  color: 'bg-orange-400', textColor: 'text-orange-600' },
  { label: 'Médio (40–69)',     min: 40, max: 70,  color: 'bg-amber-400',  textColor: 'text-amber-600'  },
  { label: 'Alto (70–100)',     min: 70, max: 101, color: 'bg-emerald-500', textColor: 'text-emerald-600' },
];

export default function CustomerEngagementChart({ data, loading }: Props) {
  const total = data.length;

  const bands = BANDS.map((b) => {
    const count = data.filter((r) => r.engagement_score >= b.min && r.engagement_score < b.max).length;
    const pct   = total > 0 ? (count / total) * 100 : 0;
    return { ...b, count, pct };
  });

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-6">
      <div className="flex items-center gap-2 mb-5">
        <div className="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center">
          <TrendingUp className="w-4 h-4 text-amber-600" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gray-900">Distribuição de Engajamento</h3>
          <p className="text-xs text-gray-400">Concentração de clientes por faixa de pontuação</p>
        </div>
      </div>

      {loading && total === 0 ? (
        <div className="flex items-center justify-center py-10">
          <Loader2 className="w-5 h-5 text-gray-300 animate-spin" />
        </div>
      ) : total === 0 ? (
        <div className="py-8 text-center text-sm text-gray-400">
          Nenhum dado de engajamento disponível
        </div>
      ) : (
        <div className="space-y-4">
          {bands.map((b) => (
            <div key={b.label}>
              <div className="flex items-center justify-between mb-1.5">
                <span className={`text-xs font-medium ${b.textColor}`}>{b.label}</span>
                <span className="text-xs font-semibold text-gray-700 tabular-nums">
                  {b.count} <span className="text-gray-400 font-normal">({b.pct.toFixed(1)}%)</span>
                </span>
              </div>
              <div className="h-2.5 rounded-full bg-gray-100 overflow-hidden">
                <div
                  className={`h-full rounded-full ${b.color} transition-all duration-700`}
                  style={{ width: `${b.pct}%` }}
                />
              </div>
            </div>
          ))}

          <div className="pt-2 mt-2 border-t border-gray-100 flex items-center justify-between">
            <span className="text-xs text-gray-400">Total analisado</span>
            <span className="text-xs font-semibold text-gray-700">{total} clientes</span>
          </div>
        </div>
      )}
    </div>
  );
}
