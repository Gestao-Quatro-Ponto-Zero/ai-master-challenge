import { cn } from '@/lib/utils'
import type { ActionType } from '@/types'

const config: Record<ActionType, { label: string; className: string }> = {
  PUSH_HARD:        { label: 'Push Hard',        className: 'bg-blue-700 text-white' },
  ACCELERATE:       { label: 'Accelerate',        className: 'bg-blue-400 text-white' },
  MONITOR:          { label: 'Monitor',           className: 'bg-gray-200 text-gray-700' },
  INVESTIGATE:      { label: 'Investigate',       className: 'bg-orange-100 text-orange-800 border border-orange-200' },
  TRANSFER:         { label: 'Transfer',          className: 'bg-purple-700 text-white' },
  CONSIDER_TRANSFER:{ label: 'Consider Transfer', className: 'bg-purple-200 text-purple-800' },
  DISCARD:          { label: 'Discard',           className: 'bg-red-100 text-red-800 border border-red-200' },
  RE_QUALIFY:       { label: 'Re-qualify',        className: 'bg-yellow-100 text-yellow-800 border border-yellow-200' },
}

interface Props {
  action: ActionType
  className?: string
}

export function ActionBadge({ action, className }: Props) {
  const { label, className: style } = config[action] ?? { label: action, className: 'bg-gray-100 text-gray-600' }
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold',
        style,
        className,
      )}
    >
      {label}
    </span>
  )
}
