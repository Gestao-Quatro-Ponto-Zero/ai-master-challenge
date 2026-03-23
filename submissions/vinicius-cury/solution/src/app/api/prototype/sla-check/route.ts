import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { shouldAutoEscalate, escalateTicket } from "@/lib/prototype/escalation";

// ─── GET: Check SLAs and auto-escalate tickets at 80% threshold ─────

export async function GET() {
  const supabase = await createClient();

  // Query all conversations with SLA deadlines in active statuses
  const { data: conversations, error } = await supabase
    .from("conversations")
    .select("id, created_at, sla_deadline, assigned_operator_id, escalation_tier, status")
    .in("status", ["escalated", "waiting_operator", "in_progress"])
    .not("sla_deadline", "is", null);

  if (error) {
    return NextResponse.json(
      { error: "Erro ao verificar SLAs", details: error.message },
      { status: 500 }
    );
  }

  if (!conversations || conversations.length === 0) {
    return NextResponse.json({ checked: 0, escalated: 0, details: [] });
  }

  const escalationResults: Array<{
    conversation_id: string;
    from_operator: string | null;
    new_tier: number | null;
    new_operator: string | null;
    error?: string;
  }> = [];

  for (const conv of conversations) {
    const needsEscalation = await shouldAutoEscalate(
      conv as Record<string, unknown>,
      supabase
    );

    if (!needsEscalation) continue;

    // Only escalate if there is an assigned operator to escalate from
    const operatorId = conv.assigned_operator_id as string | null;
    if (!operatorId) continue;

    // Don't escalate if already at max tier
    const currentTier = (conv.escalation_tier as number) || 1;
    if (currentTier >= 3) continue;

    const result = await escalateTicket(conv.id, operatorId, supabase);

    escalationResults.push({
      conversation_id: conv.id,
      from_operator: operatorId,
      new_tier: result.newTier || null,
      new_operator: result.newOperator?.name || null,
      error: result.error,
    });
  }

  return NextResponse.json({
    checked: conversations.length,
    escalated: escalationResults.filter((r) => !r.error).length,
    details: escalationResults,
  });
}
