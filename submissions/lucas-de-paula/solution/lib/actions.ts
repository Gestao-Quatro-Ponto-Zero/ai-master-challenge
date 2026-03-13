/**
 * actions.ts — Shared action tag + urgency note logic
 *
 * Used by both DealTable and DealModal so the same recommendation
 * appears in the pipeline list AND in the deal detail popup.
 */

import { type ScoredDeal } from "@/lib/scoring";

const AVG_CLOSE_DAYS = 52; // historical avg cycle from insights data

export function getActionTag(deal: Pick<ScoredDeal, "deal_stage" | "days_in_stage" | "score" | "account">): {
  label: string;
  style: string;
} {
  if (deal.deal_stage === "Engaging" && deal.days_in_stage > 90)
    return { label: "💀 Revisar ou encerrar", style: "text-red-400 bg-red-500/10 border-red-500/25" };
  if (deal.deal_stage === "Engaging" && deal.days_in_stage > 30)
    return { label: "⚠️ Contato urgente", style: "text-amber-400 bg-amber-500/10 border-amber-500/25" };
  if (deal.deal_stage === "Engaging" && deal.score >= 70)
    return { label: "🚀 Prioridade máxima", style: "text-emerald-400 bg-emerald-500/10 border-emerald-500/25" };
  if (deal.deal_stage === "Engaging")
    return { label: "📋 Avançar proposta", style: "text-blue-400 bg-blue-500/10 border-blue-500/25" };
  if (deal.deal_stage === "Prospecting" && deal.account)
    return { label: "➡️ Mover p/ Engaging", style: "text-purple-400 bg-purple-500/10 border-purple-500/25" };
  return { label: "🔍 Qualificar conta", style: "text-gray-400 bg-gray-500/10 border-gray-500/25" };
}

export function getUrgencyNote(deal: Pick<ScoredDeal, "deal_stage" | "days_in_stage" | "score">): string | null {
  if (deal.deal_stage !== "Engaging") return null;
  const remaining = AVG_CLOSE_DAYS - deal.days_in_stage;
  if (deal.score >= 70 && deal.days_in_stage <= 30)
    return `⏱ ${remaining}d para fechar saudável`;
  if (deal.days_in_stage > 30 && deal.days_in_stage <= 90)
    return `${deal.days_in_stage - 30}d além do ideal`;
  return null;
}
