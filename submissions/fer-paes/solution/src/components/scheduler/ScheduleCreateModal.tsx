import { useState, useEffect } from 'react';
import { X, Clock, Loader2, ChevronDown, CalendarClock, RefreshCw, Zap } from 'lucide-react';
import {
  createSchedule,
  SCHEDULE_TYPE_META,
  EVENT_TYPES,
  CRON_PRESETS,
  type ScheduleType,
  type CreateScheduleInput,
} from '../../services/campaignSchedulerService';
import { getCampaigns, type Campaign } from '../../services/campaignService';

interface Props {
  onClose:   () => void;
  onCreated: (id: string) => void;
  campaignId?: string;
}

const TYPE_ICONS: Record<ScheduleType, React.ComponentType<{ className?: string }>> = {
  once:            CalendarClock,
  recurring:       RefreshCw,
  event_triggered: Zap,
};

const TYPES: ScheduleType[] = ['once', 'recurring', 'event_triggered'];

export default function ScheduleCreateModal({ onClose, onCreated, campaignId }: Props) {
  const [campaigns,    setCampaigns]    = useState<Campaign[]>([]);
  const [selCampaign,  setSelCampaign]  = useState(campaignId ?? '');
  const [type,         setType]         = useState<ScheduleType>('once');
  const [runAt,        setRunAt]        = useState('');
  const [cronExpr,     setCronExpr]     = useState('');
  const [cronPreset,   setCronPreset]   = useState('');
  const [eventType,    setEventType]    = useState('');
  const [saving,       setSaving]       = useState(false);
  const [error,        setError]        = useState('');

  useEffect(() => {
    getCampaigns()
      .then((cs) => setCampaigns(cs.filter((c) => c.status === 'scheduled' || c.status === 'draft')))
      .catch(() => {});
  }, []);

  function handlePreset(val: string) {
    setCronPreset(val);
    setCronExpr(val);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selCampaign)                            { setError('Selecione uma campanha.');          return; }
    if (type === 'once' && !runAt)               { setError('Informe a data/hora de execução.'); return; }
    if (type === 'recurring' && !cronExpr.trim()){ setError('Informe a expressão cron.');        return; }
    if (type === 'event_triggered' && !eventType){ setError('Selecione o evento disparador.');   return; }

    setSaving(true); setError('');
    try {
      const input: CreateScheduleInput = {
        campaign_id:     selCampaign,
        schedule_type:   type,
        run_at:          type === 'once' ? runAt : null,
        cron_expression: type === 'recurring' ? cronExpr.trim() : null,
        event_type:      type === 'event_triggered' ? eventType : null,
        next_run_at:     type === 'once' ? runAt : null,
      };
      const id = await createSchedule(input);
      onCreated(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar agendamento.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
              <Clock className="w-4 h-4 text-blue-600" />
            </div>
            <h2 className="text-base font-semibold text-gray-900">Novo Agendamento</h2>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
          {error && (
            <div className="px-3 py-2 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm">
              {error}
            </div>
          )}

          {/* Campaign */}
          {!campaignId && (
            <div className="space-y-1">
              <label className="block text-xs font-medium text-gray-600">
                Campanha <span className="text-red-400">*</span>
              </label>
              <div className="relative">
                <select
                  value={selCampaign}
                  onChange={(e) => setSelCampaign(e.target.value)}
                  className="w-full h-9 pl-3 pr-8 rounded-xl border border-gray-200 text-sm text-gray-700 bg-white appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
                >
                  <option value="">Selecione uma campanha</option>
                  {campaigns.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
              </div>
            </div>
          )}

          {/* Schedule Type */}
          <div className="space-y-2">
            <label className="block text-xs font-medium text-gray-600">Tipo de agendamento</label>
            <div className="grid grid-cols-3 gap-2">
              {TYPES.map((t) => {
                const meta = SCHEDULE_TYPE_META[t];
                const Icon = TYPE_ICONS[t];
                const active = type === t;
                return (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setType(t)}
                    className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border text-center transition-all ${
                      active
                        ? `${meta.bg} ${meta.color} ${meta.border} shadow-sm`
                        : 'bg-gray-50 text-gray-400 border-gray-100 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="text-xs font-medium leading-tight">{meta.label}</span>
                  </button>
                );
              })}
            </div>
            <p className="text-xs text-gray-400">{SCHEDULE_TYPE_META[type].description}</p>
          </div>

          {/* Once fields */}
          {type === 'once' && (
            <div className="space-y-1">
              <label className="block text-xs font-medium text-gray-600">
                Data e hora de execução <span className="text-red-400">*</span>
              </label>
              <input
                type="datetime-local"
                value={runAt}
                onChange={(e) => setRunAt(e.target.value)}
                className="w-full h-9 px-3 rounded-xl border border-gray-200 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
              />
            </div>
          )}

          {/* Recurring fields */}
          {type === 'recurring' && (
            <div className="space-y-3">
              <div className="space-y-1">
                <label className="block text-xs font-medium text-gray-600">Presets</label>
                <div className="grid grid-cols-1 gap-1">
                  {CRON_PRESETS.map((p) => (
                    <button
                      key={p.value}
                      type="button"
                      onClick={() => handlePreset(p.value)}
                      className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs border transition-all ${
                        cronPreset === p.value
                          ? 'bg-blue-50 text-blue-600 border-blue-100 font-medium'
                          : 'bg-gray-50 text-gray-500 border-gray-100 hover:bg-gray-100'
                      }`}
                    >
                      <span>{p.label}</span>
                      <span className="font-mono text-gray-400">{p.value}</span>
                    </button>
                  ))}
                </div>
              </div>
              <div className="space-y-1">
                <label className="block text-xs font-medium text-gray-600">
                  Expressão cron personalizada <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={cronExpr}
                  onChange={(e) => { setCronExpr(e.target.value); setCronPreset(''); }}
                  placeholder="Ex: 0 9 * * 1"
                  className="w-full h-9 px-3 rounded-xl border border-gray-200 text-sm text-gray-700 font-mono placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
                />
                <p className="text-xs text-gray-400">Formato: minuto hora dia-mês mês dia-semana</p>
              </div>
            </div>
          )}

          {/* Event fields */}
          {type === 'event_triggered' && (
            <div className="space-y-1">
              <label className="block text-xs font-medium text-gray-600">
                Evento disparador <span className="text-red-400">*</span>
              </label>
              <div className="grid grid-cols-1 gap-1.5">
                {EVENT_TYPES.map((ev) => (
                  <button
                    key={ev.value}
                    type="button"
                    onClick={() => setEventType(ev.value)}
                    className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-xs border transition-all text-left ${
                      eventType === ev.value
                        ? 'bg-amber-50 text-amber-700 border-amber-100 font-medium'
                        : 'bg-gray-50 text-gray-500 border-gray-100 hover:bg-gray-100'
                    }`}
                  >
                    <Zap className="w-3 h-3 shrink-0" />
                    {ev.label}
                  </button>
                ))}
              </div>
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
              Criar Agendamento
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
