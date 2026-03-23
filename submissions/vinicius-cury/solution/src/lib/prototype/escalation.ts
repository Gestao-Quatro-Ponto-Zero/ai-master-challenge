import { createClient } from "@/lib/supabase/server";

// ─── Tier Mapping ───────────────────────────────────────────────────

type OperatorLevel = "junior" | "senior" | "lead";

const TIER_MAP: Record<OperatorLevel, number> = {
  junior: 1,
  senior: 2,
  lead: 3,
};

export function getOperatorTier(level: string): number {
  return TIER_MAP[level as OperatorLevel] ?? 1;
}

// ─── Find Best Operator ─────────────────────────────────────────────

/**
 * Query available operators matching specialty + minimum tier.
 * Prefers lower tier first (don't waste senior on junior work), then checks capacity.
 */
export async function findBestOperator(
  scenario: string | null,
  category: string | null,
  requiredTier: number,
  supabase: Awaited<ReturnType<typeof createClient>>
): Promise<{
  id: string;
  name: string;
  level: string;
  tier: number;
} | null> {
  // Fetch all operators with remaining capacity (regardless of status label)
  const { data: operators } = await supabase
    .from("operators")
    .select("id, name, level, specialties, active_tickets, max_capacity, status");

  if (!operators || operators.length === 0) return null;

  // Filter by minimum tier and capacity
  const eligible = operators
    .filter((op) => {
      const tier = getOperatorTier(op.level || "junior");
      if (tier < requiredTier) return false;
      if ((op.active_tickets || 0) >= (op.max_capacity || 5)) return false;
      return true;
    })
    .map((op) => {
      const tier = getOperatorTier(op.level || "junior");
      // Score: prefer matching specialty, then lower tier, then more capacity
      const specialties = (op.specialties as string[]) || [];
      const hasSpecialty = category
        ? specialties.some((s) => s.toLowerCase().includes((category || "").toLowerCase()))
        : false;

      return {
        ...op,
        tier,
        hasSpecialty,
        availableCapacity: (op.max_capacity || 5) - (op.active_tickets || 0),
      };
    })
    .sort((a, b) => {
      // 1. Specialty match first
      if (a.hasSpecialty && !b.hasSpecialty) return -1;
      if (!a.hasSpecialty && b.hasSpecialty) return 1;
      // 2. Lower tier preferred (don't waste senior resources)
      if (a.tier !== b.tier) return a.tier - b.tier;
      // 3. More available capacity
      return b.availableCapacity - a.availableCapacity;
    });

  if (eligible.length === 0) return null;

  const best = eligible[0];
  return {
    id: best.id,
    name: best.name,
    level: best.level || "junior",
    tier: best.tier,
  };
}

// ─── SLA Auto-Escalation Check ──────────────────────────────────────

/**
 * Check if a conversation's SLA is at 80% threshold → should escalate to next tier.
 */
export async function shouldAutoEscalate(
  conversation: Record<string, unknown>,
  _supabase: Awaited<ReturnType<typeof createClient>>
): Promise<boolean> {
  if (!conversation.sla_deadline) return false;

  const now = Date.now();
  const deadline = new Date(conversation.sla_deadline as string).getTime();
  const createdAt = new Date(conversation.created_at as string).getTime();
  const totalSlaMs = deadline - createdAt;
  const remainingMs = deadline - now;

  if (totalSlaMs <= 0) return false;

  const pctUsed = 1 - remainingMs / totalSlaMs;

  // If 80% of SLA time has been used → escalate
  return pctUsed >= 0.8;
}

// ─── Escalate Ticket ────────────────────────────────────────────────

/**
 * Find next-tier operator, transfer ticket, update conversation escalation_tier.
 */
export async function escalateTicket(
  conversationId: string,
  fromOperatorId: string,
  supabase: Awaited<ReturnType<typeof createClient>>
): Promise<{
  success: boolean;
  newOperator?: { id: string; name: string; level: string };
  newTier?: number;
  error?: string;
}> {
  // Get current conversation
  const { data: conversation } = await supabase
    .from("conversations")
    .select("id, escalation_tier, category_classified, scenario, assigned_operator_id")
    .eq("id", conversationId)
    .single();

  if (!conversation) {
    return { success: false, error: "Conversa não encontrada" };
  }

  // Get current operator tier
  const { data: fromOperator } = await supabase
    .from("operators")
    .select("id, level, active_tickets")
    .eq("id", fromOperatorId)
    .single();

  const currentTier = conversation.escalation_tier || 1;
  const nextTier = currentTier + 1;

  if (nextTier > 3) {
    return { success: false, error: "Já está no nível máximo de escalação" };
  }

  // Find best operator at next tier
  const bestOperator = await findBestOperator(
    conversation.scenario as string | null,
    conversation.category_classified as string | null,
    nextTier,
    supabase
  );

  if (!bestOperator) {
    return { success: false, error: "Nenhum operador disponível no próximo nível" };
  }

  // Update conversation
  await supabase
    .from("conversations")
    .update({
      escalation_tier: nextTier,
      escalated_from_operator: fromOperatorId,
      assigned_operator_id: bestOperator.id,
      updated_at: new Date().toISOString(),
    })
    .eq("id", conversationId);

  // Atomically decrement source operator active_tickets
  if (fromOperator) {
    await supabase.rpc("decrement_active_tickets", { operator_id: fromOperatorId });
  }

  // Atomically increment target operator active_tickets
  await supabase.rpc("increment_active_tickets", { operator_id: bestOperator.id });

  return {
    success: true,
    newOperator: bestOperator,
    newTier: nextTier,
  };
}
