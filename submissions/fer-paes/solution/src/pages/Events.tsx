import { useState, useEffect, useCallback } from 'react';
import { Activity, RefreshCw, Loader2 } from 'lucide-react';
import {
  getEventsPaginated,
  getEventTypeSummary,
  eventTypeLabel,
  eventTypeColor,
  type CustomerEvent,
  type EventFilters,
  type EventTypeSummary,
} from '../services/eventTrackingService';
import EventsFilters      from '../components/events/EventsFilters';
import EventsTable        from '../components/events/EventsTable';
import EventDetailsPanel  from '../components/events/EventDetailsPanel';

const PAGE_SIZE = 50;

function SummaryCard({ item }: { item: EventTypeSummary }) {
  const { bg, text, border } = eventTypeColor(item.event_type);
  return (
    <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${bg} ${border}`}>
      <div className="flex-1 min-w-0">
        <p className={`text-xs font-semibold ${text} truncate`}>{eventTypeLabel(item.event_type)}</p>
        <p className="text-xs text-gray-400 font-mono">{item.event_type}</p>
      </div>
      <span className={`text-xl font-bold tabular-nums ${text}`}>
        {item.count.toLocaleString('pt-BR')}
      </span>
    </div>
  );
}

export default function Events() {
  const [filters,      setFilters]      = useState<EventFilters>({ limit: PAGE_SIZE, offset: 0 });
  const [events,       setEvents]       = useState<CustomerEvent[]>([]);
  const [totalCount,   setTotalCount]   = useState(0);
  const [summary,      setSummary]      = useState<EventTypeSummary[]>([]);
  const [loading,      setLoading]      = useState(true);
  const [error,        setError]        = useState('');
  const [selectedEvent, setSelectedEvent] = useState<CustomerEvent | null>(null);
  const [lastUpdated,  setLastUpdated]  = useState<Date | null>(null);

  const load = useCallback(async (f: EventFilters) => {
    setLoading(true);
    setError('');
    try {
      const [result, sum] = await Promise.all([
        getEventsPaginated(f),
        getEventTypeSummary(),
      ]);
      setEvents(result.events);
      setTotalCount(result.totalCount);
      setSummary(sum);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar eventos.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => load(filters), filters.search ? 400 : 0);
    return () => clearTimeout(t);
  }, [filters, load]);

  function handleFiltersChange(f: EventFilters) {
    setFilters({ ...f, limit: PAGE_SIZE, offset: 0 });
    setSelectedEvent(null);
  }

  function handlePageChange(offset: number) {
    setFilters((prev) => ({ ...prev, offset }));
  }

  const hasSelectedEvent = !!selectedEvent;

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-gray-50 overflow-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 px-8 py-5 shrink-0">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center">
              <Activity className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">Rastreamento de Eventos</h1>
              <p className="text-sm text-gray-400">
                Registro de eventos de clientes e do sistema
                {lastUpdated && (
                  <span className="text-gray-300 ml-2">
                    · {lastUpdated.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                )}
              </p>
            </div>
          </div>
          <button
            onClick={() => load(filters)}
            disabled={loading}
            className="w-9 h-9 flex items-center justify-center rounded-xl border border-gray-200 text-gray-400 hover:text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
            title="Atualizar"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      <div className="flex-1 px-8 py-6 space-y-4 min-h-0">
        {error && (
          <div className="px-4 py-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm">
            {error}
          </div>
        )}

        {/* Event type summary */}
        {summary.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-5 gap-3">
            {summary.slice(0, 10).map((item) => (
              <button
                key={item.event_type}
                onClick={() =>
                  handleFiltersChange({
                    ...filters,
                    eventType: filters.eventType === item.event_type ? null : item.event_type,
                  })
                }
                className={`text-left transition-all hover:scale-[1.02] active:scale-100 ${
                  filters.eventType === item.event_type
                    ? 'ring-2 ring-blue-500 ring-offset-1 rounded-xl'
                    : ''
                }`}
              >
                <SummaryCard item={item} />
              </button>
            ))}
          </div>
        )}

        {/* Filters */}
        <EventsFilters filters={filters} onChange={handleFiltersChange} />

        {/* Main content — table + optional detail panel */}
        <div className={`flex gap-4 ${hasSelectedEvent ? 'items-start' : ''}`}>
          <div className={`min-w-0 ${hasSelectedEvent ? 'flex-1' : 'w-full'}`}>
            <div className="flex items-center gap-2 mb-3">
              <Activity className="w-4 h-4 text-gray-400" />
              <h2 className="text-sm font-semibold text-gray-700">Eventos</h2>
              {totalCount > 0 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-100 text-xs font-medium text-emerald-600">
                  {totalCount.toLocaleString('pt-BR')}
                </span>
              )}
              {loading && events.length > 0 && (
                <Loader2 className="w-3.5 h-3.5 text-gray-300 animate-spin ml-1" />
              )}
            </div>
            <EventsTable
              events={events}
              loading={loading}
              totalCount={totalCount}
              limit={PAGE_SIZE}
              offset={filters.offset ?? 0}
              onPageChange={handlePageChange}
              onSelect={(ev) => setSelectedEvent((prev) => (prev?.id === ev.id ? null : ev))}
              selectedId={selectedEvent?.id}
            />
          </div>

          {selectedEvent && (
            <div className="w-80 shrink-0 sticky top-0">
              <EventDetailsPanel
                event={selectedEvent}
                onClose={() => setSelectedEvent(null)}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
