import { useState, useEffect, useCallback } from 'react';
import { Plus, Zap, Loader2, Pencil, Trash2, RefreshCw, X, ChevronDown } from 'lucide-react';
import { getMacros, createMacro, updateMacro, deleteMacro } from '../services/macroService';
import type { Macro } from '../types';

const VARIABLE_CHIPS = ['{{customer_name}}', '{{ticket_id}}', '{{agent_name}}'];

const CATEGORY_OPTIONS = ['Greetings', 'Closing', 'Billing', 'Technical', 'General'];

interface EditorProps {
  macro: Macro | null;
  onClose: () => void;
  onSaved: () => void;
}

function MacroEditor({ macro, onClose, onSaved }: EditorProps) {
  const [name, setName] = useState(macro?.name ?? '');
  const [content, setContent] = useState(macro?.content ?? '');
  const [category, setCategory] = useState(macro?.category ?? 'General');
  const [saving, setSaving] = useState(false);

  function insertVariable(v: string) {
    const el = document.querySelector<HTMLTextAreaElement>('#macro-content');
    if (!el) {
      setContent((c) => c + v);
      return;
    }
    const start = el.selectionStart ?? content.length;
    const end = el.selectionEnd ?? start;
    const newContent = content.slice(0, start) + v + content.slice(end);
    setContent(newContent);
    setTimeout(() => {
      el.focus();
      el.setSelectionRange(start + v.length, start + v.length);
    }, 0);
  }

  async function handleSave() {
    if (!name.trim() || !content.trim()) return;
    setSaving(true);
    try {
      if (macro) {
        await updateMacro(macro.id, { name: name.trim(), content: content.trim(), category });
      } else {
        await createMacro({ name: name.trim(), content: content.trim(), category });
      }
      onSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0,0,0,0.4)' }}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg flex flex-col overflow-hidden max-h-[90vh]">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-emerald-100 flex items-center justify-center">
              <Zap className="w-3.5 h-3.5 text-emerald-600" />
            </div>
            <h2 className="text-sm font-semibold text-gray-900">
              {macro ? 'Editar Macro' : 'Nova Macro'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 px-6 py-5 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-1.5">Nome</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="ex: Saudação"
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-1.5">Categoria</label>
              <div className="relative">
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full appearance-none px-3 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 pr-8 bg-white"
                >
                  {CATEGORY_OPTIONS.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
                <ChevronDown className="w-3.5 h-3.5 text-gray-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-gray-500">Conteúdo</label>
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] text-gray-400">Inserir variável:</span>
                {VARIABLE_CHIPS.map((v) => (
                  <button
                    key={v}
                    onClick={() => insertVariable(v)}
                    className="px-2 py-0.5 text-[10px] font-mono bg-amber-50 text-amber-700 border border-amber-200 rounded-md hover:bg-amber-100 transition-colors"
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>
            <textarea
              id="macro-content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={5}
              placeholder="Olá {{customer_name}}, obrigado por entrar em contato..."
              className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 resize-none leading-relaxed"
            />
            <p className="text-[11px] text-gray-400 mt-1">
              Variáveis: <code className="font-mono bg-gray-100 px-1 rounded">{'{{customer_name}}'}</code>, <code className="font-mono bg-gray-100 px-1 rounded">{'{{ticket_id}}'}</code>, <code className="font-mono bg-gray-100 px-1 rounded">{'{{agent_name}}'}</code>
            </p>
          </div>
        </div>

        <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-end gap-3 shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            disabled={!name.trim() || !content.trim() || saving}
            onClick={handleSave}
            className="px-4 py-2 text-sm rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            {saving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            {macro ? 'Salvar Alterações' : 'Criar Macro'}
          </button>
        </div>
      </div>
    </div>
  );
}

function MacroCard({ macro, onEdit, onDelete }: { macro: Macro; onEdit: () => void; onDelete: () => void }) {
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    if (!confirm(`Excluir macro "${macro.name}"?`)) return;
    setDeleting(true);
    try {
      await deleteMacro(macro.id);
      onDelete();
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow p-5">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0 mt-0.5">
          <Zap className="w-4 h-4 text-emerald-600" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold text-gray-900">{macro.name}</h3>
            {macro.category && (
              <span className="text-[10px] font-semibold text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
                {macro.category}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500 leading-relaxed line-clamp-3">
            {macro.content}
          </p>
          <div className="flex flex-wrap gap-1 mt-2">
            {Array.from(macro.content.matchAll(/\{\{(\w+)\}\}/g)).map((m, i) => (
              <span key={i} className="text-[10px] font-mono bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded">
                {'{{'}{m[1]}{'}}'}
              </span>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <button
            onClick={onEdit}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
            title="Editar"
          >
            <Pencil className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors disabled:opacity-40"
            title="Excluir"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Macros() {
  const [macros, setMacros] = useState<Macro[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<Macro | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setMacros(await getMacros());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  function openNew() { setEditTarget(null); setModalOpen(true); }
  function openEdit(m: Macro) { setEditTarget(m); setModalOpen(true); }
  function closeModal() { setModalOpen(false); setEditTarget(null); }
  async function handleSaved() { closeModal(); await load(); }

  const grouped = macros.reduce<Record<string, Macro[]>>((acc, m) => {
    const cat = m.category || 'General';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(m);
    return acc;
  }, {});

  return (
    <div className="flex flex-col h-full bg-gray-50/30">
      <div className="px-8 py-6 bg-white border-b border-gray-100 flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Macros</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Modelos de resposta rápida para operadores — digite <code className="font-mono text-blue-600 bg-blue-50 px-1 rounded">/</code> em qualquer mensagem para usá-los
          </p>
        </div>
        <div className="flex items-center gap-3">
          {!loading && macros.length > 0 && (
            <span className="text-xs text-gray-500 font-medium">{macros.length} macro{macros.length !== 1 ? 's' : ''}</span>
          )}
          <button
            onClick={load}
            disabled={loading}
            className="w-8 h-8 flex items-center justify-center rounded-xl text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={openNew}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition-colors shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            Nova Macro
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto px-8 py-6">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="w-6 h-6 animate-spin text-gray-300" />
          </div>
        ) : macros.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 rounded-2xl bg-emerald-50 flex items-center justify-center mb-4">
              <Zap className="w-8 h-8 text-emerald-300" />
            </div>
            <h3 className="text-gray-700 font-semibold text-lg mb-1">Nenhuma macro encontrada</h3>
            <p className="text-gray-400 text-sm max-w-xs">
              Crie modelos para respostas comuns. Os operadores podem inseri-los digitando <code className="font-mono">/</code> no chat.
            </p>
            <button
              onClick={openNew}
              className="mt-5 inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              Criar sua primeira macro
            </button>
          </div>
        ) : (
          <div className="space-y-8 max-w-3xl">
            {Object.entries(grouped).map(([cat, items]) => (
              <div key={cat}>
                <h2 className="text-xs font-bold text-gray-400 uppercase tracking-wide mb-3">{cat}</h2>
                <div className="grid grid-cols-1 gap-3">
                  {items.map((m) => (
                    <MacroCard
                      key={m.id}
                      macro={m}
                      onEdit={() => openEdit(m)}
                      onDelete={load}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {modalOpen && (
        <MacroEditor macro={editTarget} onClose={closeModal} onSaved={handleSaved} />
      )}
    </div>
  );
}
