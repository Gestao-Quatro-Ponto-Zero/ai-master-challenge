import { CheckCircle2, XCircle, Clock, Loader2, ChevronRight } from 'lucide-react';
import type { LLMRequest, LLMRequestStatus } from '../../types';

const STATUS_CONFIG: Record<LLMRequestStatus, { icon: React.FC<{ className?: string }>; label: string; cls: string }> = {
  success: { icon: CheckCircle2, label: 'Success', cls: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
  error:   { icon: XCircle,      label: 'Error',   cls: 'bg-red-500/10 text-red-400 border-red-500/20'             },
  timeout: { icon: Clock,        label: 'Timeout', cls: 'bg-amber-500/10 text-amber-400 border-amber-500/20'        },
  pending: { icon: Loader2,      label: 'Pending', cls: 'bg-slate-700 text-slate-400 border-white/10'              },
};

function formatLatency(ms: number | null): string {
  if (ms === null) return '—';
  if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`;
  return `${ms}ms`;
}

function formatTokens(n: number | null): string {
  if (n === null) return '—';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function shortId(id: string): string {
  return id.slice(0, 8).toUpperCase();
}

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

interface Props {
  requests: LLMRequest[];
  loading: boolean;
  selectedId: string | null;
  onSelect: (req: LLMRequest) => void;
}

export default function LLMRequestsTable({ requests, loading, selectedId, onSelect }: Props) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="w-6 h-6 text-slate-400 animate-spin" />
      </div>
    );
  }

  if (requests.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="w-12 h-12 rounded-full bg-slate-900 flex items-center justify-center mb-3">
          <Clock className="w-6 h-6 text-slate-600" />
        </div>
        <p className="text-slate-400 font-medium">No request logs found</p>
        <p className="text-slate-600 text-sm mt-1">LLM calls will appear here once the system makes requests</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-white/5">
            <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Request ID</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Model</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Provider</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Agent</th>
            <th className="text-right px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Tokens</th>
            <th className="text-right px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Latency</th>
            <th className="text-center px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
            <th className="text-right px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Time</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {requests.map((req) => {
            const cfg = STATUS_CONFIG[req.status];
            const Icon = cfg.icon;
            const isSelected = req.id === selectedId;

            return (
              <tr
                key={req.id}
                onClick={() => onSelect(req)}
                className={`cursor-pointer transition-colors ${
                  isSelected ? 'bg-blue-600/10' : 'hover:bg-white/[0.02]'
                }`}
              >
                <td className="px-4 py-3.5">
                  <code className="text-slate-400 text-xs font-mono">{shortId(req.id)}</code>
                </td>
                <td className="px-4 py-3.5">
                  <p className="text-white text-sm">
                    {req.model?.name ?? req.model_identifier ?? '—'}
                  </p>
                </td>
                <td className="px-4 py-3.5">
                  <span className="text-slate-300 text-sm capitalize">{req.provider ?? '—'}</span>
                </td>
                <td className="px-4 py-3.5">
                  <span className="text-slate-400 text-sm">{req.agent?.name ?? '—'}</span>
                </td>
                <td className="px-4 py-3.5 text-right">
                  <span className="text-slate-300 text-sm tabular-nums">{formatTokens(req.total_tokens)}</span>
                </td>
                <td className="px-4 py-3.5 text-right">
                  <span className={`text-sm tabular-nums ${
                    req.latency_ms && req.latency_ms > 3000 ? 'text-amber-400' : 'text-slate-300'
                  }`}>
                    {formatLatency(req.latency_ms)}
                  </span>
                </td>
                <td className="px-4 py-3.5 text-center">
                  <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${cfg.cls}`}>
                    <Icon className={`w-3 h-3 ${req.status === 'pending' ? 'animate-spin' : ''}`} />
                    {cfg.label}
                  </span>
                </td>
                <td className="px-4 py-3.5 text-right">
                  <span className="text-slate-500 text-xs">{relativeTime(req.created_at)}</span>
                </td>
                <td className="px-4 py-3.5">
                  <ChevronRight className={`w-4 h-4 transition-colors ${isSelected ? 'text-blue-400' : 'text-slate-700'}`} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
