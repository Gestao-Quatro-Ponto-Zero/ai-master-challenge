import { Loader2, Activity, ChevronLeft, ChevronRight, User } from 'lucide-react';
import type { CustomerEvent } from '../../services/eventTrackingService';
import { eventTypeLabel, eventTypeColor, sourceLabel, formatEventDate } from '../../services/eventTrackingService';

interface Props {
  events:      CustomerEvent[];
  loading:     boolean;
  totalCount:  number;
  limit:       number;
  offset:      number;
  onPageChange:(offset: number) => void;
  onSelect:    (event: CustomerEvent) => void;
  selectedId?: string;
}

function EventTypeBadge({ type }: { type: string }) {
  const { bg, text, border } = eventTypeColor(type);
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${bg} ${text} ${border} whitespace-nowrap`}>
      {eventTypeLabel(type)}
    </span>
  );
}

function SourceBadge({ source }: { source: string }) {
  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-50 text-gray-500 border border-gray-100 whitespace-nowrap">
      {sourceLabel(source)}
    </span>
  );
}

export default function EventsTable({
  events,
  loading,
  totalCount,
  limit,
  offset,
  onPageChange,
  onSelect,
  selectedId,
}: Props) {
  const totalPages   = Math.ceil(totalCount / limit);
  const currentPage  = Math.floor(offset / limit) + 1;
  const startItem    = offset + 1;
  const endItem      = Math.min(offset + events.length, totalCount);

  if (loading && events.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 flex items-center justify-center py-24">
        <Loader2 className="w-5 h-5 text-gray-300 animate-spin" />
      </div>
    );
  }

  if (!loading && events.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 flex flex-col items-center justify-center py-24 gap-3">
        <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center">
          <Activity className="w-6 h-6 text-gray-300" />
        </div>
        <p className="text-sm text-gray-400">Nenhum evento encontrado</p>
        <p className="text-xs text-gray-300">Ajuste os filtros ou aguarde novos eventos</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden flex flex-col">
      <div className="overflow-x-auto flex-1">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100">
              {['Tipo de Evento', 'Cliente', 'Origem', 'Dados', 'Data / Hora'].map((h) => (
                <th
                  key={h}
                  className="text-left px-5 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider whitespace-nowrap"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {events.map((ev) => {
              const isSelected = ev.id === selectedId;
              const dataKeys   = Object.keys(ev.event_data ?? {}).slice(0, 2);
              return (
                <tr
                  key={ev.id}
                  onClick={() => onSelect(ev)}
                  className={`cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-blue-50/60 hover:bg-blue-50/80'
                      : 'hover:bg-gray-50/50'
                  }`}
                >
                  <td className="px-5 py-3.5">
                    <EventTypeBadge type={ev.event_type} />
                  </td>
                  <td className="px-5 py-3.5">
                    {ev.customer_id ? (
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-blue-50 flex items-center justify-center shrink-0">
                          <User className="w-3 h-3 text-blue-400" />
                        </div>
                        <div>
                          <p className="text-sm text-gray-800 font-medium">
                            {ev.customer_name ?? 'Desconhecido'}
                          </p>
                          {ev.customer_email && (
                            <p className="text-xs text-gray-400 truncate max-w-[160px]">{ev.customer_email}</p>
                          )}
                        </div>
                      </div>
                    ) : (
                      <span className="text-xs text-gray-400 italic">Sistema</span>
                    )}
                  </td>
                  <td className="px-5 py-3.5">
                    <SourceBadge source={ev.source} />
                  </td>
                  <td className="px-5 py-3.5">
                    {dataKeys.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {dataKeys.map((k) => (
                          <span
                            key={k}
                            className="inline-flex items-center px-1.5 py-0.5 rounded bg-gray-100 text-xs text-gray-500 font-mono"
                          >
                            {k}
                          </span>
                        ))}
                        {Object.keys(ev.event_data ?? {}).length > 2 && (
                          <span className="text-xs text-gray-400">
                            +{Object.keys(ev.event_data).length - 2}
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-xs text-gray-300">—</span>
                    )}
                  </td>
                  <td className="px-5 py-3.5 text-sm text-gray-500 whitespace-nowrap tabular-nums">
                    {formatEventDate(ev.created_at)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalCount > 0 && (
        <div className="flex items-center justify-between px-5 py-3 border-t border-gray-100">
          <p className="text-xs text-gray-400">
            {startItem}–{endItem} de {totalCount.toLocaleString('pt-BR')} eventos
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => onPageChange(Math.max(0, offset - limit))}
              disabled={currentPage <= 1 || loading}
              className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-xs text-gray-500 px-2">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => onPageChange(offset + limit)}
              disabled={currentPage >= totalPages || loading}
              className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
