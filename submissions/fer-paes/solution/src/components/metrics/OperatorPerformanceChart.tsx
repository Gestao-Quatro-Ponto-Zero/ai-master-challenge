import type { OperatorMetricRow } from '../../services/metricsService';
import { formatDuration } from '../../services/metricsService';

interface BarChartItem {
  label:   string;
  value:   number;
  display: string;
  color:   string;
}

interface Props {
  rows:   OperatorMetricRow[];
  metric: 'tickets_handled' | 'tickets_resolved' | 'avg_first_response_time' | 'avg_resolution_time' | 'resolution_rate';
}

const METRIC_META: Record<Props['metric'], {
  label:     string;
  isTime:    boolean;
  lowerBetter: boolean;
}> = {
  tickets_handled:         { label: 'Tickets Handled',      isTime: false, lowerBetter: false },
  tickets_resolved:        { label: 'Tickets Resolved',     isTime: false, lowerBetter: false },
  avg_first_response_time: { label: 'Avg First Response',   isTime: true,  lowerBetter: true  },
  avg_resolution_time:     { label: 'Avg Resolution Time',  isTime: true,  lowerBetter: true  },
  resolution_rate:         { label: 'Resolution Rate (%)',  isTime: false, lowerBetter: false },
};

function getBarColor(pct: number, lowerBetter: boolean): string {
  const effective = lowerBetter ? 100 - pct : pct;
  if (effective >= 80) return 'bg-emerald-500';
  if (effective >= 50) return 'bg-amber-400';
  return 'bg-rose-500';
}

export default function OperatorPerformanceChart({ rows, metric }: Props) {
  const meta   = METRIC_META[metric];
  const values = rows.map((r) => (r[metric] as number) ?? 0);
  const maxVal = Math.max(...values, 1);

  const items: BarChartItem[] = rows.map((r, i) => {
    const val = values[i];
    const pct = Math.round((val / maxVal) * 100);
    return {
      label:   r.full_name || r.email,
      value:   val,
      display: meta.isTime
        ? formatDuration(val)
        : metric === 'resolution_rate'
          ? `${val}%`
          : String(val),
      color:   getBarColor(pct, meta.lowerBetter),
    };
  });

  const sorted = [...items].sort((a, b) => {
    return meta.lowerBetter ? a.value - b.value : b.value - a.value;
  });

  return (
    <div className="space-y-1.5">
      <p className="text-xs font-medium text-slate-500 mb-3">{meta.label}</p>
      {sorted.map((item) => {
        const pct = maxVal > 0 ? Math.round((item.value / maxVal) * 100) : 0;
        return (
          <div key={item.label} className="flex items-center gap-3">
            <div className="w-24 shrink-0 text-right">
              <span className="text-xs text-slate-500 truncate">{item.label.split(' ')[0]}</span>
            </div>
            <div className="flex-1 h-5 bg-slate-800/60 rounded-full overflow-hidden relative">
              <div
                className={`h-full rounded-full transition-all duration-500 ${item.color}`}
                style={{ width: `${pct}%` }}
              />
              <span className="absolute inset-0 flex items-center pl-2 text-[10px] font-medium text-white/80">
                {item.display}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
