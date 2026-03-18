import { useState } from 'react';
import { ChevronDown, ChevronUp, ChevronsUpDown } from 'lucide-react';
import type { OperatorMetricRow } from '../../services/metricsService';
import { formatDuration } from '../../services/metricsService';

type SortKey = keyof Pick<
  OperatorMetricRow,
  'tickets_handled' | 'tickets_resolved' | 'avg_first_response_time' | 'avg_resolution_time' | 'resolution_rate' | 'csat_score'
>;

interface Props {
  rows:             OperatorMetricRow[];
  selectedId:       string | null;
  onSelectOperator: (row: OperatorMetricRow) => void;
}

function Avatar({ name, email }: { name: string; email: string }) {
  const label    = name || email;
  const initials = label.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase() || '?';
  const colors   = ['bg-blue-600', 'bg-emerald-600', 'bg-amber-600', 'bg-rose-600', 'bg-cyan-600'];
  const color    = colors[(initials.charCodeAt(0) ?? 0) % colors.length];
  return (
    <div className={`w-7 h-7 rounded-full ${color} flex items-center justify-center shrink-0`}>
      <span className="text-white text-xs font-semibold">{initials}</span>
    </div>
  );
}

function RateBar({ value }: { value: number }) {
  const color = value >= 80 ? 'bg-emerald-500' : value >= 50 ? 'bg-amber-400' : 'bg-rose-500';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-700/60 rounded-full overflow-hidden min-w-[40px]">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${value}%` }} />
      </div>
      <span className={`text-xs tabular-nums w-8 text-right font-medium ${value >= 80 ? 'text-emerald-400' : value >= 50 ? 'text-amber-400' : 'text-rose-400'}`}>
        {value}%
      </span>
    </div>
  );
}

interface SortState { key: SortKey; dir: 'asc' | 'desc' }

const COLUMNS: { key: SortKey; label: string; align?: string }[] = [
  { key: 'tickets_handled',         label: 'Handled'       },
  { key: 'tickets_resolved',        label: 'Resolved'      },
  { key: 'avg_first_response_time', label: 'Avg Response'  },
  { key: 'avg_resolution_time',     label: 'Avg Resolution' },
  { key: 'resolution_rate',         label: 'Rate'          },
  { key: 'csat_score',              label: 'CSAT'          },
];

const LOWER_BETTER_KEYS: SortKey[] = ['avg_first_response_time', 'avg_resolution_time'];

export default function OperatorMetricsTable({ rows, selectedId, onSelectOperator }: Props) {
  const [sort, setSort] = useState<SortState>({ key: 'tickets_handled', dir: 'desc' });

  function toggleSort(key: SortKey) {
    setSort((prev) =>
      prev.key === key
        ? { key, dir: prev.dir === 'asc' ? 'desc' : 'asc' }
        : { key, dir: LOWER_BETTER_KEYS.includes(key) ? 'asc' : 'desc' },
    );
  }

  const sorted = [...rows].sort((a, b) => {
    const av = (a[sort.key] as number) ?? 0;
    const bv = (b[sort.key] as number) ?? 0;
    return sort.dir === 'asc' ? av - bv : bv - av;
  });

  function SortIcon({ col }: { col: SortKey }) {
    if (sort.key !== col) return <ChevronsUpDown className="w-3 h-3 text-slate-700" />;
    return sort.dir === 'asc'
      ? <ChevronUp className="w-3 h-3 text-emerald-400" />
      : <ChevronDown className="w-3 h-3 text-emerald-400" />;
  }

  return (
    <div className="bg-slate-900/60 border border-white/6 rounded-2xl overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-white/5">
            <th className="px-4 py-3 text-left text-xs font-medium text-slate-600">Operator</th>
            {COLUMNS.map((col) => (
              <th key={col.key} className="px-4 py-3 text-left text-xs font-medium text-slate-600">
                <button
                  onClick={() => toggleSort(col.key)}
                  className="flex items-center gap-1 hover:text-slate-300 transition-colors"
                >
                  {col.label}
                  <SortIcon col={col.key} />
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, idx) => {
            const isSelected = row.operator_id === selectedId;
            return (
              <tr
                key={row.operator_id}
                onClick={() => onSelectOperator(row)}
                className={`border-b border-white/4 last:border-0 cursor-pointer transition-colors ${
                  isSelected ? 'bg-emerald-500/8 hover:bg-emerald-500/10' : 'hover:bg-white/3'
                }`}
              >
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2.5">
                    <div className="relative">
                      <Avatar name={row.full_name} email={row.email} />
                      {idx === 0 && sort.key === 'tickets_handled' && (
                        <span className="absolute -top-1 -right-1 text-[10px]">🥇</span>
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-medium text-white truncate">{row.full_name || row.email}</p>
                      {row.full_name && <p className="text-xs text-slate-600 truncate">{row.email}</p>}
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm font-semibold tabular-nums text-blue-400">{row.tickets_handled}</span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm font-semibold tabular-nums text-emerald-400">{row.tickets_resolved}</span>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs tabular-nums ${
                    row.avg_first_response_time === 0 ? 'text-slate-700'
                    : row.avg_first_response_time <= 10 ? 'text-emerald-400'
                    : row.avg_first_response_time <= 30 ? 'text-amber-400'
                    : 'text-rose-400'
                  }`}>
                    {formatDuration(row.avg_first_response_time)}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs tabular-nums ${
                    row.avg_resolution_time === 0 ? 'text-slate-700'
                    : row.avg_resolution_time <= 120 ? 'text-emerald-400'
                    : row.avg_resolution_time <= 480 ? 'text-amber-400'
                    : 'text-rose-400'
                  }`}>
                    {formatDuration(row.avg_resolution_time)}
                  </span>
                </td>
                <td className="px-4 py-3 min-w-[100px]">
                  <RateBar value={row.resolution_rate} />
                </td>
                <td className="px-4 py-3">
                  {row.csat_score != null ? (
                    <span className={`text-xs font-medium ${
                      row.csat_score >= 4 ? 'text-emerald-400' : row.csat_score >= 3 ? 'text-amber-400' : 'text-rose-400'
                    }`}>
                      {row.csat_score.toFixed(1)}
                    </span>
                  ) : (
                    <span className="text-xs text-slate-700">—</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
