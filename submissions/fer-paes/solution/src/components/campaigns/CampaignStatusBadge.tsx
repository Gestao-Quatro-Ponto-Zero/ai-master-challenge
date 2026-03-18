import type { CampaignStatus } from '../../services/campaignService';
import { STATUS_META } from '../../services/campaignService';
import { FileText, Clock, Play, CheckCircle2, PauseCircle } from 'lucide-react';

const ICONS: Record<CampaignStatus, React.ComponentType<{ className?: string }>> = {
  draft:     FileText,
  scheduled: Clock,
  running:   Play,
  completed: CheckCircle2,
  paused:    PauseCircle,
};

interface Props {
  status: CampaignStatus;
  size?:  'sm' | 'md';
}

export default function CampaignStatusBadge({ status, size = 'sm' }: Props) {
  const meta = STATUS_META[status];
  const Icon = ICONS[status];
  const pad  = size === 'md' ? 'px-3 py-1 text-sm gap-1.5' : 'px-2 py-0.5 text-xs gap-1';

  return (
    <span
      className={`inline-flex items-center rounded-full font-medium border ${pad} ${meta.color} ${meta.bg} ${meta.border}`}
    >
      <Icon className={size === 'md' ? 'w-3.5 h-3.5' : 'w-3 h-3'} />
      {meta.label}
    </span>
  );
}
