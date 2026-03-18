import { useState, useEffect } from 'react';
import { Shield, Timer, CheckCircle2, AlertTriangle } from 'lucide-react';
import { computeSLACountdown, formatSLATime } from '../../services/slaService';
import type { TicketSLA } from '../../types';

interface SLAPanelProps {
  sla: TicketSLA;
}

function DeadlineRow({
  label,
  deadline,
  achievedAt,
}: {
  label: string;
  deadline: string;
  achievedAt: string | null;
}) {
  const now = Date.now();
  const deadlineMs = new Date(deadline).getTime();
  const isBreached = !achievedAt && now > deadlineMs;
  const wasLate = achievedAt && new Date(achievedAt).getTime() > deadlineMs;

  let statusIcon = <Timer className="w-3 h-3 text-amber-500" />;
  let statusColor = 'text-amber-600';
  let timeText = '';

  if (achievedAt) {
    if (wasLate) {
      statusIcon = <AlertTriangle className="w-3 h-3 text-red-500" />;
      statusColor = 'text-red-600';
      timeText = 'Late';
    } else {
      statusIcon = <CheckCircle2 className="w-3 h-3 text-emerald-500" />;
      statusColor = 'text-emerald-600';
      timeText = 'Done';
    }
  } else if (isBreached) {
    statusIcon = <AlertTriangle className="w-3 h-3 text-red-500" />;
    statusColor = 'text-red-600';
    timeText = 'Breached';
  } else {
    const minsLeft = Math.floor((deadlineMs - now) / 60_000);
    const isUrgent = minsLeft <= 15;
    const isWarning = minsLeft <= 60;
    statusIcon = <Timer className={`w-3 h-3 ${isUrgent ? 'text-red-500' : isWarning ? 'text-amber-500' : 'text-emerald-500'}`} />;
    statusColor = isUrgent ? 'text-red-600' : isWarning ? 'text-amber-600' : 'text-emerald-600';
    timeText = formatSLATime(minsLeft);
  }

  return (
    <div className="flex items-start justify-between gap-2">
      <div className="min-w-0">
        <p className="text-xs text-gray-500">{label}</p>
        <p className="text-[10px] text-gray-400 mt-0.5">
          Due {new Date(deadline).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
      <div className="flex items-center gap-1 shrink-0">
        {statusIcon}
        <span className={`text-xs font-semibold ${statusColor}`}>{timeText}</span>
      </div>
    </div>
  );
}

export default function SLAPanel({ sla }: SLAPanelProps) {
  const [, forceUpdate] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => forceUpdate((n) => n + 1), 30_000);
    return () => clearInterval(interval);
  }, []);

  const countdown = computeSLACountdown(sla);
  const isBreached = sla.status === 'breached' || countdown.isBreached;

  return (
    <section>
      <div className="flex items-center justify-between mb-2.5">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
          <Shield className="w-3 h-3" />
          SLA
        </p>
        {isBreached ? (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-semibold bg-red-50 text-red-600 border border-red-200">
            <AlertTriangle className="w-2.5 h-2.5" />
            Breached
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-semibold bg-emerald-50 text-emerald-600 border border-emerald-200">
            <CheckCircle2 className="w-2.5 h-2.5" />
            On track
          </span>
        )}
      </div>
      <div className="space-y-3">
        <DeadlineRow
          label="First response"
          deadline={sla.first_response_deadline}
          achievedAt={sla.first_response_at}
        />
        <DeadlineRow
          label="Resolution"
          deadline={sla.resolution_deadline}
          achievedAt={sla.resolved_at}
        />
      </div>
    </section>
  );
}
