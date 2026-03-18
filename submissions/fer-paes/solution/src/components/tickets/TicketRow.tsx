import { useNavigate } from 'react-router-dom';
import { ExternalLink, UserCheck, XCircle, ChevronDown } from 'lucide-react';
import type { TicketWithRelations, TicketStatus, TicketSLA } from '../../types';
import {
  STATUS_CONFIG,
  PRIORITY_CONFIG,
  CHANNEL_ICONS,
  formatRelativeTime,
  shortId,
} from './ticketConfig';
import SLABadge from './SLABadge';
import { TagChip } from './TagSelector';
import type { Tag } from '../../types';

interface Props {
  ticket: TicketWithRelations;
  sla?: TicketSLA | null;
  tags?: Tag[];
  actionLoading: boolean;
  onAssign: () => void;
  onClose: () => void;
  onStatusChange: (status: TicketStatus) => void;
}

export default function TicketRow({ ticket, sla, tags, actionLoading, onAssign, onClose, onStatusChange }: Props) {
  const navigate = useNavigate();
  const statusCfg = STATUS_CONFIG[ticket.status];
  const StatusIcon = statusCfg.icon;
  const priorityCfg = PRIORITY_CONFIG[ticket.priority];
  const channelIcon = CHANNEL_ICONS[ticket.channel?.type || ''] || '?';
  const isClosed = ticket.status === 'closed';

  return (
    <tr className="group hover:bg-slate-50/60 transition-colors">
      <td className="px-5 py-3.5">
        <div>
          <span className="block text-xs font-mono text-gray-400 mb-0.5">#{shortId(ticket.id)}</span>
          <span className="block text-sm font-medium text-gray-900 leading-snug line-clamp-1 max-w-[200px]">
            {ticket.subject || 'No subject'}
          </span>
          {tags && tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {tags.slice(0, 3).map((tag) => (
                <TagChip key={tag.id} tag={tag} size="xs" />
              ))}
              {tags.length > 3 && (
                <span className="text-[10px] text-gray-400">+{tags.length - 3}</span>
              )}
            </div>
          )}
        </div>
      </td>

      <td className="px-5 py-3.5">
        {ticket.customer ? (
          <div>
            <p className="text-sm font-medium text-gray-800 truncate max-w-[140px]">
              {ticket.customer.name || 'Unknown'}
            </p>
            {ticket.customer.email && (
              <p className="text-xs text-gray-400 truncate max-w-[140px]">
                {ticket.customer.email}
              </p>
            )}
          </div>
        ) : (
          <span className="text-sm text-gray-400">—</span>
        )}
      </td>

      <td className="px-5 py-3.5">
        {ticket.channel ? (
          <div className="flex items-center gap-1.5">
            <span className="text-base leading-none">{channelIcon}</span>
            <span className="text-sm text-gray-600 capitalize">{ticket.channel.name}</span>
          </div>
        ) : (
          <span className="text-sm text-gray-400">—</span>
        )}
      </td>

      <td className="px-5 py-3.5">
        <div className="relative group/status inline-block">
          <button
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border ${statusCfg.color}`}
          >
            <StatusIcon className="w-3 h-3" />
            {statusCfg.label}
            {!isClosed && <ChevronDown className="w-2.5 h-2.5 opacity-50" />}
          </button>
          {!isClosed && (
            <div className="absolute left-0 top-full mt-1 z-20 hidden group-hover/status:block">
              <div className="bg-white border border-gray-100 rounded-xl shadow-lg overflow-hidden min-w-[160px] py-1">
                {(Object.keys(STATUS_CONFIG) as TicketStatus[])
                  .filter((s) => s !== ticket.status && s !== 'closed')
                  .map((s) => {
                    const cfg = STATUS_CONFIG[s];
                    const Ico = cfg.icon;
                    return (
                      <button
                        key={s}
                        disabled={actionLoading}
                        onClick={() => onStatusChange(s)}
                        className="w-full flex items-center gap-2 px-3 py-2 text-xs text-gray-600 hover:bg-gray-50 transition-colors"
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
      </td>

      <td className="px-5 py-3.5">
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold border ${priorityCfg.bg} ${priorityCfg.color}`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${priorityCfg.dot}`} />
          {priorityCfg.label}
        </span>
      </td>

      <td className="px-5 py-3.5">
        {ticket.assigned_user ? (
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-xs font-semibold text-blue-700 shrink-0">
              {(ticket.assigned_user.full_name || ticket.assigned_user.email)[0].toUpperCase()}
            </div>
            <span className="text-sm text-gray-700 truncate max-w-[100px]">
              {ticket.assigned_user.full_name || ticket.assigned_user.email}
            </span>
          </div>
        ) : (
          <span className="text-xs text-gray-400 italic">Unassigned</span>
        )}
      </td>

      <td className="px-5 py-3.5">
        <div className="flex flex-col gap-1 items-start">
          <span className="text-sm text-gray-400">{formatRelativeTime(ticket.updated_at)}</span>
          {sla && !isClosed && <SLABadge sla={sla} compact />}
        </div>
      </td>

      <td className="px-5 py-3.5">
        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            title="Open ticket"
            onClick={() => navigate(`/tickets/${ticket.id}`)}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </button>
          {!isClosed && (
            <button
              title="Assign ticket"
              disabled={actionLoading}
              onClick={onAssign}
              className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors disabled:opacity-40"
            >
              <UserCheck className="w-3.5 h-3.5" />
            </button>
          )}
          {!isClosed && (
            <button
              title="Close ticket"
              disabled={actionLoading}
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors disabled:opacity-40"
            >
              <XCircle className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}
