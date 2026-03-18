import { ArrowLeft, XCircle, UserCheck, ChevronDown, RotateCcw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { TicketWithRelations, TicketStatus } from '../../types';
import { STATUS_CONFIG, PRIORITY_CONFIG, CHANNEL_ICONS, shortId } from './ticketConfig';

interface TicketHeaderProps {
  ticket: TicketWithRelations;
  onStatusChange: (status: TicketStatus) => void;
  onAssign: () => void;
  onClose: () => void;
  loading?: boolean;
}

export default function TicketHeader({ ticket, onStatusChange, onAssign, onClose, loading }: TicketHeaderProps) {
  const navigate = useNavigate();
  const statusCfg = STATUS_CONFIG[ticket.status];
  const StatusIcon = statusCfg.icon;
  const priorityCfg = PRIORITY_CONFIG[ticket.priority];
  const channelIcon = CHANNEL_ICONS[ticket.channel?.type || ''] || '?';
  const isClosed = ticket.status === 'closed';

  const statusOptions = (Object.keys(STATUS_CONFIG) as TicketStatus[]).filter(
    (s) => s !== ticket.status && s !== 'closed'
  );

  return (
    <div className="bg-white border-b border-gray-100 px-6 py-3.5 shrink-0">
      <div className="flex items-center gap-3 mb-2.5">
        <button
          onClick={() => navigate('/tickets')}
          className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors shrink-0"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
        </button>
        <span className="text-xs font-mono text-gray-400 shrink-0">#{shortId(ticket.id)}</span>
        <div className="h-3.5 w-px bg-gray-200 shrink-0" />
        <h1 className="text-sm font-semibold text-gray-900 truncate flex-1 min-w-0">
          {ticket.subject || 'No subject'}
        </h1>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <div className="relative group/status">
          <button
            className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border transition-colors ${statusCfg.color}`}
          >
            <StatusIcon className="w-3.5 h-3.5" />
            {statusCfg.label}
            {!isClosed && statusOptions.length > 0 && (
              <ChevronDown className="w-2.5 h-2.5 opacity-60" />
            )}
          </button>
          {!isClosed && statusOptions.length > 0 && (
            <div className="absolute left-0 top-full mt-1.5 z-30 hidden group-hover/status:block">
              <div className="bg-white border border-gray-100 rounded-xl shadow-xl overflow-hidden min-w-[170px] py-1">
                {statusOptions.map((s) => {
                  const cfg = STATUS_CONFIG[s];
                  const Ico = cfg.icon;
                  return (
                    <button
                      key={s}
                      disabled={loading}
                      onClick={() => onStatusChange(s)}
                      className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-xs text-gray-600 hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                      <Ico className="w-3.5 h-3.5" />
                      {cfg.label}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold border ${priorityCfg.bg} ${priorityCfg.color}`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${priorityCfg.dot}`} />
          {priorityCfg.label}
        </span>

        {ticket.customer && (
          <>
            <div className="h-4 w-px bg-gray-200" />
            <div className="flex items-center gap-1.5">
              <div className="w-5 h-5 rounded-full bg-slate-200 flex items-center justify-center text-xs font-semibold text-slate-600 shrink-0">
                {(ticket.customer.name || ticket.customer.email || '?')[0].toUpperCase()}
              </div>
              <span className="text-xs text-gray-700 font-medium truncate max-w-[160px]">
                {ticket.customer.name || ticket.customer.email || 'Unknown customer'}
              </span>
            </div>
          </>
        )}

        {ticket.channel && (
          <>
            <div className="h-4 w-px bg-gray-200" />
            <div className="flex items-center gap-1.5">
              <span className="text-sm leading-none">{channelIcon}</span>
              <span className="text-xs text-gray-500 capitalize">{ticket.channel.name}</span>
            </div>
          </>
        )}

        <div className="ml-auto flex items-center gap-2 shrink-0">
          {ticket.assigned_user ? (
            <button
              onClick={onAssign}
              disabled={loading || isClosed}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-50 border border-gray-200 hover:border-blue-200 hover:bg-blue-50/60 disabled:cursor-default disabled:hover:bg-gray-50 disabled:hover:border-gray-200 transition-colors group"
              title={isClosed ? '' : 'Change assigned operator'}
            >
              <div className="w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center text-xs font-semibold text-blue-700 shrink-0">
                {(ticket.assigned_user.full_name || ticket.assigned_user.email)[0].toUpperCase()}
              </div>
              <span className="text-xs text-gray-600 font-medium">
                {ticket.assigned_user.full_name || ticket.assigned_user.email}
              </span>
              {!isClosed && (
                <ChevronDown className="w-3 h-3 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              )}
            </button>
          ) : (
            !isClosed && (
              <button
                onClick={onAssign}
                disabled={loading}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-dashed border-gray-300 text-xs text-gray-500 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50/50 transition-colors disabled:opacity-50"
              >
                <UserCheck className="w-3.5 h-3.5" />
                Assign
              </button>
            )
          )}

          {isClosed ? (
            <button
              onClick={() => onStatusChange('open')}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 text-xs text-gray-500 hover:text-emerald-600 hover:border-emerald-200 hover:bg-emerald-50 transition-colors disabled:opacity-50"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reopen
            </button>
          ) : (
            <button
              onClick={onClose}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 text-xs text-gray-500 hover:text-red-600 hover:border-red-200 hover:bg-red-50 transition-colors disabled:opacity-50"
            >
              <XCircle className="w-3.5 h-3.5" />
              Close
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
