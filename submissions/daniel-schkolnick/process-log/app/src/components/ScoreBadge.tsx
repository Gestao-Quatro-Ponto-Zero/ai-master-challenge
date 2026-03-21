import type { ScoreGrade, ActionStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const scoreStyles: Record<string, string> = {
  A: "bg-[hsl(var(--score-a))] text-[hsl(var(--score-a-foreground))]",
  B: "bg-[hsl(var(--score-b))] text-[hsl(var(--score-b-foreground))]",
  C: "bg-[hsl(var(--score-c))] text-[hsl(var(--score-c-foreground))]",
  D: "bg-[hsl(var(--score-d))] text-[hsl(var(--score-d-foreground))]",
  incomplete: "bg-[hsl(var(--incomplete))] text-[hsl(var(--incomplete-foreground))]",
};

const actionStyles: Record<ActionStatus, string> = {
  "Foco agora": "bg-[hsl(var(--action-focus))] text-[hsl(var(--action-focus-foreground))]",
  "Foco depois": "bg-[hsl(var(--action-later))] text-[hsl(var(--action-later-foreground))]",
  "Baixa prioridade": "bg-[hsl(var(--action-low))] text-[hsl(var(--action-low-foreground))]",
  "Corrigir cadastro": "bg-[hsl(var(--action-fix))] text-[hsl(var(--action-fix-foreground))]",
  "Ganho": "bg-[hsl(var(--chart-green))]/15 text-[hsl(var(--chart-green))]",
  "Perdido": "bg-muted text-muted-foreground",
};

export function ScoreBadge({ grade }: { grade: ScoreGrade | null }) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 badge-caps", scoreStyles[grade ?? "incomplete"])}>
      {grade ? `Score ${grade}` : "Incompleto"}
    </span>
  );
}

export function ActionBadge({ status }: { status: ActionStatus }) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 badge-caps", actionStyles[status])}>
      {status}
    </span>
  );
}

export function IncompleteBadge({ missingFields }: { missingFields: string[] }) {
  if (missingFields.length === 0) return null;
  const label = `Dados incompletos: ${missingFields.join(" e ")} ausente${missingFields.length > 1 ? "s" : ""}`;
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 badge-caps", scoreStyles.incomplete)}>
      {label}
    </span>
  );
}
