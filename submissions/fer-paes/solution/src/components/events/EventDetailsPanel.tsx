import { X, Calendar, User, Tag, Database, Globe } from 'lucide-react';
import type { CustomerEvent } from '../../services/eventTrackingService';
import { eventTypeLabel, eventTypeColor, sourceLabel, formatEventDate } from '../../services/eventTrackingService';
import { Link } from 'react-router-dom';

interface Props {
  event:   CustomerEvent;
  onClose: () => void;
}

function DetailRow({ icon: Icon, label, children }: {
  icon:     React.ComponentType<{ className?: string }>;
  label:    string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3 py-3 border-b border-gray-100 last:border-0">
      <div className="w-7 h-7 rounded-lg bg-gray-50 flex items-center justify-center shrink-0 mt-0.5">
        <Icon className="w-3.5 h-3.5 text-gray-400" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs text-gray-400 mb-0.5">{label}</p>
        <div className="text-sm text-gray-800">{children}</div>
      </div>
    </div>
  );
}

export default function EventDetailsPanel({ event, onClose }: Props) {
  const { bg, text, border } = eventTypeColor(event.event_type);
  const hasData = event.event_data && Object.keys(event.event_data).length > 0;

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden flex flex-col">
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
            <Tag className="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Detalhes do Evento</h3>
            <p className="text-xs text-gray-400 font-mono">{event.id.slice(0, 8)}…</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 px-5 overflow-y-auto">
        <DetailRow icon={Tag} label="Tipo de Evento">
          <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold border ${bg} ${text} ${border}`}>
            {eventTypeLabel(event.event_type)}
          </span>
          <span className="ml-2 text-xs text-gray-400 font-mono">{event.event_type}</span>
        </DetailRow>

        <DetailRow icon={User} label="Cliente">
          {event.customer_id ? (
            <Link
              to={`/customers/${event.customer_id}`}
              className="text-blue-600 hover:text-blue-700 font-medium transition-colors"
            >
              {event.customer_name ?? 'Nome desconhecido'}
            </Link>
          ) : (
            <span className="text-gray-400 italic">Evento do sistema</span>
          )}
          {event.customer_email && (
            <p className="text-xs text-gray-400 mt-0.5">{event.customer_email}</p>
          )}
        </DetailRow>

        <DetailRow icon={Globe} label="Origem">
          <span className="font-medium">{sourceLabel(event.source)}</span>
          <span className="ml-1.5 text-xs text-gray-400 font-mono">({event.source})</span>
        </DetailRow>

        <DetailRow icon={Calendar} label="Data e Hora">
          {formatEventDate(event.created_at)}
        </DetailRow>

        <DetailRow icon={Database} label="Dados do Evento">
          {hasData ? (
            <pre className="text-xs bg-gray-50 border border-gray-100 rounded-xl p-3 overflow-auto max-h-64 text-gray-700 font-mono leading-relaxed whitespace-pre-wrap">
              {JSON.stringify(event.event_data, null, 2)}
            </pre>
          ) : (
            <span className="text-gray-400 italic text-xs">Sem dados adicionais</span>
          )}
        </DetailRow>
      </div>
    </div>
  );
}
