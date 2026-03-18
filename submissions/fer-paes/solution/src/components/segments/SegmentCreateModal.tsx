import { useState } from 'react';
import { X, Loader2, Layers } from 'lucide-react';
import {
  createSegment,
  type CreateSegmentInput,
  type SegmentRule,
} from '../../services/segmentationEngineService';
import SegmentRulesEditor from './SegmentRulesEditor';

interface Props {
  onClose:   () => void;
  onCreated: (id: string) => void;
}

export default function SegmentCreateModal({ onClose, onCreated }: Props) {
  const [name,        setName]        = useState('');
  const [description, setDescription] = useState('');
  const [rules,       setRules]       = useState<SegmentRule>({});
  const [isDynamic,   setIsDynamic]   = useState(true);
  const [saving,      setSaving]      = useState(false);
  const [error,       setError]       = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) { setError('Nome é obrigatório.'); return; }
    setSaving(true); setError('');
    try {
      const input: CreateSegmentInput = {
        segment_name: name.trim(),
        description:  description.trim(),
        rules,
        is_dynamic:   isDynamic,
      };
      const id = await createSegment(input);
      onCreated(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar segmento.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
              <Layers className="w-4 h-4 text-blue-600" />
            </div>
            <h2 className="text-base font-semibold text-gray-900">Novo Segmento</h2>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
          {error && (
            <div className="px-3 py-2 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm">
              {error}
            </div>
          )}

          <div className="space-y-1">
            <label className="block text-xs font-medium text-gray-600">
              Nome do segmento <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: Clientes inativos 30 dias"
              className="w-full h-9 px-3 rounded-xl border border-gray-200 text-sm text-gray-700 placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
            />
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-medium text-gray-600">Descrição</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Descreva o propósito deste segmento..."
              rows={2}
              className="w-full px-3 py-2 rounded-xl border border-gray-200 text-sm text-gray-700 placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all resize-none"
            />
          </div>

          {/* Type toggle */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-gray-50 border border-gray-100">
            <div>
              <p className="text-sm font-medium text-gray-700">Segmento dinâmico</p>
              <p className="text-xs text-gray-400">
                {isDynamic
                  ? 'Membros recalculados automaticamente pelas regras'
                  : 'Membros adicionados manualmente'}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setIsDynamic(!isDynamic)}
              className={`relative w-10 h-5 rounded-full transition-colors ${
                isDynamic ? 'bg-blue-500' : 'bg-gray-300'
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                  isDynamic ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {isDynamic && (
            <div className="bg-gray-50 rounded-xl border border-gray-100 p-4">
              <SegmentRulesEditor rules={rules} onChange={setRules} />
            </div>
          )}

          {/* Footer */}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-sm text-gray-600 hover:bg-gray-100 border border-gray-200 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-2 px-5 py-2 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-60 transition-colors"
            >
              {saving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              Criar Segmento
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
