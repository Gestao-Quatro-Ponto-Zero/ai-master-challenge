import { Search, SlidersHorizontal, X } from 'lucide-react';
import { EVENT_TYPES, EVENT_SOURCES, eventTypeLabel, sourceLabel } from '../../services/eventTrackingService';
import type { EventFilters } from '../../services/eventTrackingService';

interface Props {
  filters:   EventFilters;
  onChange:  (filters: EventFilters) => void;
}

function Select({
  value,
  onChange,
  placeholder,
  options,
}: {
  value:       string;
  onChange:    (v: string) => void;
  placeholder: string;
  options:     { value: string; label: string }[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="h-9 px-3 rounded-xl border border-gray-200 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
    >
      <option value="">{placeholder}</option>
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}

function DateInput({
  value,
  onChange,
  placeholder,
}: {
  value:       string;
  onChange:    (v: string) => void;
  placeholder: string;
}) {
  return (
    <input
      type="datetime-local"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="h-9 px-3 rounded-xl border border-gray-200 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
    />
  );
}

const EVENT_TYPE_OPTIONS = EVENT_TYPES.map((t) => ({ value: t, label: eventTypeLabel(t) }));
const SOURCE_OPTIONS      = EVENT_SOURCES.map((s) => ({ value: s, label: sourceLabel(s) }));

export default function EventsFilters({ filters, onChange }: Props) {
  const hasActiveFilters =
    !!filters.search    ||
    !!filters.eventType ||
    !!filters.source    ||
    !!filters.dateFrom  ||
    !!filters.dateTo;

  function clear() {
    onChange({ limit: filters.limit, offset: 0 });
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 px-4 py-3">
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex items-center gap-1.5 text-xs font-medium text-gray-400 mr-1">
          <SlidersHorizontal className="w-3.5 h-3.5" />
          Filtros
        </div>

        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
          <input
            type="text"
            value={filters.search ?? ''}
            onChange={(e) => onChange({ ...filters, search: e.target.value, offset: 0 })}
            placeholder="Buscar por cliente, tipo ou origem..."
            className="w-full h-9 pl-8 pr-3 rounded-xl border border-gray-200 text-sm text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
          />
        </div>

        <Select
          value={filters.eventType ?? ''}
          onChange={(v) => onChange({ ...filters, eventType: v || null, offset: 0 })}
          placeholder="Tipo de evento"
          options={EVENT_TYPE_OPTIONS}
        />

        <Select
          value={filters.source ?? ''}
          onChange={(v) => onChange({ ...filters, source: v || null, offset: 0 })}
          placeholder="Origem"
          options={SOURCE_OPTIONS}
        />

        <DateInput
          value={filters.dateFrom ?? ''}
          onChange={(v) => onChange({ ...filters, dateFrom: v ? new Date(v).toISOString() : null, offset: 0 })}
          placeholder="De"
        />

        <DateInput
          value={filters.dateTo ?? ''}
          onChange={(v) => onChange({ ...filters, dateTo: v ? new Date(v).toISOString() : null, offset: 0 })}
          placeholder="Até"
        />

        {hasActiveFilters && (
          <button
            onClick={clear}
            className="flex items-center gap-1 h-9 px-3 rounded-xl text-xs font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100 border border-gray-200 transition-colors"
          >
            <X className="w-3 h-3" />
            Limpar
          </button>
        )}
      </div>
    </div>
  );
}
