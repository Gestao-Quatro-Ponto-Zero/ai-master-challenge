import { cn } from "@/lib/utils";
import { useI18n } from "@/lib/i18n-context";
import { PRIORITY_STYLES } from "./priority";
import type { Priority } from "@/lib/types";

export function PriorityBadge({ priority, className }: { priority: Priority; className?: string }) {
  const { priority: priorityLabel } = useI18n();
  const s = PRIORITY_STYLES[priority];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide",
        s.bg,
        s.border,
        s.text,
        className,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", s.dot)} />
      {priorityLabel(priority)}
    </span>
  );
}

export function ScoreChip({
  score,
  priority,
  className,
}: {
  score: number;
  priority: Priority;
  className?: string;
}) {
  const s = PRIORITY_STYLES[priority];
  return (
    <span
      className={cn(
        "tabular inline-flex h-7 min-w-9 items-center justify-center rounded-md border px-1.5 text-sm font-bold",
        s.bg,
        s.border,
        s.text,
        className,
      )}
    >
      {score}
    </span>
  );
}
