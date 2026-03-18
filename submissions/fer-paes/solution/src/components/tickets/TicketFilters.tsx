import { Search, ChevronDown, SlidersHorizontal } from 'lucide-react';
import type { TicketStatus, TicketPriority, Channel, TicketFilters as TicketFiltersType } from '../../types';
import { STATUS_CONFIG } from './ticketConfig';

interface Props {
  filters: TicketFiltersType;
  search: string;
  channels: Channel[];
  ticketCounts: Record<string, number>;
  totalCount: number;
  onFilterChange: (filters: TicketFiltersType) => void;
  onSearchChange: (s: string) => void;
}

export default function TicketFilters({
  filters,
  search,
  channels,
  ticketCounts,
  totalCount,
  onFilterChange,
  onSearchChange,
}: Props) {
  return (
    <div>
      <div className="flex items-center gap-2 overflow-x-auto pb-0.5">
        <button
          onClick={() => onFilterChange({ ...filters, status: undefined })}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all border ${
            !filters.status
              ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
              : 'text-gray-500 border-transparent hover:text-gray-700 hover:bg-gray-100'
          }`}
        >
          All
          <span
            className={`text-xs px-1.5 py-0.5 rounded-md font-semibold ${
              !filters.status ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-500'
            }`}
          >
            {totalCount}
          </span>
        </button>

        {(Object.keys(STATUS_CONFIG) as TicketStatus[]).map((s) => {
          const cfg = STATUS_CONFIG[s];
          const Icon = cfg.icon;
          const count = ticketCounts[s] || 0;
          const active = filters.status === s;
          return (
            <button
              key={s}
              onClick={() => onFilterChange({ ...filters, status: s })}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all border ${
                active
                  ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                  : 'text-gray-500 border-transparent hover:text-gray-700 hover:bg-gray-100'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {cfg.label}
              <span
                className={`text-xs px-1.5 py-0.5 rounded-md font-semibold ${
                  active ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-500'
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      <div className="flex items-center gap-2.5 mt-3.5 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search tickets, customers..."
            className="w-full pl-8.5 pr-4 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400/30 focus:border-blue-300 transition-all placeholder:text-gray-400 bg-white"
            style={{ paddingLeft: '2rem' }}
          />
        </div>

        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-3.5 h-3.5 text-gray-400 shrink-0" />

          <div className="relative">
            <select
              value={filters.priority || ''}
              onChange={(e) =>
                onFilterChange({ ...filters, priority: (e.target.value as TicketPriority) || undefined })
              }
              className="appearance-none pl-3 pr-7 py-2 rounded-xl border border-gray-200 text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400/30 bg-white cursor-pointer"
            >
              <option value="">All Priorities</option>
              <option value="urgent">Urgent</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-400 pointer-events-none" />
          </div>

          <div className="relative">
            <select
              value={filters.channel_id || ''}
              onChange={(e) =>
                onFilterChange({ ...filters, channel_id: e.target.value || undefined })
              }
              className="appearance-none pl-3 pr-7 py-2 rounded-xl border border-gray-200 text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400/30 bg-white cursor-pointer"
            >
              <option value="">All Channels</option>
              {channels.map((ch) => (
                <option key={ch.id} value={ch.id}>
                  {ch.name}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-400 pointer-events-none" />
          </div>

          <div className="relative">
            <select
              value={filters.assigned_user_id || ''}
              onChange={(e) =>
                onFilterChange({ ...filters, assigned_user_id: e.target.value || undefined })
              }
              className="appearance-none pl-3 pr-7 py-2 rounded-xl border border-gray-200 text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400/30 bg-white cursor-pointer"
            >
              <option value="">All Assigned</option>
              <option value="unassigned">Unassigned</option>
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-400 pointer-events-none" />
          </div>
        </div>
      </div>
    </div>
  );
}
