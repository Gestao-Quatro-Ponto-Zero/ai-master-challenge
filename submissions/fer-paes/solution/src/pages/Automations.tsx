import { useState, useEffect, useCallback } from 'react';
import { Plus, Zap, Loader2, RefreshCw } from 'lucide-react';
import { getRules } from '../services/automationService';
import RuleCard from '../components/automations/RuleCard';
import RuleEditorModal from '../components/automations/RuleEditorModal';
import type { AutomationRule } from '../types';

export default function Automations() {
  const [rules, setRules] = useState<AutomationRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<AutomationRule | null | 'new'>('init' as never);
  const [modalOpen, setModalOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<AutomationRule | null>(null);

  const loadRules = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getRules();
      setRules(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRules();
  }, [loadRules]);

  function openNew() {
    setEditTarget(null);
    setModalOpen(true);
  }

  function openEdit(rule: AutomationRule) {
    setEditTarget(rule);
    setModalOpen(true);
  }

  function closeModal() {
    setModalOpen(false);
    setEditTarget(null);
  }

  async function handleSaved() {
    closeModal();
    await loadRules();
  }

  const active = rules.filter((r) => r.is_active).length;
  const total = rules.length;

  return (
    <div className="flex flex-col h-full bg-gray-50/30">
      <div className="px-8 py-6 bg-white border-b border-gray-100 flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Automações</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Regras que são executadas automaticamente em eventos de ticket
          </p>
        </div>
        <div className="flex items-center gap-3">
          {!loading && total > 0 && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded-xl border border-gray-200">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-xs text-gray-600 font-medium">
                {active}/{total} ativas
              </span>
            </div>
          )}
          <button
            onClick={loadRules}
            disabled={loading}
            className="w-8 h-8 flex items-center justify-center rounded-xl text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors disabled:opacity-50"
            title="Atualizar"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={openNew}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition-colors shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            Nova Regra
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto px-8 py-6">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="w-6 h-6 animate-spin text-gray-300" />
          </div>
        ) : rules.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center mb-4">
              <Zap className="w-8 h-8 text-blue-300" />
            </div>
            <h3 className="text-gray-700 font-semibold text-lg mb-1">Nenhuma automação encontrada</h3>
            <p className="text-gray-400 text-sm max-w-xs">
              Crie regras para atribuir, etiquetar ou atualizar tickets automaticamente com base em eventos.
            </p>
            <button
              onClick={openNew}
              className="mt-5 inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              Criar sua primeira regra
            </button>
          </div>
        ) : (
          <div className="space-y-3 max-w-2xl">
            {rules.map((rule) => (
              <RuleCard
                key={rule.id}
                rule={rule}
                onChange={loadRules}
                onEdit={openEdit}
              />
            ))}
          </div>
        )}
      </div>

      {modalOpen && (
        <RuleEditorModal
          rule={editTarget}
          onClose={closeModal}
          onSaved={handleSaved}
        />
      )}
    </div>
  );
}
