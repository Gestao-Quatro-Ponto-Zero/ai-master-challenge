import type { Lead } from "@/lib/types";
import { ScoreBadge, ActionBadge, IncompleteBadge } from "./ScoreBadge";
import { motion } from "framer-motion";
import { Pencil, AlertCircle } from "lucide-react";

const spring = { type: "spring" as const, stiffness: 300, damping: 30, mass: 1 };

const isFinalized = (stage: string) => stage === "Won" || stage === "Lost";

export function KanbanCard({ lead, onClick }: { lead: Lead; onClick?: () => void }) {
  const finalized = isFinalized(lead.deal_stage);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={spring}
      onClick={onClick}
      className={`group rounded-lg bg-card p-4 transition-all duration-150 cursor-pointer
        shadow-[0_0_0_1px_rgba(0,0,0,.05),0_1px_3px_0_rgba(0,0,0,.03)]
        hover:shadow-[0_0_0_1px_rgba(0,0,0,.1),0_6px_12px_0_rgba(0,0,0,.08)]
        hover:-translate-y-0.5
        ${finalized ? "opacity-55 saturate-50" : ""}
        ${lead.isIncomplete && !finalized ? "ring-1 ring-[hsl(var(--incomplete))]/30" : ""}`}
    >
      {/* Header with edit icon */}
      <div className="flex items-start justify-between gap-2 mb-1">
        <h3 className="text-sm font-bold text-card-foreground leading-tight truncate flex-1">
          {lead.account} — {lead.product}
        </h3>
        <Pencil className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-muted-foreground shrink-0 mt-0.5 transition-colors" />
      </div>

      {/* Line 2: Company + Product */}
      <p className="text-xs text-muted-foreground mb-2 truncate">
        {lead.account} · {lead.product}
      </p>

      {/* Line 3: Badges */}
      <div className="flex flex-wrap gap-1.5 mb-2">
        {!lead.isIncomplete && <ScoreBadge grade={lead.scoreGrade} />}
        <ActionBadge status={lead.actionStatus} />
        {lead.isIncomplete && <IncompleteBadge missingFields={lead.missingFields} />}
      </div>

      {/* CTA for incomplete */}
      {lead.isIncomplete && !finalized && (
        <div className="flex items-center gap-1.5 text-[11px] font-semibold text-[hsl(var(--action-fix))] mb-2">
          <AlertCircle className="w-3.5 h-3.5" />
          Completar dados
        </div>
      )}

      {/* Line 4: Metadata */}
      <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-[11px] text-muted-foreground mb-1.5">
        <span>Vendedor: {lead.sales_agent}</span>
        <span>Etapa: {lead.deal_stage}</span>
        <span>Setor: {lead.sector ?? "—"}</span>
        <span>Porte: {lead.employeeBucket ?? "—"}</span>
      </div>

      {/* Line 5: ID */}
      <p className="text-[10px] font-tabular text-muted-foreground/60 mb-1.5">
        ID: {lead.opportunity_id}
      </p>

      {/* Line 6: Score explanation */}
      {lead.scoreExplanation && (
        <p className="text-[10px] text-muted-foreground/80 italic leading-tight">
          {lead.scoreExplanation}
        </p>
      )}
    </motion.div>
  );
}
