import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Loader2 } from 'lucide-react';
import type { OperatorStatus } from '../../types';

interface StatusConfig {
  label:      string;
  dot:        string;
  ring:       string;
  text:       string;
  badgeBg:    string;
  badgeBorder: string;
}

const STATUS_CONFIG: Record<OperatorStatus, StatusConfig> = {
  online: {
    label:       'Online',
    dot:         'bg-emerald-400',
    ring:        'ring-2 ring-emerald-400/30',
    text:        'text-emerald-300',
    badgeBg:     'bg-emerald-500/10',
    badgeBorder: 'border-emerald-500/20',
  },
  away: {
    label:       'Away',
    dot:         'bg-amber-400',
    ring:        'ring-2 ring-amber-400/30',
    text:        'text-amber-300',
    badgeBg:     'bg-amber-500/10',
    badgeBorder: 'border-amber-500/20',
  },
  busy: {
    label:       'Busy',
    dot:         'bg-rose-400',
    ring:        'ring-2 ring-rose-400/30',
    text:        'text-rose-300',
    badgeBg:     'bg-rose-500/10',
    badgeBorder: 'border-rose-500/20',
  },
  offline: {
    label:       'Offline',
    dot:         'bg-slate-600',
    ring:        '',
    text:        'text-slate-500',
    badgeBg:     'bg-slate-800/60',
    badgeBorder: 'border-slate-700/40',
  },
};

const SELECTABLE_STATUSES: OperatorStatus[] = ['online', 'away', 'offline'];

interface Props {
  status:    OperatorStatus;
  loading?:  boolean;
  onChange:  (s: OperatorStatus) => Promise<void>;
}

export default function OperatorPresenceSelector({ status, loading, onChange }: Props) {
  const [open,   setOpen]   = useState(false);
  const [saving, setSaving] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, [open]);

  async function handleSelect(next: OperatorStatus) {
    setOpen(false);
    if (next === status) return;
    setSaving(true);
    try { await onChange(next); }
    catch { } finally { setSaving(false); }
  }

  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.offline;

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        disabled={loading || saving}
        className={`flex items-center gap-2 px-3 py-2 rounded-xl border transition-colors disabled:opacity-50 ${cfg.badgeBg} ${cfg.badgeBorder} hover:brightness-110`}
      >
        {loading || saving ? (
          <Loader2 className="w-2.5 h-2.5 animate-spin text-slate-500" />
        ) : (
          <span className={`w-2 h-2 rounded-full shrink-0 ${cfg.dot} ${cfg.ring}`} />
        )}
        <span className={`text-xs font-medium ${cfg.text}`}>{cfg.label}</span>
        <ChevronDown className={`w-3 h-3 ${cfg.text} opacity-60 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 z-30 bg-slate-800 border border-white/10 rounded-xl overflow-hidden shadow-2xl min-w-[140px]">
          <div className="px-3 py-2 border-b border-white/6">
            <p className="text-xs text-slate-600 font-medium">Set status</p>
          </div>
          {SELECTABLE_STATUSES.map((s) => {
            const c = STATUS_CONFIG[s];
            const isActive = s === status;
            return (
              <button
                key={s}
                onClick={() => handleSelect(s)}
                className={`w-full flex items-center gap-2.5 px-3 py-2.5 text-xs transition-colors hover:bg-white/5 ${
                  isActive ? 'bg-white/4' : ''
                }`}
              >
                <span className={`w-2 h-2 rounded-full shrink-0 ${c.dot}`} />
                <span className={`font-medium ${isActive ? c.text : 'text-slate-400'}`}>{c.label}</span>
                {isActive && (
                  <span className={`ml-auto text-xs ${c.text} opacity-60`}>current</span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
