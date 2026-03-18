import { STATUS_META, type DeliveryStatus } from '../../services/campaignDeliveryService';

interface Props {
  status: DeliveryStatus;
  size?:  'sm' | 'md';
}

export default function CampaignDeliveryStatusBadge({ status, size = 'sm' }: Props) {
  const meta = STATUS_META[status] ?? STATUS_META.pending;
  const pad  = size === 'md' ? 'px-3 py-1 text-sm gap-2' : 'px-2 py-0.5 text-xs gap-1.5';

  return (
    <span className={`inline-flex items-center rounded-full font-medium border ${pad} ${meta.color} ${meta.bg} ${meta.border}`}>
      <span className={`rounded-full shrink-0 ${size === 'md' ? 'w-2 h-2' : 'w-1.5 h-1.5'} ${meta.dot}`} />
      {meta.label}
    </span>
  );
}
