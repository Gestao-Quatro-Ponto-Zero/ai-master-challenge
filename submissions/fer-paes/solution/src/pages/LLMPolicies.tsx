import { useState, useEffect, useCallback } from 'react';
import { Plus, Loader2, SlidersHorizontal, Info } from 'lucide-react';
import {
  getPolicies,
  updatePolicy,
  deletePolicy,
  TASK_TYPES,
  type LLMPolicy,
} from '../services/promptPolicyService';
import { getActiveModels, type RouterModel } from '../services/llmRouterService';
import LLMPoliciesTable    from '../components/llm/LLMPoliciesTable';
import LLMPolicyCreateModal from '../components/llm/LLMPolicyCreateModal';
import LLMPolicyEditModal   from '../components/llm/LLMPolicyEditModal';

const TASK_COLORS: Record<string, string> = {
  chat:           'bg-blue-500/10   text-blue-400   border-blue-500/20',
  classification: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  summarization:  'bg-amber-500/10  text-amber-400  border-amber-500/20',
  reasoning:      'bg-rose-500/10   text-rose-400   border-rose-500/20',
  extraction:     'bg-cyan-500/10   text-cyan-400   border-cyan-500/20',
  translation:    'bg-teal-500/10   text-teal-400   border-teal-500/20',
  embedding:      'bg-slate-500/10  text-slate-400  border-slate-500/20',
  test:           'bg-slate-500/10  text-slate-400  border-slate-500/20',
};

export default function LLMPolicies() {
  const [policies,     setPolicies]     = useState<LLMPolicy[]>([]);
  const [models,       setModels]       = useState<RouterModel[]>([]);
  const [loading,      setLoading]      = useState(true);
  const [error,        setError]        = useState('');
  const [filterTask,   setFilterTask]   = useState('');
  const [showCreate,   setShowCreate]   = useState(false);
  const [editTarget,   setEditTarget]   = useState<LLMPolicy | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<LLMPolicy | null>(null);
  const [deleting,     setDeleting]     = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [p, m] = await Promise.all([getPolicies(), getActiveModels()]);
      setPolicies(p);
      setModels(m);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar políticas');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleToggle(policy: LLMPolicy) {
    try {
      await updatePolicy(policy.id, { is_active: !policy.is_active });
      setPolicies((prev) =>
        prev.map((p) => p.id === policy.id ? { ...p, is_active: !p.is_active } : p)
      );
    } catch {}
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deletePolicy(deleteTarget.id);
      setPolicies((prev) => prev.filter((p) => p.id !== deleteTarget.id));
      setDeleteTarget(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao excluir');
    } finally {
      setDeleting(false);
    }
  }

  const filtered = filterTask ? policies.filter((p) => p.task_type === filterTask) : policies;

  const activeCount   = policies.filter((p) =>  p.is_active).length;
  const inactiveCount = policies.filter((p) => !p.is_active).length;
  const taskCoverage  = new Set(policies.filter((p) => p.is_active).map((p) => p.task_type)).size;

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-slate-950 overflow-auto">
      {/* Header */}
      <div className="px-8 py-6 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-500/20 flex items-center justify-center">
              <SlidersHorizontal className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h1 className="text-white font-semibold text-lg">Políticas de Roteamento</h1>
              <p className="text-slate-400 text-sm mt-0.5">Configure qual modelo lida com cada tipo de tarefa</p>
            </div>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nova Política
          </button>
        </div>

        {/* Stats */}
        <div className="mt-5 grid grid-cols-3 gap-4 max-w-lg">
          {[
            { label: 'Total de Políticas', value: policies.length },
            { label: 'Ativo',              value: activeCount,   ok: true },
            { label: 'Cobertura de Tarefas', value: `${taskCoverage} tipos` },
          ].map((s) => (
            <div key={s.label} className="bg-slate-900 border border-white/5 rounded-lg px-4 py-3">
              <p className="text-xs text-slate-500 mb-1">{s.label}</p>
              <p className={`text-xl font-bold tabular-nums ${s.ok && activeCount > 0 ? 'text-emerald-400' : 'text-white'}`}>
                {s.value}
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="flex-1 px-8 py-6">
        {/* Info banner */}
        <div className="mb-5 flex items-start gap-2.5 px-4 py-3 rounded-lg bg-blue-500/5 border border-blue-500/15">
          <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
          <p className="text-blue-300/70 text-sm">
            O Roteador LLM verifica essas políticas antes de cada requisição. Para cada <code className="text-blue-300">task_type</code>,
            o roteador escolhe a política ativa com o menor número de prioridade. Se nenhuma política corresponder, o modelo ativo mais barato é usado como fallback.
          </p>
        </div>

        {/* Filters */}
        <div className="mb-4 flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setFilterTask('')}
            className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors
              ${!filterTask ? 'bg-white text-slate-900 border-white' : 'bg-transparent text-slate-400 border-white/10 hover:border-white/20'}`}
          >
            All ({policies.length})
          </button>
          {TASK_TYPES.map((t) => {
            const count = policies.filter((p) => p.task_type === t).length;
            if (count === 0) return null;
            return (
              <button
                key={t}
                onClick={() => setFilterTask(t)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors
                  ${filterTask === t
                    ? (TASK_COLORS[t] ?? 'bg-slate-700 text-slate-300 border-white/20')
                    : 'bg-transparent text-slate-400 border-white/10 hover:border-white/20'}`}
              >
                {t} ({count})
              </button>
            );
          })}
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Table */}
        <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
            </div>
          ) : (
            <LLMPoliciesTable
              policies={filtered}
              onEdit={setEditTarget}
              onToggle={handleToggle}
              onDelete={setDeleteTarget}
            />
          )}
        </div>

        {/* inactive count note */}
        {inactiveCount > 0 && !filterTask && (
          <p className="mt-3 text-xs text-slate-600 text-center">
            {inactiveCount} {inactiveCount === 1 ? 'política inativa está' : 'políticas inativas estão'} esmaecida(s) — são ignoradas pelo roteador
          </p>
        )}
      </div>

      {/* Modals */}
      {showCreate && (
        <LLMPolicyCreateModal
          models={models}
          onSaved={() => { setShowCreate(false); load(); }}
          onClose={() => setShowCreate(false)}
        />
      )}

      {editTarget && (
        <LLMPolicyEditModal
          policy={editTarget}
          models={models}
          onSaved={() => { setEditTarget(null); load(); }}
          onClose={() => setEditTarget(null)}
        />
      )}

      {/* Delete confirm */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-sm bg-slate-900 border border-white/10 rounded-2xl shadow-2xl p-6">
            <h3 className="text-white font-semibold mb-2">Excluir Política</h3>
            <p className="text-slate-400 text-sm mb-6">
              Excluir <span className="text-white font-medium">{deleteTarget.policy_name}</span>? Esta ação não pode ser desfeita.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteTarget(null)}
                className="flex-1 py-2.5 rounded-lg border border-white/10 text-slate-400 hover:text-white text-sm font-medium transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-medium transition-colors"
              >
                {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                {deleting ? 'Excluindo…' : 'Excluir'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
