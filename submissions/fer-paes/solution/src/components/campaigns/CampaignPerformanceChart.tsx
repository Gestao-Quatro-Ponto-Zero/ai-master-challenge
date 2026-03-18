import { useState } from 'react';
import { Loader2, BarChart2 } from 'lucide-react';
import type { CampaignAnalyticsRow } from '../../services/campaignAnalyticsService';

type MetricKey = 'sent_count' | 'delivered_count' | 'open_count' | 'click_count' | 'reply_count' | 'conversion_count';

const METRICS: { key: MetricKey; label: string; color: string; bg: string }[] = [
  { key: 'sent_count',       label: 'Enviados',    color: 'bg-sky-400',    bg: 'bg-sky-50'    },
  { key: 'delivered_count',  label: 'Entregues',   color: 'bg-emerald-400',bg: 'bg-emerald-50'},
  { key: 'open_count',       label: 'Abertos',     color: 'bg-blue-400',   bg: 'bg-blue-50'   },
  { key: 'click_count',      label: 'Clicados',    color: 'bg-violet-400', bg: 'bg-violet-50' },
  { key: 'reply_count',      label: 'Respondidos', color: 'bg-amber-400',  bg: 'bg-amber-50'  },
  { key: 'conversion_count', label: 'Convertidos', color: 'bg-teal-400',   bg: 'bg-teal-50'   },
];

interface BarProps {
  campaigns: CampaignAnalyticsRow[];
  metric:    typeof METRICS[number];
  maxValue:  number;
}

function Bars({ campaigns, metric, maxValue }: BarProps) {
  const [hovered, setHovered] = useState<string | null>(null);

  if (campaigns.length === 0) return null;

  return (
    <div className="flex items-end gap-1.5 h-40 w-full overflow-x-auto pb-1">
      {campaigns.map((c) => {
        const val = c[metric.key];
        const pct = maxValue > 0 ? (val / maxValue) * 100 : 0;
        const isHov = hovered === c.campaign_id;

        return (
          <div
            key={c.campaign_id}
            className="flex flex-col items-center gap-1 flex-1 min-w-[32px] max-w-[64px] group"
            onMouseEnter={() => setHovered(c.campaign_id)}
            onMouseLeave={() => setHovered(null)}
          >
            {isHov && (
              <div className="bg-gray-800 text-white text-xs rounded-lg px-2 py-1 whitespace-nowrap absolute -translate-y-8 pointer-events-none z-10 shadow-lg">
                {c.campaign_name}: {val.toLocaleString('pt-BR')}
              </div>
            )}
            <div className="w-full flex items-end justify-center h-32">
              <div
                className={`w-full rounded-t-md transition-all duration-300 ${metric.color} ${isHov ? 'opacity-100 scale-y-105' : 'opacity-80'}`}
                style={{ height: `${Math.max(pct, pct > 0 ? 4 : 0)}%` }}
              />
            </div>
            <p className="text-[10px] text-gray-400 truncate w-full text-center px-0.5">
              {c.campaign_name.length > 8 ? c.campaign_name.slice(0, 7) + '…' : c.campaign_name}
            </p>
          </div>
        );
      })}
    </div>
  );
}

interface Props {
  rows:    CampaignAnalyticsRow[];
  loading: boolean;
}

export default function CampaignPerformanceChart({ rows, loading }: Props) {
  const [activeMetric, setActiveMetric] = useState<MetricKey>('sent_count');
  const metric  = METRICS.find((m) => m.key === activeMetric)!;
  const maxVal  = Math.max(...rows.map((r) => r[activeMetric]), 1);
  const topRows = rows.slice(0, 12);

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5">
      <div className="flex items-start justify-between gap-4 mb-5 flex-wrap">
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <BarChart2 className="w-4 h-4 text-gray-400" />
            <h3 className="text-sm font-semibold text-gray-700">Performance por Campanha</h3>
          </div>
          <p className="text-xs text-gray-400">Comparativo das primeiras {topRows.length} campanhas por métrica selecionada</p>
        </div>

        {/* Metric selector */}
        <div className="flex flex-wrap gap-1.5">
          {METRICS.map((m) => (
            <button
              key={m.key}
              onClick={() => setActiveMetric(m.key)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all border
                ${activeMetric === m.key
                  ? `${m.color.replace('bg-', 'bg-').replace('-400', '-100')} ${m.color.replace('bg-', 'text-').replace('-400', '-700')} border-transparent shadow-sm`
                  : 'bg-gray-50 text-gray-500 border-gray-100 hover:bg-gray-100'
                }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="h-40 flex items-center justify-center">
          <Loader2 className="w-5 h-5 text-gray-300 animate-spin" />
        </div>
      ) : rows.length === 0 ? (
        <div className="h-40 flex flex-col items-center justify-center gap-2">
          <BarChart2 className="w-8 h-8 text-gray-200" />
          <p className="text-sm text-gray-300">Sem dados para exibir</p>
        </div>
      ) : (
        <div className="relative">
          {/* Y-axis guides */}
          <div className="absolute inset-0 flex flex-col justify-between pointer-events-none pb-5">
            {[1, 0.75, 0.5, 0.25, 0].map((frac) => (
              <div key={frac} className="flex items-center gap-2 w-full">
                <span className="text-[10px] text-gray-300 w-8 text-right shrink-0">
                  {Math.round(maxVal * frac).toLocaleString('pt-BR')}
                </span>
                <div className="flex-1 border-t border-dashed border-gray-100" />
              </div>
            ))}
          </div>

          <div className="pl-10 relative">
            <Bars campaigns={topRows} metric={metric} maxValue={maxVal} />
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="mt-3 pt-3 border-t border-gray-50 flex items-center gap-2">
        <div className={`w-3 h-3 rounded-sm ${metric.color}`} />
        <span className="text-xs text-gray-500">{metric.label}</span>
        {rows.length > 12 && (
          <span className="text-xs text-gray-300 ml-auto">
            Exibindo top 12 de {rows.length} campanhas
          </span>
        )}
      </div>
    </div>
  );
}
