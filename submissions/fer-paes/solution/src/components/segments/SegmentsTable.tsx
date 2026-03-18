import { useState } from 'react';
import { Loader2, Layers, RefreshCw, PencilLine, ChevronRight, Users, CheckCircle2, XCircle, Zap, Settings } from 'lucide-react';
import type { CustomerSegment, SegmentRule } from '../../services/segmentationEngineService';
import { ruleLabel, updateSegment, refreshSegmentMembers } from '../../services/segmentationEngineService';

interface Props {
  segments:    CustomerSegment[];
  loading:     boolean;
  onSelect:    (segment: CustomerSegment) => void;
  selectedId?: string;
  onRefresh:   () => void;
}

function RuleChips({ rules }: { rules: SegmentRule }) {
  const entries = Object.entries(rules).filter(([, v]) => v !== null && v !== undefined);
  if (entries.length === 0) return <span className="text-xs text-gray-300 italic">Sem regras</span>;
  return (
    <div className="flex flex-wrap gap-1">
      {entries.slice(0, 3).map(([k, v]) => (
        <span
          key={k}
          className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-500 border border-gray-100"
        >
          {ruleLabel(k as keyof SegmentRule, v)}
        </span>
      ))}
      {entries.length > 3 && (
        <span className="text-xs text-gray-400">+{entries.length - 3}</span>
      )}
    </div>
  );
}

function SegmentRow({
  segment,
  isSelected,
  onSelect,
  onRefreshed,
}: {
  segment:     CustomerSegment;
  isSelected:  boolean;
  onSelect:    () => void;
  onRefreshed: (count: number) => void;
}) {
  const [refreshing, setRefreshing] = useState(false);
  const [toggling,   setToggling]   = useState(false);

  async function handleRefresh(e: React.MouseEvent) {
    e.stopPropagation();
    setRefreshing(true);
    try {
      const count = await refreshSegmentMembers(segment.id);
      onRefreshed(count);
    } finally {
      setRefreshing(false);
    }
  }

  async function handleToggleActive(e: React.MouseEvent) {
    e.stopPropagation();
    setToggling(true);
    try {
      await updateSegment(segment.id, { is_active: !segment.is_active });
      onRefreshed(segment.member_count);
    } finally {
      setToggling(false);
    }
  }

  return (
    <tr
      onClick={onSelect}
      className={`cursor-pointer transition-colors ${
        isSelected ? 'bg-blue-50/60 hover:bg-blue-50/80' : 'hover:bg-gray-50/50'
      }`}
    >
      <td className="px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${
            segment.is_active ? 'bg-blue-50' : 'bg-gray-50'
          }`}>
            <Layers className={`w-3.5 h-3.5 ${segment.is_active ? 'text-blue-500' : 'text-gray-300'}`} />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-800">{segment.segment_name}</p>
            {segment.description && (
              <p className="text-xs text-gray-400 truncate max-w-[200px]">{segment.description}</p>
            )}
          </div>
        </div>
      </td>
      <td className="px-5 py-3.5">
        <RuleChips rules={segment.rules} />
      </td>
      <td className="px-5 py-3.5">
        <div className="flex items-center gap-1.5">
          <Users className="w-3.5 h-3.5 text-gray-300" />
          <span className="text-sm font-semibold text-gray-700 tabular-nums">
            {segment.member_count.toLocaleString('pt-BR')}
          </span>
        </div>
      </td>
      <td className="px-5 py-3.5">
        <div className="flex items-center gap-1.5">
          {segment.is_dynamic ? (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-600 border border-amber-100">
              <Zap className="w-2.5 h-2.5" />
              Dinâmico
            </span>
          ) : (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-50 text-gray-500 border border-gray-100">
              <Settings className="w-2.5 h-2.5" />
              Estático
            </span>
          )}
        </div>
      </td>
      <td className="px-5 py-3.5">
        {segment.is_active ? (
          <span className="flex items-center gap-1 text-xs font-medium text-emerald-600">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Ativo
          </span>
        ) : (
          <span className="flex items-center gap-1 text-xs font-medium text-gray-400">
            <XCircle className="w-3.5 h-3.5" />
            Inativo
          </span>
        )}
      </td>
      <td className="px-5 py-3.5">
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          {segment.is_dynamic && (
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              title="Recalcular membros"
              className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 disabled:opacity-40 transition-colors"
            >
              {refreshing
                ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                : <RefreshCw className="w-3.5 h-3.5" />
              }
            </button>
          )}
          <button
            onClick={handleToggleActive}
            disabled={toggling}
            title={segment.is_active ? 'Desativar' : 'Ativar'}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 disabled:opacity-40 transition-colors"
          >
            {toggling
              ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
              : <PencilLine className="w-3.5 h-3.5" />
            }
          </button>
          <button
            onClick={onSelect}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </td>
    </tr>
  );
}

export default function SegmentsTable({ segments, loading, onSelect, selectedId, onRefresh }: Props) {
  if (loading && segments.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 flex items-center justify-center py-20">
        <Loader2 className="w-5 h-5 text-gray-300 animate-spin" />
      </div>
    );
  }

  if (!loading && segments.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 flex flex-col items-center justify-center py-20 gap-3">
        <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center">
          <Layers className="w-6 h-6 text-gray-300" />
        </div>
        <p className="text-sm text-gray-400">Nenhum segmento criado</p>
        <p className="text-xs text-gray-300">Crie um segmento para agrupar clientes por comportamento</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-100">
            {['Segmento', 'Regras', 'Membros', 'Tipo', 'Status', 'Ações'].map((h) => (
              <th key={h} className="text-left px-5 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {segments.map((seg) => (
            <SegmentRow
              key={seg.id}
              segment={seg}
              isSelected={seg.id === selectedId}
              onSelect={() => onSelect(seg)}
              onRefreshed={onRefresh}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
