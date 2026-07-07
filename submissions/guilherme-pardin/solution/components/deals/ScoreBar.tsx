import { cn, tierColor } from "@/lib/utils";
import type { Tier } from "@/lib/types";

export function ScoreBar({
  score,
  tier,
  className,
  showLabel = true,
}: {
  score: number;
  tier: Tier;
  className?: string;
  showLabel?: boolean;
}) {
  const c = tierColor[tier];
  const pct = Math.max(0, Math.min(100, score));
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full", c.solid)}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-semibold tabular-nums text-slate-600 w-8 text-right">
          {score}
        </span>
      )}
    </div>
  );
}
