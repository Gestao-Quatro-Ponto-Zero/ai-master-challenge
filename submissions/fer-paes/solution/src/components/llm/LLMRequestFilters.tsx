import { Search, Filter } from 'lucide-react';
import type { LLMRequestFilters, LLMModel, LLMRequestStatus } from '../../types';

const STATUS_OPTIONS: { value: LLMRequestStatus | ''; label: string }[] = [
  { value: '',        label: 'All Status'  },
  { value: 'success', label: 'Success'     },
  { value: 'pending', label: 'Pending'     },
  { value: 'error',   label: 'Error'       },
  { value: 'timeout', label: 'Timeout'     },
];

const PROVIDER_OPTIONS = [
  { value: '',          label: 'All Providers' },
  { value: 'openai',    label: 'OpenAI'        },
  { value: 'anthropic', label: 'Anthropic'     },
  { value: 'google',    label: 'Google'        },
  { value: 'mistral',   label: 'Mistral'       },
];

interface Props {
  filters: LLMRequestFilters;
  search: string;
  models: LLMModel[];
  onChange: (filters: LLMRequestFilters) => void;
  onSearchChange: (v: string) => void;
}

export default function LLMRequestFiltersBar({ filters, search, models, onChange, onSearchChange }: Props) {
  function set<K extends keyof LLMRequestFilters>(key: K, value: LLMRequestFilters[K]) {
    onChange({ ...filters, [key]: value || undefined });
  }

  return (
    <div className="px-8 py-3 border-b border-white/5 flex items-center gap-3 flex-wrap bg-slate-950">
      <div className="relative flex-1 min-w-48">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input
          type="text"
          placeholder="Search by model or provider..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-white/10 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
        />
      </div>

      <div className="flex items-center gap-1.5">
        <Filter className="w-3.5 h-3.5 text-slate-500" />
        <span className="text-xs text-slate-500 font-medium">Filters:</span>
      </div>

      <select
        value={filters.provider ?? ''}
        onChange={(e) => set('provider', e.target.value)}
        className="bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
      >
        {PROVIDER_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>

      <select
        value={filters.model_id ?? ''}
        onChange={(e) => set('model_id', e.target.value)}
        className="bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
      >
        <option value="">All Models</option>
        {models.map((m) => (
          <option key={m.id} value={m.id}>{m.name}</option>
        ))}
      </select>

      <select
        value={filters.status ?? ''}
        onChange={(e) => set('status', e.target.value as LLMRequestStatus)}
        className="bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
      >
        {STATUS_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>

      <div className="flex items-center gap-2">
        <input
          type="date"
          value={filters.from ? filters.from.slice(0, 10) : ''}
          onChange={(e) => set('from', e.target.value ? `${e.target.value}T00:00:00Z` : undefined)}
          className="bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
        />
        <span className="text-slate-600 text-xs">to</span>
        <input
          type="date"
          value={filters.to ? filters.to.slice(0, 10) : ''}
          onChange={(e) => set('to', e.target.value ? `${e.target.value}T23:59:59Z` : undefined)}
          className="bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
        />
      </div>
    </div>
  );
}
