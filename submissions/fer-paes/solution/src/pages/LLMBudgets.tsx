import { useState, useEffect, useCallback } from 'react';
import { Plus, Loader2, Wallet, Info, AlertTriangle, RotateCcw, ShieldOff } from 'lucide-react';
import {
  getBudgets, deleteBudget, resetBudgetUsage, getActiveBudget,
  isExhausted, isOverAlert,
  type LLMBudget,
} from '../services/budgetManagerService';
import LLMBudgetOverview    from '../components/budget/LLMBudgetOverview';
import LLMBudgetTable       from '../components/budget/LLMBudgetTable';
import LLMBudgetCreateModal from '../components/budget/LLMBudgetCreateModal';
import LLMBudgetEditModal   from '../components/budget/LLMBudgetEditModal';

export default function LLMBudgets() {
  const [budgets,        setBudgets]        = useState<LLMBudget[]>([]);
  const [activeBudget,   setActiveBudget]   = useState<LLMBudget | null>(null);
  const [loading,        setLoading]        = useState(true);
  const [error,          setError]          = useState('');
  const [showCreate,     setShowCreate]     = useState(false);
  const [editTarget,     setEditTarget]     = useState<LLMBudget | null>(null);
  const [deleteTarget,   setDeleteTarget]   = useState<LLMBudget | null>(null);
  const [resetTarget,    setResetTarget]    = useState<LLMBudget | null>(null);
  const [deleting,       setDeleting]       = useState(false);
  const [resetting,      setResetting]      = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [all, active] = await Promise.all([getBudgets(), getActiveBudget()]);
      setBudgets(all);
      setActiveBudget(active);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar orçamentos');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteBudget(deleteTarget.id);
      setDeleteTarget(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao excluir');
    } finally {
      setDeleting(false);
    }
  }

  async function handleReset() {
    if (!resetTarget) return;
    setResetting(true);
    try {
      await resetBudgetUsage(resetTarget.id);
      setResetTarget(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao redefinir');
    } finally {
      setResetting(false);
    }
  }

  const exhaustedCount = budgets.filter((b) => b.is_active && isExhausted(b)).length;
  const alertCount     = budgets.filter((b) => b.is_active && isOverAlert(b) && !isExhausted(b)).length;

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-slate-950 overflow-auto">
      {/* Header */}
      <div className="px-8 py-6 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/20 flex items-center justify-center">
              <Wallet className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-white font-semibold text-lg">Gerenciador de Orçamentos</h1>
              <p className="text-slate-400 text-sm mt-0.5">Controle os gastos LLM e os limites de consumo de tokens</p>
            </div>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            Novo Orçamento
          </button>
        </div>
      </div>

      <div className="flex-1 px-8 py-6 space-y-6">
        {/* Alert banners */}
        {exhaustedCount > 0 && (
          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20">
            <ShieldOff className="w-4 h-4 text-red-400 flex-shrink-0" />
            <p className="text-red-300 text-sm">
              <span className="font-semibold">{exhaustedCount} {exhaustedCount === 1 ? 'orçamento ativo foi esgotado.' : 'orçamentos ativos foram esgotados.'}</span>
              {' '}As requisições LLM correspondentes a esses orçamentos estão bloqueadas. Redefina os contadores ou aumente os limites para restaurar o acesso.
            </p>
          </div>
        )}
        {alertCount > 0 && exhaustedCount === 0 && (
          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
            <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
            <p className="text-amber-300 text-sm">
              <span className="font-semibold">{alertCount} {alertCount === 1 ? 'orçamento está' : 'orçamentos estão'} acima do limite de alerta.</span>
              {' '}Considere aumentar os limites ou redefinir antes do fim do período.
            </p>
          </div>
        )}

        {/* Overview cards — always show active global budget */}
        {!loading && (
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">Período Atual — Orçamento Global</p>
            <LLMBudgetOverview budget={activeBudget} />
          </div>
        )}

        {/* Info */}
        <div className="flex items-start gap-2.5 px-4 py-3 rounded-lg bg-blue-500/5 border border-blue-500/15">
          <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
          <p className="text-blue-300/70 text-sm">
            Toda requisição LLM passa por uma verificação de orçamento antes da execução. Quando o limite de custo ou de tokens de um orçamento ativo é atingido,
            as requisições seguintes são bloqueadas e retornam um erro. Redefina os contadores manualmente ou crie um novo orçamento para o próximo período.
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">{error}</div>
        )}

        {/* All budgets table */}
        <div>
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">Todos os Orçamentos</p>
          <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
            {loading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
              </div>
            ) : (
              <LLMBudgetTable
                budgets={budgets}
                onEdit={setEditTarget}
                onDelete={setDeleteTarget}
                onReset={setResetTarget}
              />
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      {showCreate && (
        <LLMBudgetCreateModal
          onSaved={() => { setShowCreate(false); load(); }}
          onClose={() => setShowCreate(false)}
        />
      )}

      {editTarget && (
        <LLMBudgetEditModal
          budget={editTarget}
          onSaved={() => { setEditTarget(null); load(); }}
          onClose={() => setEditTarget(null)}
        />
      )}

      {/* Delete confirm */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-sm bg-slate-900 border border-white/10 rounded-2xl shadow-2xl p-6">
            <h3 className="text-white font-semibold mb-2">Excluir Orçamento</h3>
            <p className="text-slate-400 text-sm mb-6">
              Excluir <span className="text-white font-medium">{deleteTarget.name}</span>? Esta ação não pode ser desfeita e removerá todo o rastreamento de gastos deste período.
            </p>
            <div className="flex gap-3">
              <button onClick={() => setDeleteTarget(null)} className="flex-1 py-2.5 rounded-lg border border-white/10 text-slate-400 hover:text-white text-sm font-medium transition-colors">Cancelar</button>
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

      {/* Reset confirm */}
      {resetTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-sm bg-slate-900 border border-white/10 rounded-2xl shadow-2xl p-6">
            <div className="flex items-center gap-2.5 mb-3">
              <RotateCcw className="w-4 h-4 text-amber-400" />
              <h3 className="text-white font-semibold">Redefinir Contadores de Uso</h3>
            </div>
            <p className="text-slate-400 text-sm mb-6">
              Redefinir os contadores de gasto e tokens de <span className="text-white font-medium">{resetTarget.name}</span> para zero?
              Isso vai reativar as requisições bloqueadas caso o orçamento tenha sido esgotado.
            </p>
            <div className="flex gap-3">
              <button onClick={() => setResetTarget(null)} className="flex-1 py-2.5 rounded-lg border border-white/10 text-slate-400 hover:text-white text-sm font-medium transition-colors">Cancelar</button>
              <button
                onClick={handleReset}
                disabled={resetting}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-sm font-medium transition-colors"
              >
                {resetting ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />}
                {resetting ? 'Redefinindo…' : 'Redefinir Contadores'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
