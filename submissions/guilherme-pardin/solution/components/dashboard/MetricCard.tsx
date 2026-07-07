import { cn } from "@/lib/utils";

export function MetricCard({
  label,
  value,
  hint,
  icon,
  accent = "bg-slate-100 text-slate-700",
  className,
}: {
  label: string;
  value: string | number;
  hint?: string;
  icon?: React.ReactNode;
  accent?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "bg-white border border-slate-200 rounded-lg p-4 shadow-[var(--shadow-metric)]",
        className,
      )}
    >
      <div className="flex items-center gap-2">
        {icon && (
          <div
            className={cn(
              "h-7 w-7 rounded-md grid place-items-center",
              accent,
            )}
          >
            {icon}
          </div>
        )}
        <div className="text-[11px] uppercase tracking-wide text-slate-500 font-medium">
          {label}
        </div>
      </div>
      <div className="text-2xl font-bold text-slate-900 tabular-nums mt-2 leading-tight">
        {value}
      </div>
      {hint && <div className="text-xs text-slate-500 mt-0.5">{hint}</div>}
    </div>
  );
}
