import { useState } from 'react';
import { CheckCircle2, CreditCard as Edit3, Save, X } from 'lucide-react';
import { updateResolutionNotes } from '../../services/ticketService';

interface ResolutionPanelProps {
  ticketId: string;
  initialNotes: string | null;
  readonly?: boolean;
  onSaved?: (notes: string) => void;
  compact?: boolean;
}

export default function ResolutionPanel({
  ticketId,
  initialNotes,
  readonly = false,
  onSaved,
  compact = false,
}: ResolutionPanelProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(initialNotes ?? '');
  const [saved, setSaved] = useState(initialNotes ?? '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await updateResolutionNotes(ticketId, draft.trim());
      setSaved(draft.trim());
      setEditing(false);
      onSaved?.(draft.trim());
    } catch {
      setError('Falha ao salvar. Tente novamente.');
    } finally {
      setSaving(false);
    }
  }

  function handleCancel() {
    setDraft(saved);
    setEditing(false);
    setError(null);
  }

  const hasContent = saved.trim().length > 0;

  if (compact) {
    return (
      <section>
        <div className="flex items-center justify-between mb-2.5">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Solução Empregada</p>
          {!readonly && !editing && (
            <button
              onClick={() => setEditing(true)}
              className="text-xs text-blue-500 hover:text-blue-700 flex items-center gap-1 transition-colors"
            >
              <Edit3 className="w-3 h-3" />
              {hasContent ? 'Editar' : 'Registrar'}
            </button>
          )}
        </div>

        {editing ? (
          <div className="space-y-2">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Descreva a solução aplicada para resolver este ticket..."
              rows={4}
              className="w-full text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-emerald-200 focus:border-emerald-300 placeholder:text-gray-400 leading-relaxed"
            />
            {error && <p className="text-xs text-red-500">{error}</p>}
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-xs font-medium hover:bg-emerald-700 transition-colors disabled:opacity-60"
              >
                <Save className="w-3 h-3" />
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
              <button
                onClick={handleCancel}
                disabled={saving}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-100 text-gray-600 text-xs hover:bg-gray-200 transition-colors"
              >
                <X className="w-3 h-3" />
                Cancelar
              </button>
            </div>
          </div>
        ) : hasContent ? (
          <div className="rounded-lg bg-emerald-50 border border-emerald-100 px-3 py-2.5">
            <p className="text-xs text-emerald-800 leading-relaxed whitespace-pre-wrap">{saved}</p>
          </div>
        ) : (
          <p className="text-xs text-gray-400 italic">Nenhuma solução registrada ainda.</p>
        )}
      </section>
    );
  }

  return (
    <div className={`rounded-xl border-2 transition-all ${
      hasContent
        ? 'border-emerald-200 bg-emerald-50/60'
        : 'border-dashed border-gray-200 bg-white'
    }`}>
      <div className="px-4 py-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
            hasContent ? 'bg-emerald-100' : 'bg-gray-100'
          }`}>
            <CheckCircle2 className={`w-4 h-4 ${hasContent ? 'text-emerald-600' : 'text-gray-400'}`} />
          </div>
          <div>
            <p className={`text-sm font-semibold ${hasContent ? 'text-emerald-800' : 'text-gray-600'}`}>
              Solução Empregada
            </p>
            {!hasContent && !editing && (
              <p className="text-xs text-gray-400">Registre a solução aplicada para este ticket</p>
            )}
          </div>
        </div>
        {!readonly && !editing && (
          <button
            onClick={() => setEditing(true)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors shrink-0 ${
              hasContent
                ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Edit3 className="w-3 h-3" />
            {hasContent ? 'Editar' : 'Registrar Solução'}
          </button>
        )}
      </div>

      {(editing || hasContent) && (
        <div className="px-4 pb-4">
          <div className={`h-px mb-3 ${hasContent ? 'bg-emerald-100' : 'bg-gray-100'}`} />

          {editing ? (
            <div className="space-y-3">
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Descreva detalhadamente a solução aplicada para resolver este ticket..."
                rows={5}
                autoFocus
                className="w-full text-sm text-gray-700 bg-white border border-gray-200 rounded-xl px-4 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-emerald-200 focus:border-emerald-300 placeholder:text-gray-400 leading-relaxed"
              />
              {error && <p className="text-sm text-red-500">{error}</p>}
              <div className="flex gap-2">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-60 shadow-sm shadow-emerald-200"
                >
                  <Save className="w-3.5 h-3.5" />
                  {saving ? 'Salvando...' : 'Salvar Solução'}
                </button>
                <button
                  onClick={handleCancel}
                  disabled={saving}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-gray-200 text-gray-600 text-sm hover:bg-gray-50 transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                  Cancelar
                </button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-emerald-800 leading-relaxed whitespace-pre-wrap">{saved}</p>
          )}
        </div>
      )}
    </div>
  );
}
