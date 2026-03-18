import { useState, useEffect, useCallback } from 'react';
import { Loader2, Users, ChevronLeft, ChevronRight, CircleUser as UserCircle, Ticket, MessageSquare, TrendingUp, RefreshCw, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { CustomerSegment, SegmentMember } from '../../services/segmentationEngineService';
import { getSegmentMembers, refreshSegmentMembers, ruleLabel, type SegmentRule } from '../../services/segmentationEngineService';

const PAGE_SIZE = 50;

function EngagementBar({ score }: { score: number }) {
  const pct  = Math.min(100, Math.max(0, score));
  const color = pct >= 70 ? 'bg-emerald-400' : pct >= 40 ? 'bg-amber-400' : 'bg-red-400';
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-500 tabular-nums w-8">{pct.toFixed(0)}</span>
    </div>
  );
}

interface Props {
  segment: CustomerSegment;
  onClose: () => void;
}

export default function SegmentMembersTable({ segment, onClose }: Props) {
  const [members,     setMembers]    = useState<SegmentMember[]>([]);
  const [totalCount,  setTotalCount] = useState(0);
  const [offset,      setOffset]     = useState(0);
  const [loading,     setLoading]    = useState(true);
  const [refreshing,  setRefreshing] = useState(false);
  const [error,       setError]      = useState('');

  const load = useCallback(async (off: number) => {
    setLoading(true); setError('');
    try {
      const result = await getSegmentMembers(segment.id, PAGE_SIZE, off);
      setMembers(result.members);
      setTotalCount(result.totalCount);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar membros.');
    } finally {
      setLoading(false);
    }
  }, [segment.id]);

  useEffect(() => { setOffset(0); load(0); }, [load]);

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await refreshSegmentMembers(segment.id);
      await load(offset);
    } finally {
      setRefreshing(false);
    }
  }

  const totalPages  = Math.ceil(totalCount / PAGE_SIZE);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const ruleEntries = Object.entries(segment.rules).filter(([, v]) => v !== null && v !== undefined);

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden flex flex-col">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
            <Users className="w-4 h-4 text-blue-600" />
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-gray-900 truncate">{segment.segment_name}</h3>
            <p className="text-xs text-gray-400">
              {totalCount.toLocaleString('pt-BR')} membros
              {segment.last_refreshed_at && (
                <span className="ml-1 text-gray-300">
                  · atualizado {new Date(segment.last_refreshed_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {segment.is_dynamic && (
            <button
              onClick={handleRefresh}
              disabled={refreshing || loading}
              title="Recalcular membros"
              className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 disabled:opacity-40 transition-colors"
            >
              {refreshing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
            </button>
          )}
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Rules summary */}
      {ruleEntries.length > 0 && (
        <div className="px-5 py-2.5 bg-gray-50 border-b border-gray-100 flex flex-wrap gap-1.5">
          {ruleEntries.map(([k, v]) => (
            <span key={k} className="px-2 py-0.5 rounded-full text-xs bg-white border border-gray-200 text-gray-500">
              {ruleLabel(k as keyof SegmentRule, v)}
            </span>
          ))}
        </div>
      )}

      {error && (
        <div className="px-5 py-3 text-sm text-red-600 bg-red-50 border-b border-red-100">{error}</div>
      )}

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-5 h-5 text-gray-300 animate-spin" />
          </div>
        ) : members.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-2">
            <Users className="w-8 h-8 text-gray-200" />
            <p className="text-sm text-gray-400">Nenhum membro neste segmento</p>
            {segment.is_dynamic && (
              <button onClick={handleRefresh} className="text-xs text-blue-500 hover:text-blue-700 transition-colors">
                Recalcular agora
              </button>
            )}
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100">
                {['Cliente', 'Tickets', 'Mensagens', 'Engajamento', 'Adicionado em'].map((h) => (
                  <th key={h} className="text-left px-5 py-2.5 text-xs font-medium text-gray-400 uppercase tracking-wider whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {members.map((m) => (
                <tr key={m.member_id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-blue-50 flex items-center justify-center shrink-0">
                        <UserCircle className="w-4 h-4 text-blue-400" />
                      </div>
                      <div>
                        <Link
                          to={`/customers/${m.customer_id}`}
                          className="text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
                        >
                          {m.customer_name ?? 'Desconhecido'}
                        </Link>
                        <p className="text-xs text-gray-400">{m.customer_email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-3">
                    <span className="flex items-center gap-1 text-sm text-gray-600">
                      <Ticket className="w-3 h-3 text-gray-300" />
                      {Number(m.total_tickets).toLocaleString('pt-BR')}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <span className="flex items-center gap-1 text-sm text-gray-600">
                      <MessageSquare className="w-3 h-3 text-gray-300" />
                      {Number(m.total_messages).toLocaleString('pt-BR')}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-1">
                      <TrendingUp className="w-3 h-3 text-gray-300" />
                      <EngagementBar score={m.engagement_score} />
                    </div>
                  </td>
                  <td className="px-5 py-3 text-xs text-gray-400 whitespace-nowrap tabular-nums">
                    {new Date(m.added_at).toLocaleDateString('pt-BR')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {totalCount > PAGE_SIZE && (
        <div className="flex items-center justify-between px-5 py-3 border-t border-gray-100">
          <p className="text-xs text-gray-400">
            {offset + 1}–{Math.min(offset + members.length, totalCount)} de {totalCount.toLocaleString('pt-BR')}
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => { setOffset(Math.max(0, offset - PAGE_SIZE)); load(Math.max(0, offset - PAGE_SIZE)); }}
              disabled={currentPage <= 1 || loading}
              className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-xs text-gray-500 px-2">{currentPage} / {totalPages}</span>
            <button
              onClick={() => { setOffset(offset + PAGE_SIZE); load(offset + PAGE_SIZE); }}
              disabled={currentPage >= totalPages || loading}
              className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
