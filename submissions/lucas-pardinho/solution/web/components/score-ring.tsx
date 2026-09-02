import { scoreOf } from "@/lib/analytics";
import type { Opportunity } from "@/lib/types";

export function ScoreRing({ opportunity, size = "md" }: { opportunity: Opportunity; size?: "sm" | "md" | "lg" }) {
  const score = scoreOf(opportunity);
  const normalized = Math.max(0, Math.min(100, score ?? 0));

  return (
    <div
      className={`score-ring ${size} ${score === null ? "empty" : ""}`}
      style={{ "--score": `${normalized * 3.6}deg` } as React.CSSProperties}
      role="img"
      aria-label={score === null ? "Sem score de prioridade" : `Score ${Math.round(score)} de 100`}
    >
      <span>{score === null ? "—" : Math.round(score)}</span>
      {size === "lg" ? <small>{opportunity.priorityScore === null ? "qualificação" : "prioridade"}</small> : null}
    </div>
  );
}
