import type { OperatorStatus } from '../types';

const STATUS_CONFIG: Record<OperatorStatus, { dot: string; label: string; text: string }> = {
  online: { dot: 'bg-emerald-500', label: 'Online', text: 'text-emerald-600' },
  away:   { dot: 'bg-amber-400',  label: 'Away',   text: 'text-amber-600'  },
  busy:   { dot: 'bg-rose-500',   label: 'Busy',   text: 'text-rose-600'   },
  offline:{ dot: 'bg-gray-300',   label: 'Offline', text: 'text-gray-400'  },
};

interface PresenceDotProps {
  status: OperatorStatus;
  size?: 'sm' | 'md';
  className?: string;
}

export function PresenceDot({ status, size = 'sm', className = '' }: PresenceDotProps) {
  const cfg = STATUS_CONFIG[status];
  const dim = size === 'sm' ? 'w-2 h-2' : 'w-2.5 h-2.5';
  return (
    <span
      className={`inline-block rounded-full shrink-0 ${dim} ${cfg.dot} ${
        status === 'online' ? 'ring-2 ring-white' : ''
      } ${className}`}
      title={cfg.label}
    />
  );
}

interface PresenceBadgeProps {
  status: OperatorStatus;
  showLabel?: boolean;
  size?: 'sm' | 'md';
  className?: string;
}

export function PresenceBadge({ status, showLabel = false, size = 'sm', className = '' }: PresenceBadgeProps) {
  const cfg = STATUS_CONFIG[status];
  return (
    <span className={`inline-flex items-center gap-1.5 ${className}`}>
      <PresenceDot status={status} size={size} />
      {showLabel && <span className={`text-xs font-medium ${cfg.text}`}>{cfg.label}</span>}
    </span>
  );
}

export const PRESENCE_OPTIONS: { value: OperatorStatus; label: string }[] = [
  { value: 'online',  label: 'Online'  },
  { value: 'away',    label: 'Away'    },
  { value: 'busy',    label: 'Busy'    },
  { value: 'offline', label: 'Offline' },
];
