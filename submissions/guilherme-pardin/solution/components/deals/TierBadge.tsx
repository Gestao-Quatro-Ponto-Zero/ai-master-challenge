import { Badge } from "@/components/ui/badge";
import { tierEmoji, tierLabel } from "@/lib/data";
import { cn, tierColor } from "@/lib/utils";
import type { Tier } from "@/lib/types";

export function TierBadge({ tier, className }: { tier: Tier; className?: string }) {
  const c = tierColor[tier];
  return (
    <Badge
      variant="outline"
      className={cn(
        "gap-1 border font-medium",
        c.bg,
        c.text,
        c.border,
        className,
      )}
    >
      <span>{tierEmoji[tier]}</span>
      {tierLabel[tier]}
    </Badge>
  );
}
