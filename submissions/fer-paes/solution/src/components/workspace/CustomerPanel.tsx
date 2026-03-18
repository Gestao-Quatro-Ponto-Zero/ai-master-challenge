import { useState, useEffect } from 'react';
import { User, Mail, Phone, Hash, Calendar, Tag, ExternalLink, Loader2, Ticket as TicketIcon, Clock } from 'lucide-react';
import {
  getCustomerHistory,
  type WorkspaceTicket,
} from '../../services/workspaceService';
import type { TicketStatus, TicketPriority } from '../../types';

interface Props {
  ticket: WorkspaceTicket;
}

const STATUS_BADGE: Record<TicketStatus, { label: string; className: string }> = {
  open:             { label: 'Open',             className: 'bg-emerald-900/50 text-emerald-300 border-emerald-500/20' },
  in_progress:      { label: 'In Progress',      className: 'bg-blue-900/50 text-blue-300 border-blue-500/20'         },
  waiting_customer: { label: 'Waiting Customer', className: 'bg-amber-900/50 text-amber-300 border-amber-500/20'      },
  resolved:         { label: 'Resolved',         className: 'bg-slate-700/60 text-slate-400 border-slate-600/30'      },
  closed:           { label: 'Closed',           className: 'bg-slate-800/60 text-slate-600 border-slate-700/30'      },
};

const PRIORITY_DOT: Record<TicketPriority, string> = {
  urgent: 'bg-rose-500',
  high:   'bg-amber-400',
  medium: 'bg-blue-400',
  low:    'bg-slate-500',
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' });
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins  = Math.floor(diff / 60000);
  if (mins < 1)  return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border-b border-white/5 pb-4 mb-4 last:border-0 last:pb-0 last:mb-0">
      <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-3">{title}</h3>
      {children}
    </div>
  );
}

function InfoRow({ icon: Icon, label, value }: {
  icon:  React.ComponentType<{ className?: string }>;
  label: string;
  value: string | null | undefined;
}) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-2.5 mb-2.5 last:mb-0">
      <Icon className="w-3.5 h-3.5 text-slate-600 mt-0.5 shrink-0" />
      <div className="min-w-0">
        <p className="text-xs text-slate-600">{label}</p>
        <p className="text-xs font-medium text-slate-300 break-all">{value}</p>
      </div>
    </div>
  );
}

export default function CustomerPanel({ ticket }: Props) {
  const [history,  setHistory]  = useState<WorkspaceTicket[]>([]);
  const [loading,  setLoading]  = useState(false);

  const customer = ticket.customer as {
    id?: string; name?: string; email?: string; phone?: string;
    external_id?: string; created_at?: string;
  } | null;

  useEffect(() => {
    if (!customer?.id) return;
    setLoading(true);
    getCustomerHistory(customer.id, ticket.id)
      .then(setHistory)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [customer?.id, ticket.id]);

  const statusInfo = STATUS_BADGE[ticket.status] ?? STATUS_BADGE.open;

  return (
    <div className="flex flex-col h-full bg-slate-950 border-l border-white/5 overflow-y-auto">
      <div className="px-4 pt-4 pb-2 border-b border-white/5 shrink-0">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Customer &amp; Ticket</span>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-0">
        {/* Customer Info */}
        <Section title="Customer">
          {customer ? (
            <>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-9 h-9 rounded-full bg-blue-600/20 flex items-center justify-center shrink-0">
                  <span className="text-blue-300 text-sm font-semibold">
                    {(customer.name || customer.email || '?')[0].toUpperCase()}
                  </span>
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-white truncate">{customer.name || 'Unknown'}</p>
                  {customer.email && <p className="text-xs text-slate-500 truncate">{customer.email}</p>}
                </div>
              </div>
              <InfoRow icon={Mail}     label="Email"       value={customer.email}       />
              <InfoRow icon={Phone}    label="Phone"       value={customer.phone}       />
              <InfoRow icon={Hash}     label="External ID" value={customer.external_id} />
              {customer.created_at && (
                <InfoRow icon={Calendar} label="Customer since" value={formatDate(customer.created_at)} />
              )}
            </>
          ) : (
            <p className="text-xs text-slate-700">No customer data available.</p>
          )}
        </Section>

        {/* Ticket Details */}
        <Section title="Ticket Details">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-600">Status</span>
              <span className={`text-xs px-2 py-0.5 rounded-lg border font-medium ${statusInfo.className}`}>
                {statusInfo.label}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-600">Priority</span>
              <div className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${PRIORITY_DOT[ticket.priority]}`} />
                <span className="text-xs text-slate-300 capitalize">{ticket.priority}</span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-600">Channel</span>
              <span className="text-xs text-slate-300 capitalize">
                {(ticket.channel as { name?: string } | null)?.name ?? 'Unknown'}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-600">Created</span>
              <span className="text-xs text-slate-300">{timeAgo(ticket.created_at)}</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-600">Updated</span>
              <span className="text-xs text-slate-300">{timeAgo(ticket.updated_at)}</span>
            </div>

            <div className="pt-1">
              <span className="text-xs text-slate-700 font-mono">#{ticket.id.slice(0, 8)}</span>
            </div>
          </div>
        </Section>

        {/* Customer History */}
        <Section title="Customer History">
          {loading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="w-4 h-4 animate-spin text-slate-700" />
            </div>
          ) : history.length === 0 ? (
            <p className="text-xs text-slate-700">No previous tickets.</p>
          ) : (
            <div className="space-y-2">
              {history.map((t) => {
                const hStatus = STATUS_BADGE[t.status] ?? STATUS_BADGE.open;
                return (
                  <div
                    key={t.id}
                    className="flex flex-col gap-1 px-3 py-2.5 rounded-xl bg-slate-900/60 border border-white/5"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs font-medium text-slate-300 truncate flex-1">
                        {t.subject || 'No subject'}
                      </p>
                      <span className={`text-xs px-1.5 py-0.5 rounded-md border shrink-0 ${hStatus.className}`}>
                        {hStatus.label}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`w-1.5 h-1.5 rounded-full ${PRIORITY_DOT[t.priority]}`} />
                      <span className="text-xs text-slate-600 capitalize">{t.priority}</span>
                      <span className="text-xs text-slate-700">·</span>
                      <span className="text-xs text-slate-700">{timeAgo(t.created_at)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Section>
      </div>
    </div>
  );
}
