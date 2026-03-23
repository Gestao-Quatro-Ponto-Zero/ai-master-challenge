import { cn } from '@/lib/utils'

interface SelectFilterProps {
  label: string
  value: string
  options: { value: string; label: string }[]
  onChange: (value: string) => void
  className?: string
}

export function SelectFilter({ label, value, options, onChange, className }: SelectFilterProps) {
  return (
    <div className={cn('flex flex-col gap-1', className)}>
      <label className="text-xs text-muted-foreground font-medium">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  )
}

interface FilterBarProps {
  children: React.ReactNode
  className?: string
}

export function FilterBar({ children, className }: FilterBarProps) {
  return (
    <div className={cn('flex flex-wrap gap-4 items-end p-4 bg-muted/40 rounded-lg border', className)}>
      {children}
    </div>
  )
}
