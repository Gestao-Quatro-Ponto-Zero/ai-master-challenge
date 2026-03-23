import { NextRequest, NextResponse } from "next/server";
import { z } from "zod/v4";
import { createClient } from "@/lib/supabase/server";
import { getOperatorTier } from "@/lib/prototype/escalation";

const TransferInput = z.object({
  conversation_id: z.string().uuid("ID de conversa inválido"),
  from_operator_id: z.string().uuid("ID de operador de origem inválido"),
  to_operator_id: z.string().uuid("ID de operador de destino inválido"),
});

// ─── POST: Transfer ticket between operators ────────────────────────

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: "Corpo da requisição inválido" },
      { status: 400 }
    );
  }

  const parsed = TransferInput.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Dados inválidos", details: parsed.error.issues },
      { status: 400 }
    );
  }

  const { conversation_id, from_operator_id, to_operator_id } = parsed.data;
  const supabase = await createClient();

  // Verify conversation
  const { data: conversation, error: convError } = await supabase
    .from("conversations")
    .select("id, assigned_operator_id, escalation_tier, escalated_from_operator")
    .eq("id", conversation_id)
    .single();

  if (convError || !conversation) {
    return NextResponse.json(
      { error: "Conversa não encontrada" },
      { status: 404 }
    );
  }

  if (conversation.assigned_operator_id !== from_operator_id) {
    return NextResponse.json(
      { error: "Conversa não está atribuída a este operador" },
      { status: 400 }
    );
  }

  // Get source operator level
  const { data: fromOp } = await supabase
    .from("operators")
    .select("id, level")
    .eq("id", from_operator_id)
    .single();

  // Verify target operator capacity
  const { data: toOperator, error: toError } = await supabase
    .from("operators")
    .select("id, active_tickets, max_capacity, level")
    .eq("id", to_operator_id)
    .single();

  if (toError || !toOperator) {
    return NextResponse.json(
      { error: "Operador de destino não encontrado" },
      { status: 404 }
    );
  }

  if ((toOperator.active_tickets || 0) >= (toOperator.max_capacity || 5)) {
    return NextResponse.json(
      { error: "Operador de destino está na capacidade máxima" },
      { status: 400 }
    );
  }

  // Check direction: prevent downward transfers (senior cannot transfer to junior)
  const fromTier = getOperatorTier(fromOp?.level || "junior");
  const toTier = getOperatorTier(toOperator.level || "junior");

  if (toTier < fromTier) {
    return NextResponse.json(
      { error: "Não é permitido transferir para um operador de nível inferior" },
      { status: 400 }
    );
  }

  // If transferring UP (escalation), increment escalation_tier
  const currentEscalationTier = (conversation.escalation_tier as number) || 1;
  const isEscalation = toTier > fromTier;
  const newEscalationTier = isEscalation
    ? Math.max(currentEscalationTier, toTier)
    : currentEscalationTier;

  // Transfer: update conversation
  const { data: updatedConv, error: updateError } = await supabase
    .from("conversations")
    .update({
      assigned_operator_id: to_operator_id,
      escalation_tier: newEscalationTier,
      escalated_from_operator: isEscalation ? from_operator_id : conversation.escalated_from_operator,
      updated_at: new Date().toISOString(),
    })
    .eq("id", conversation_id)
    .select()
    .single();

  if (updateError) {
    return NextResponse.json(
      { error: "Erro ao transferir conversa", details: updateError.message },
      { status: 500 }
    );
  }

  // Atomically decrement source operator, increment target operator
  await supabase.rpc("decrement_active_tickets", { operator_id: from_operator_id });
  await supabase.rpc("increment_active_tickets", { operator_id: to_operator_id });

  return NextResponse.json({ conversation: updatedConv });
}
