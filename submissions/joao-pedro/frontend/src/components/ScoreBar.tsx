import { cn } from '@/lib/utils'

interface ScoreRowProps {
  label: string
  value: number
  color: string
}

function ScoreRow({ label, value, color }: ScoreRowProps) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-24 shrink-0 text-muted-foreground">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-secondary overflow-hidden">
        <div
          className={cn('h-full rounded-full', color)}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
      <span className="w-10 text-right font-mono text-xs">{value.toFixed(0)}</span>
    </div>
  )
}

interface Props {
  urgency: number
  probability: number
  value: number
  score: number
  className?: string
}

export function ScoreBar({ urgency, probability, value, score, className }: Props) {
  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      <ScoreRow label="Urgência"     value={urgency}     color="bg-orange-500" />
      <ScoreRow label="Prob."        value={probability} color="bg-blue-500" />
      <ScoreRow label="Valor"        value={value}       color="bg-green-500" />
      <div className="border-t pt-1.5 mt-0.5">
        <ScoreRow label="Score"      value={score}       color="bg-slate-700" />
      </div>
    </div>
  )
}
