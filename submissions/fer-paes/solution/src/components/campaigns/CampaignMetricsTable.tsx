import { useState } from 'react';
import { BarChart2, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import type { CampaignAnalyticsRow } from '../../services/campaignAnalyticsService';
import { CHANNEL_META, STATUS_META } from '../../services/campaignService';

type SortKey = 'campaign_name' | 'sent_count' | 'delivered_count' | 'open_rate' | 'click_rate' | 'conversion_rate';

function RateBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2 min-w-0">
      <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden shrink-0">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
      <span className="text-xs font-medium tabular-nums text-gray-600">{value}%</span>
    </div>
  );
}

function SortIcon({ field, current, dir }: { field: SortKey; current: SortKey; dir: 'asc' | 'desc' }) {
  if (field !== current) return <ArrowUpDown className="w-3 h-3 text-gray-300" />;
  return dir === 'asc'
    ? <ArrowUp className="w-3 h-3 text-gray-500" />
    : <ArrowDown className="w-3 h-3 text-gray-500" />;
}

interface Props {
  rows:    CampaignAnalyticsRow[];
  loading: boolean;
  onSelect?: (row: CampaignAnalyticsRow) => void;
  selected?: string | null;
}

export default function CampaignMetricsTable({ rows, loading, onSelect, selected }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('sent_count');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  function handleSort(key: SortKey) {
    if (key === sortKey) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortKey(key); setSortDir('desc'); }
  }

  const sorted = [...rows].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];
    const cmp = typeof av === 'string' ? av.localeCompare(bv as string) : (av as number) - (bv as number);
    return sortDir === 'asc' ? cmp : -cmp;
  });

  const headers: { label: string; key?: SortKey; align?: string }[] = [
    { label: 'Campanha',    key: 'campaign_name' },
    { label: 'Canal'  },
    { label: 'Status' },
    { label: 'Enviados',    key: 'sent_count',    align: 'text-right' },
    { label: 'Entregues',   key: 'delivered_count',align: 'text-right' },
    { label: 'Abertura',    key: 'open_rate' },
    { label: 'Clique',      key: 'click_rate' },
    { label: 'Conversão',   key: 'conversion_rate' },
  ];

  if (rows.length === 0 && !loading) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 flex flex-col items-center justify-center py-20 gap-3">
        <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center">
          <BarChart2 className="w-6 h-6 text-gray-300" />
        </div>
        <p className="text-sm text-gray-400">Nenhuma campanha com métricas disponíveis</p>
        <p className="text-xs text-gray-300">Execute uma campanha para gerar dados de performance</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-100">
            {headers.map(({ label, key, align }) => (
              <th
                key={label}
                onClick={() => key && handleSort(key)}
                className={`text-left px-5 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider whitespace-nowrap
                  ${key ? 'cursor-pointer select-none hover:text-gray-600 transition-colors' : ''}
                  ${align ?? ''}`}
              >
                <div className="inline-flex items-center gap-1">
                  {label}
                  {key && <SortIcon field={key} current={sortKey} dir={sortDir} />}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {loading && rows.length === 0 ? (
            Array.from({ length: 4 }).map((_, i) => (
              <tr key={i} className="animate-pulse">
                {headers.map((h) => (
                  <td key={h.label} className="px-5 py-4">
                    <div className="h-3 bg-gray-100 rounded-full w-full max-w-[80px]" />
                  </td>
                ))}
              </tr>
            ))
          ) : (
            sorted.map((row) => {
              const chMeta  = CHANNEL_META[row.campaign_channel];
              const stMeta  = STATUS_META[row.campaign_status];
              const isSelected = selected === row.campaign_id;

              return (
                <tr
                  key={row.campaign_id}
                  onClick={() => onSelect?.(row)}
                  className={`transition-colors ${onSelect ? 'cursor-pointer' : ''}
                    ${isSelected ? 'bg-sky-50/60' : 'hover:bg-gray-50/50'}`}
                >
                  {/* Campaign name */}
                  <td className="px-5 py-3.5">
                    <p className="text-sm font-medium text-gray-800 truncate max-w-[180px]">{row.campaign_name}</p>
                    {row.segment_name && (
                      <p className="text-xs text-gray-400 truncate max-w-[180px]">{row.segment_name}</p>
                    )}
                  </td>

                  {/* Channel */}
                  <td className="px-5 py-3.5">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${chMeta.color} ${chMeta.bg}`}>
                      {chMeta.label}
                    </span>
                  </td>

                  {/* Status */}
                  <td className="px-5 py-3.5">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${stMeta.color} ${stMeta.bg} ${stMeta.border}`}>
                      {stMeta.label}
                    </span>
                  </td>

                  {/* Sent */}
                  <td className="px-5 py-3.5 text-right">
                    <span className="text-sm font-medium text-gray-700 tabular-nums">
                      {row.sent_count.toLocaleString('pt-BR')}
                    </span>
                  </td>

                  {/* Delivered */}
                  <td className="px-5 py-3.5 text-right">
                    <span className="text-sm font-medium text-emerald-600 tabular-nums">
                      {row.delivered_count.toLocaleString('pt-BR')}
                    </span>
                  </td>

                  {/* Open rate */}
                  <td className="px-5 py-3.5">
                    <RateBar value={row.open_rate} color="bg-blue-400" />
                  </td>

                  {/* Click rate */}
                  <td className="px-5 py-3.5">
                    <RateBar value={row.click_rate} color="bg-violet-400" />
                  </td>

                  {/* Conversion rate */}
                  <td className="px-5 py-3.5">
                    <RateBar value={row.conversion_rate} color="bg-teal-400" />
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
