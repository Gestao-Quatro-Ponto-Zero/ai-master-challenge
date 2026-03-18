import { useState, useEffect } from 'react';
import { X, Loader2, Megaphone, ChevronDown, Info } from 'lucide-react';
import {
  createCampaign,
  CHANNEL_META,
  TEMPLATE_VARS,
  type CreateCampaignInput,
  type CampaignChannel,
} from '../../services/campaignService';
import { getSegments, type CustomerSegment } from '../../services/segmentationEngineService';

interface Props {
  onClose:   () => void;
  onCreated: (id: string) => void;
}

const CHANNELS: CampaignChannel[] = ['email', 'whatsapp', 'chat', 'sms'];

export default function CampaignCreateModal({ onClose, onCreated }: Props) {
  const [name,       setName]       = useState('');
  const [description,setDescription]= useState('');
  const [segmentId,  setSegmentId]  = useState('');
  const [channel,    setChannel]    = useState<CampaignChannel>('email');
  const [template,   setTemplate]   = useState('');
  const [scheduledAt,setScheduledAt]= useState('');
  const [segments,   setSegments]   = useState<CustomerSegment[]>([]);
  const [saving,     setSaving]     = useState(false);
  const [error,      setError]      = useState('');

  useEffect(() => {
    getSegments()
      .then((s) => setSegments(s.filter((sg) => sg.is_active)))
      .catch(() => {});
  }, []);

  function insertVar(v: string) {
    setTemplate((prev) => prev + v);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim())      { setError('Nome é obrigatório.');               return; }
    if (!segmentId)        { setError('Selecione um segmento.');            return; }
    if (!template.trim())  { setError('Template de mensagem é obrigatório.'); return; }
    setSaving(true); setError('');
    try {
      const input: CreateCampaignInput = {
        name:             name.trim(),
        description:      description.trim(),
        segment_id:       segmentId,
        channel,
        message_template: template.trim(),
        scheduled_at:     scheduledAt || null,
      };
      const id = await createCampaign(input);
      onCreated(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar campanha.');
    } finally {
      setSaving(false);
    }
  }

  const selectedSeg = segments.find((s) => s.id === segmentId);

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
              <Megaphone className="w-4 h-4 text-blue-600" />
            </div>
            <h2 className="text-base font-semibold text-gray-900">Nova Campanha</h2>
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

          {/* Name + Description */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="block text-xs font-medium text-gray-600">
                Nome da campanha <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ex: Reativação de Clientes"
                className="w-full h-9 px-3 rounded-xl border border-gray-200 text-sm text-gray-700 placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
              />
            </div>
            <div className="space-y-1">
              <label className="block text-xs font-medium text-gray-600">Descrição</label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Objetivo da campanha..."
                className="w-full h-9 px-3 rounded-xl border border-gray-200 text-sm text-gray-700 placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
              />
            </div>
          </div>

          {/* Segment + Channel */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="block text-xs font-medium text-gray-600">
                Segmento <span className="text-red-400">*</span>
              </label>
              <div className="relative">
                <select
                  value={segmentId}
                  onChange={(e) => setSegmentId(e.target.value)}
                  className="w-full h-9 pl-3 pr-8 rounded-xl border border-gray-200 text-sm text-gray-700 bg-white appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
                >
                  <option value="">Selecione um segmento</option>
                  {segments.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.segment_name} ({s.member_count} membros)
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
              </div>
              {selectedSeg && (
                <p className="text-xs text-gray-400 flex items-center gap-1">
                  <Info className="w-3 h-3" />
                  {selectedSeg.member_count.toLocaleString('pt-BR')} clientes serão impactados
                </p>
              )}
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-medium text-gray-600">Canal</label>
              <div className="grid grid-cols-4 gap-1.5">
                {CHANNELS.map((ch) => {
                  const meta = CHANNEL_META[ch];
                  const active = channel === ch;
                  return (
                    <button
                      key={ch}
                      type="button"
                      onClick={() => setChannel(ch)}
                      className={`py-2 rounded-xl text-xs font-medium border transition-all ${
                        active
                          ? `${meta.bg} ${meta.color} ${meta.border} shadow-sm`
                          : 'bg-gray-50 text-gray-400 border-gray-100 hover:bg-gray-100'
                      }`}
                    >
                      {meta.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Schedule */}
          <div className="space-y-1">
            <label className="block text-xs font-medium text-gray-600">Agendamento (opcional)</label>
            <input
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              className="w-full h-9 px-3 rounded-xl border border-gray-200 text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
            />
          </div>

          {/* Template */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-medium text-gray-600">
                Template da mensagem <span className="text-red-400">*</span>
              </label>
              <div className="flex flex-wrap gap-1">
                {TEMPLATE_VARS.map((v) => (
                  <button
                    key={v}
                    type="button"
                    onClick={() => insertVar(v)}
                    className="px-2 py-0.5 rounded-lg text-xs font-mono bg-gray-100 text-gray-500 hover:bg-blue-50 hover:text-blue-600 transition-colors border border-gray-100"
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>
            <textarea
              value={template}
              onChange={(e) => setTemplate(e.target.value)}
              rows={5}
              placeholder={`Ex: Olá {{customer_name}}, sentimos sua falta!\nVolte a conversar conosco sempre que precisar.`}
              className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-700 placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all font-mono resize-none"
            />
            {template && (
              <div className="px-3 py-2.5 bg-gray-50 rounded-xl border border-gray-100">
                <p className="text-xs font-medium text-gray-400 mb-1">Preview</p>
                <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                  {template
                    .replace('{{customer_name}}', 'João Silva')
                    .replace('{{customer_email}}', 'joao@email.com')
                    .replace('{{last_ticket_date}}', '10/03/2026')
                    .replace('{{company_name}}', 'Sua Empresa')
                    .replace('{{support_link}}', 'https://support.empresa.com')}
                </p>
              </div>
            )}
          </div>

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
              Criar Campanha
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
