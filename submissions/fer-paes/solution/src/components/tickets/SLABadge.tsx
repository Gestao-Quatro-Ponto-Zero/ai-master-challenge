import { useState, useEffect } from 'react';
import { Timer, AlertTriangle } from 'lucide-react';
import { computeSLACountdown, formatSLATime } from '../../services/slaService';
import type { TicketSLA } from '../../types';

interface SLABadgeProps {
  sla: TicketSLA;
  compact?: boolean;
}

export default function SLABadge({ sla, compact = false }: SLABadgeProps) {
  const [countdown, setCountdown] = useState(() => computeSLACountdown(sla));

  useEffect(() => {
    setCountdown(computeSLACountdown(sla));
    const interval = setInterval(() => {
      setCountdown(computeSLACountdown(sla));
    }, 30_000);
    return () => clearInterval(interval);
  }, [sla]);

  if (sla.status === 'breached' || countdown.isBreached) {
    return (
      <span
        className={`inline-flex items-center gap-1 font-medium text-red-600 bg-red-50 border border-red-200 rounded-lg ${compact ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-1 text-xs'}`}
        title="SLA breached"
      >
        <AlertTriangle className={compact ? 'w-2.5 h-2.5' : 'w-3 h-3'} />
        SLA breached
      </span>
    );
  }

  const mins = countdown.minutesRemaining;
  const isUrgent = mins <= 15;
  const isWarning = mins <= 60;

  const colorClass = isUrgent
    ? 'text-red-600 bg-red-50 border-red-200'
    : isWarning
    ? 'text-amber-600 bg-amber-50 border-amber-200'
    : 'text-emerald-600 bg-emerald-50 border-emerald-200';

  return (
    <span
      className={`inline-flex items-center gap-1 font-medium border rounded-lg ${colorClass} ${compact ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-1 text-xs'}`}
      title={`${countdown.label} due: ${new Date(countdown.deadline).toLocaleString()}`}
    >
      <Timer className={compact ? 'w-2.5 h-2.5' : 'w-3 h-3'} />
      {formatSLATime(mins)}
    </span>
  );
}
