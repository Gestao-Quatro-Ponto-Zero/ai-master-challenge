import { cn } from '@/lib/utils'
import type { ViabilityLabel } from '@/types'

const styles: Record<ViabilityLabel, string> = {
  Alta: 'bg-green-100 text-green-800 border-green-200',
  Média: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  Baixa: 'bg-red-100 text-red-800 border-red-200',
}

interface Props {
  label: ViabilityLabel
  className?: string
}

export function ViabilityBadge({ label, className }: Props) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold',
        styles[label],
        className,
      )}
    >
      {label}
    </span>
  )
}
