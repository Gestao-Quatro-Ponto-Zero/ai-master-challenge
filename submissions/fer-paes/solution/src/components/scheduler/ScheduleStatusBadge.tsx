import { CheckCircle2, XCircle } from 'lucide-react';

interface Props {
  isActive: boolean;
  size?:    'sm' | 'md';
}

export default function ScheduleStatusBadge({ isActive, size = 'sm' }: Props) {
  const pad  = size === 'md' ? 'px-3 py-1 text-sm gap-1.5' : 'px-2 py-0.5 text-xs gap-1';
  const Icon = isActive ? CheckCircle2 : XCircle;
  const cls  = isActive
    ? 'text-emerald-600 bg-emerald-50 border-emerald-100'
    : 'text-gray-400 bg-gray-100 border-gray-200';

  return (
    <span className={`inline-flex items-center rounded-full font-medium border ${pad} ${cls}`}>
      <Icon className={size === 'md' ? 'w-3.5 h-3.5' : 'w-3 h-3'} />
      {isActive ? 'Ativo' : 'Inativo'}
    </span>
  );
}
