import type { Priority, ScoredDeal } from "@/lib/types";
import type { QuickFilter } from "./FilterBar";

export const PRIORITY_STYLES: Record<
  Priority,
  { text: string; bg: string; border: string; dot: string; label: string }
> = {
  High: {
    text: "text-gold",
    bg: "bg-gold/15",
    border: "border-gold/40",
    dot: "bg-gold",
    label: "High priority",
  },
  Priority: {
    text: "text-success",
    bg: "bg-success/15",
    border: "border-success/40",
    dot: "bg-success",
    label: "Priority",
  },
  Watch: {
    text: "text-warning",
    bg: "bg-warning/15",
    border: "border-warning/40",
    dot: "bg-warning",
    label: "Watch",
  },
  Low: {
    text: "text-muted-foreground",
    bg: "bg-muted",
    border: "border-border",
    dot: "bg-muted-foreground",
    label: "Low",
  },
};

export function priorityFor(score: number): Priority {
  if (score >= 80) return "High";
  if (score >= 60) return "Priority";
  if (score >= 40) return "Watch";
  return "Low";
}

const ACTIONABLE = new Set([
  "callToday",
  "engageBuyer",
  "followUp",
  "qualify",
  "managerReview",
  "revive",
]);

/** Quick-filter predicate; combines (AND) with the existing selects. */
export function matchesQuick(d: ScoredDeal, quick: QuickFilter): boolean {
  switch (quick) {
    case "act_now":
      return (
        (d.priority === "High" || d.priority === "Priority") && ACTIONABLE.has(d.nextActionCode)
      );
    case "high_score":
      return d.score >= 75;
    case "cooling_risk":
      return d.risks.some((r) => r.code === "cooling_risk");
    case "manager_review":
      return d.nextActionCode === "managerReview";
    case "engaging":
      return d.stage === "Engaging";
    case "prospecting":
      return d.stage === "Prospecting";
    default:
      return true;
  }
}
