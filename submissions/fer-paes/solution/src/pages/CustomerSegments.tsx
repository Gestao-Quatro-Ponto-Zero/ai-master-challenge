import { useState, useEffect, useCallback } from 'react';
import { Layers, Plus, RefreshCw, Loader2, Users, Zap, CheckCircle2 } from 'lucide-react';
import {
  getSegments,
  refreshAllSegments,
  type CustomerSegment,
} from '../services/segmentationEngineService';
import SegmentsTable       from '../components/segments/SegmentsTable';
import SegmentCreateModal  from '../components/segments/SegmentCreateModal';
import SegmentMembersTable from '../components/segments/SegmentMembersTable';

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label:  string;
  value:  string | number;
  icon:   React.ComponentType<{ className?: string }>;
  color:  string;
}) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 px-5 py-4 flex items-center gap-3">
      <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${color}`}>
        <Icon className="w-4.5 h-4.5 text-current" />
      </div>
      <div>
        <p className="text-xs text-gray-400">{label}</p>
        <p className="text-xl font-bold text-gray-900 tabular-nums">{value}</p>
      </div>
    </div>
  );
}

export default function CustomerSegments() {
  const [segments,        setSegments]        = useState<CustomerSegment[]>([]);
  const [loading,         setLoading]         = useState(true);
  const [refreshingAll,   setRefreshingAll]   = useState(false);
  const [error,           setError]           = useState('');
  const [showCreate,      setShowCreate]      = useState(false);
  const [selectedSegment, setSelectedSegment] = useState<CustomerSegment | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const data = await getSegments();
      setSegments(data);
      if (selectedSegment) {
        const updated = data.find((s) => s.id === selectedSegment.id);
        if (updated) setSelectedSegment(updated);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar segmentos.');
    } finally {
      setLoading(false);
    }
  }, [selectedSegment]);

  useEffect(() => { load(); }, []);

  async function handleRefreshAll() {
    setRefreshingAll(true);
    try {
      await refreshAllSegments();
      await load();
    } finally {
      setRefreshingAll(false);
    }
  }

  async function handleCreated(id: string) {
    setShowCreate(false);
    await load();
    const seg = segments.find((s) => s.id === id);
    if (seg) setSelectedSegment(seg);
  }

  const totalMembers  = segments.reduce((a, s) => a + s.member_count, 0);
  const activeCount   = segments.filter((s) => s.is_active).length;
  const dynamicCount  = segments.filter((s) => s.is_dynamic).length;

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-gray-50 overflow-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 px-8 py-5 shrink-0">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
              <Layers className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">Segmentação de Clientes</h1>
              <p className="text-sm text-gray-400">Agrupe clientes por comportamento e defina campanhas</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleRefreshAll}
              disabled={refreshingAll || loading}
              className="flex items-center gap-1.5 h-9 px-4 rounded-xl border border-gray-200 text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              {refreshingAll
                ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                : <RefreshCw className="w-3.5 h-3.5" />
              }
              Recalcular todos
            </button>
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-1.5 h-9 px-4 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Novo segmento
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 px-8 py-6 space-y-5 min-h-0">
        {error && (
          <div className="px-4 py-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm">
            {error}
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="Total de segmentos"  value={segments.length} icon={Layers}        color="bg-blue-50 text-blue-600"    />
          <StatCard label="Segmentos ativos"     value={activeCount}     icon={CheckCircle2}  color="bg-emerald-50 text-emerald-600" />
          <StatCard label="Dinâmicos"            value={dynamicCount}    icon={Zap}           color="bg-amber-50 text-amber-600"   />
          <StatCard label="Total de membros"     value={totalMembers.toLocaleString('pt-BR')} icon={Users} color="bg-sky-50 text-sky-600" />
        </div>

        {/* Main area */}
        <div className="flex gap-5 items-start">
          <div className="flex-1 min-w-0 space-y-3">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-gray-400" />
              <h2 className="text-sm font-semibold text-gray-700">Segmentos</h2>
              {loading && <Loader2 className="w-3.5 h-3.5 text-gray-300 animate-spin ml-1" />}
            </div>
            <SegmentsTable
              segments={segments}
              loading={loading}
              onSelect={(seg) => setSelectedSegment((prev) => (prev?.id === seg.id ? null : seg))}
              selectedId={selectedSegment?.id}
              onRefresh={load}
            />
          </div>

          {selectedSegment && (
            <div className="w-[500px] shrink-0 sticky top-0">
              <SegmentMembersTable
                segment={selectedSegment}
                onClose={() => setSelectedSegment(null)}
              />
            </div>
          )}
        </div>
      </div>

      {showCreate && (
        <SegmentCreateModal
          onClose={() => setShowCreate(false)}
          onCreated={handleCreated}
        />
      )}
    </div>
  );
}
