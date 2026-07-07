import { cn } from "@/lib/utils";

export function HorizontalBar({
  label,
  value,
  max,
  displayValue,
  hint,
  color = "bg-blue-500",
  labelWidth = "w-40",
}: {
  label: string;
  value: number;
  max: number;
  displayValue: string;
  hint?: string;
  color?: string;
  labelWidth?: string;
}) {
  const pct = max ? Math.max(2, (value / max) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <div className={cn("shrink-0 text-sm text-slate-700 truncate", labelWidth)}>
        {label}
      </div>
      <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full", color)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="shrink-0 text-right min-w-[80px]">
        <div className="text-sm font-semibold text-slate-900 tabular-nums leading-tight">
          {displayValue}
        </div>
        {hint && (
          <div className="text-[10px] text-slate-400 tabular-nums">{hint}</div>
        )}
      </div>
    </div>
  );
}
