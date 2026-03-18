import { X, CheckCircle2, XCircle, Clock, Loader2, Cpu, Bot, Zap, Timer, AlertTriangle } from 'lucide-react';
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

interface RowProps { label: string; value: React.ReactNode }
function DetailRow({ label, value }: RowProps) {
  return (
    <div className="flex items-start justify-between py-3 border-b border-white/5 last:border-0">
      <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</span>
      <span className="text-sm text-white text-right max-w-48 break-all">{value}</span>
    </div>
  );
}

interface Props {
  request: LLMRequest;
  onClose: () => void;
}

export default function LLMRequestDetails({ request, onClose }: Props) {
  const cfg = STATUS_CONFIG[request.status];
  const Icon = cfg.icon;

  const timestamp = new Date(request.created_at).toLocaleString();

  return (
    <div className="w-96 bg-slate-900 border-l border-white/5 flex flex-col h-full overflow-hidden flex-shrink-0">
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
        <h3 className="text-white font-semibold text-sm">Request Details</h3>
        <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="px-5 py-4 border-b border-white/5">
          <div className="flex items-center justify-between mb-3">
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${cfg.cls}`}>
              <Icon className={`w-3 h-3 ${request.status === 'pending' ? 'animate-spin' : ''}`} />
              {cfg.label}
            </span>
            <code className="text-slate-500 text-xs font-mono">{request.id.slice(0, 16)}...</code>
          </div>
          <p className="text-xs text-slate-500">{timestamp}</p>
        </div>

        <div className="px-5 py-4 border-b border-white/5">
          <div className="flex items-center gap-2 mb-3">
            <Cpu className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Model</span>
          </div>
          <DetailRow label="Name"       value={request.model?.name ?? request.model_identifier ?? '—'} />
          <DetailRow label="Provider"   value={<span className="capitalize">{request.provider ?? '—'}</span>} />
          <DetailRow label="Identifier" value={<code className="font-mono text-xs text-slate-300">{request.model_identifier ?? '—'}</code>} />
        </div>

        <div className="px-5 py-4 border-b border-white/5">
          <div className="flex items-center gap-2 mb-3">
            <Bot className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Agent</span>
          </div>
          <DetailRow label="Agent" value={request.agent?.name ?? <span className="text-slate-500">System / No agent</span>} />
        </div>

        <div className="px-5 py-4 border-b border-white/5">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Token Usage</span>
          </div>
          <div className="grid grid-cols-3 gap-3 mt-2">
            {[
              { label: 'Prompt',     value: request.prompt_tokens },
              { label: 'Completion', value: request.completion_tokens },
              { label: 'Total',      value: request.total_tokens },
            ].map((t) => (
              <div key={t.label} className="bg-slate-800 rounded-lg px-3 py-2.5 text-center">
                <p className="text-lg font-bold text-white tabular-nums">
                  {t.value !== null ? t.value.toLocaleString() : '—'}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">{t.label}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="px-5 py-4 border-b border-white/5">
          <div className="flex items-center gap-2 mb-3">
            <Timer className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Performance</span>
          </div>
          <div className="bg-slate-800 rounded-lg px-4 py-3 flex items-center justify-between">
            <span className="text-sm text-slate-400">Latency</span>
            <span className={`text-sm font-semibold tabular-nums ${
              request.latency_ms && request.latency_ms > 3000 ? 'text-amber-400' : 'text-white'
            }`}>
              {formatLatency(request.latency_ms)}
            </span>
          </div>
        </div>

        {request.error_message && (
          <div className="px-5 py-4">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
              <span className="text-xs font-medium text-red-400 uppercase tracking-wider">Error</span>
            </div>
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3">
              <p className="text-red-400 text-sm break-words">{request.error_message}</p>
            </div>
          </div>
        )}

        {request.metadata && Object.keys(request.metadata).length > 0 && (
          <div className="px-5 py-4">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Metadata</span>
            <pre className="mt-2 text-xs text-slate-400 bg-slate-800 rounded-lg p-3 overflow-x-auto">
              {JSON.stringify(request.metadata, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
