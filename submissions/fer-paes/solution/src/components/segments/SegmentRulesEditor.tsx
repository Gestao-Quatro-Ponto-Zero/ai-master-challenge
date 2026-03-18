import { Sparkles } from 'lucide-react';
import type { SegmentRule } from '../../services/segmentationEngineService';
import { RULE_PRESETS } from '../../services/segmentationEngineService';

interface Props {
  rules:    SegmentRule;
  onChange: (rules: SegmentRule) => void;
}

function NumberField({
  label,
  value,
  onChange,
  min,
  max,
  placeholder,
}: {
  label:       string;
  value:       number | null | undefined;
  onChange:    (v: number | null) => void;
  min?:        number;
  max?:        number;
  placeholder?: string;
}) {
  return (
    <div className="space-y-1">
      <label className="block text-xs font-medium text-gray-600">{label}</label>
      <input
        type="number"
        min={min}
        max={max}
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))}
        placeholder={placeholder ?? '—'}
        className="w-full h-9 px-3 rounded-xl border border-gray-200 text-sm text-gray-700 placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
      />
    </div>
  );
}

function TextField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label:        string;
  value:        string | null | undefined;
  onChange:     (v: string | null) => void;
  placeholder?: string;
}) {
  return (
    <div className="space-y-1">
      <label className="block text-xs font-medium text-gray-600">{label}</label>
      <input
        type="text"
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value || null)}
        placeholder={placeholder}
        className="w-full h-9 px-3 rounded-xl border border-gray-200 text-sm text-gray-700 placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
      />
    </div>
  );
}

export default function SegmentRulesEditor({ rules, onChange }: Props) {
  function set<K extends keyof SegmentRule>(key: K, val: SegmentRule[K]) {
    if (val === null || val === undefined) {
      const { [key]: _removed, ...rest } = rules;
      onChange(rest as SegmentRule);
    } else {
      onChange({ ...rules, [key]: val });
    }
  }

  function applyPreset(preset: { rules: SegmentRule }) {
    onChange(preset.rules);
  }

  const activeCount = Object.values(rules).filter((v) => v !== null && v !== undefined).length;

  return (
    <div className="space-y-4">
      {/* Presets */}
      <div>
        <div className="flex items-center gap-1.5 mb-2">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-xs font-medium text-gray-500">Presets rápidos</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {RULE_PRESETS.map((preset) => (
            <button
              key={preset.label}
              type="button"
              onClick={() => applyPreset(preset)}
              className="px-2.5 py-1 rounded-lg text-xs font-medium bg-amber-50 text-amber-700 border border-amber-100 hover:bg-amber-100 transition-colors"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      <div className="border-t border-gray-100 pt-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-gray-600">Regras do Segmento</span>
          {activeCount > 0 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-600 border border-blue-100">
              {activeCount} ativa{activeCount > 1 ? 's' : ''}
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <NumberField
            label="Sem interação há X dias"
            value={rules.last_interaction_days}
            onChange={(v) => set('last_interaction_days', v)}
            min={1}
            placeholder="Ex: 30"
          />
          <NumberField
            label="Mínimo de mensagens"
            value={rules.min_messages}
            onChange={(v) => set('min_messages', v)}
            min={0}
            placeholder="Ex: 5"
          />
          <NumberField
            label="Mínimo de tickets"
            value={rules.min_tickets}
            onChange={(v) => set('min_tickets', v)}
            min={0}
            placeholder="Ex: 3"
          />
          <NumberField
            label="Score de engajamento mínimo"
            value={rules.min_engagement_score}
            onChange={(v) => set('min_engagement_score', v)}
            min={0}
            max={100}
            placeholder="Ex: 70"
          />
          <NumberField
            label="Score de engajamento máximo"
            value={rules.max_engagement_score}
            onChange={(v) => set('max_engagement_score', v)}
            min={0}
            max={100}
            placeholder="Ex: 30"
          />
          <TextField
            label="Tipo de evento obrigatório"
            value={rules.event_type}
            onChange={(v) => set('event_type', v)}
            placeholder="Ex: campaign_opened"
          />
          <NumberField
            label="Mínimo de eventos desse tipo"
            value={rules.min_events}
            onChange={(v) => set('min_events', v)}
            min={1}
            placeholder="Ex: 1"
          />
        </div>

        {activeCount === 0 && (
          <p className="mt-3 text-xs text-gray-400 italic">
            Sem regras definidas — o segmento incluirá todos os clientes.
          </p>
        )}
      </div>
    </div>
  );
}
