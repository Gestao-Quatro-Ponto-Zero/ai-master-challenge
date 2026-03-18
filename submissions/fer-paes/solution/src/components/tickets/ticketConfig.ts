import { Circle, Clock, CheckCircle2, XCircle, PauseCircle } from 'lucide-react';
import type { TicketStatus, TicketPriority } from '../../types';

export const STATUS_CONFIG: Record<
  TicketStatus,
  { label: string; color: string; icon: React.ComponentType<{ className?: string }> }
> = {
  open: { label: 'Open', color: 'bg-emerald-50 text-emerald-700 border-emerald-100', icon: Circle },
  in_progress: { label: 'In Progress', color: 'bg-blue-50 text-blue-700 border-blue-100', icon: Clock },
  waiting_customer: { label: 'Waiting', color: 'bg-amber-50 text-amber-700 border-amber-100', icon: PauseCircle },
  resolved: { label: 'Resolved', color: 'bg-teal-50 text-teal-700 border-teal-100', icon: CheckCircle2 },
  closed: { label: 'Closed', color: 'bg-gray-50 text-gray-500 border-gray-200', icon: XCircle },
};

export const PRIORITY_CONFIG: Record<
  TicketPriority,
  { label: string; color: string; bg: string; dot: string }
> = {
  urgent: { label: 'Urgent', color: 'text-red-700', bg: 'bg-red-50 border-red-100', dot: 'bg-red-500' },
  high: { label: 'High', color: 'text-orange-700', bg: 'bg-orange-50 border-orange-100', dot: 'bg-orange-500' },
  medium: { label: 'Medium', color: 'text-amber-700', bg: 'bg-amber-50 border-amber-100', dot: 'bg-amber-400' },
  low: { label: 'Low', color: 'text-gray-500', bg: 'bg-gray-50 border-gray-200', dot: 'bg-gray-300' },
};

export const CHANNEL_ICONS: Record<string, string> = {
  chat: '💬',
  email: '✉️',
  social: '📱',
  phone: '📞',
  api: '🔌',
  bot: '🤖',
};

export function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export function shortId(id: string): string {
  return id.slice(0, 8).toUpperCase();
}
