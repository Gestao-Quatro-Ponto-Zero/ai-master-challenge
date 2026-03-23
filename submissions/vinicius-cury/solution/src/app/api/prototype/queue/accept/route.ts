import { NextRequest, NextResponse } from "next/server";
import { z } from "zod/v4";
import { createClient } from "@/lib/supabase/server";
import { getOperatorTier } from "@/lib/prototype/escalation";

const AcceptInput = z.object({
  conversation_id: z.string().uuid("ID de conversa inválido"),
  operator_id: z.string().uuid("ID de operador inválido"),
});

// ─── POST: Operator accepts a ticket from the queue ─────────────────

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

  const parsed = AcceptInput.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Dados inválidos", details: parsed.error.issues },
      { status: 400 }
    );
  }

  const { conversation_id, operator_id } = parsed.data;
  const supabase = await createClient();

  // Verify conversation exists and is in an acceptable state
  const { data: conversation, error: convError } = await supabase
    .from("conversations")
    .select("id, status, assigned_operator_id, escalation_tier, category_classified")
    .eq("id", conversation_id)
    .single();

  if (convError || !conversation) {
    return NextResponse.json(
      { error: "Conversa não encontrada" },
      { status: 404 }
    );
  }

  if (
    conversation.status !== "escalated" &&
    conversation.status !== "waiting_operator"
  ) {
    return NextResponse.json(
      { error: "Conversa não está disponível para aceitar" },
      { status: 400 }
    );
  }

  // Verify operator exists
  const { data: operator, error: opError } = await supabase
    .from("operators")
    .select("id, active_tickets, max_capacity, level, specialties")
    .eq("id", operator_id)
    .single();

  if (opError || !operator) {
    return NextResponse.json(
      { error: "Operador não encontrado" },
      { status: 404 }
    );
  }

  if ((operator.active_tickets || 0) >= (operator.max_capacity || 5)) {
    return NextResponse.json(
      { error: "Operador já está na capacidade máxima" },
      { status: 400 }
    );
  }

  // Validate operator tier >= ticket escalation_tier
  const operatorTier = getOperatorTier(operator.level || "junior");
  const ticketTier = (conversation.escalation_tier as number) || 1;
  if (operatorTier < ticketTier) {
    return NextResponse.json(
      {
        error: `Operador nível ${operator.level || "junior"} não pode aceitar ticket de nível ${ticketTier}`,
      },
      { status: 400 }
    );
  }

  // Validate operator has matching specialty for the ticket's category
  const operatorSpecialties = (operator.specialties as string[]) || [];
  const ticketCategory = conversation.category_classified as string | null;
  if (ticketCategory && operatorSpecialties.length > 0) {
    const hasMatch = operatorSpecialties.some(
      (s) => s.toLowerCase().includes(ticketCategory.toLowerCase())
    );
    // Warn but don't block — specialty is a preference, not a hard requirement
    // This allows flexibility when no specialist is available
    if (!hasMatch) {
      // Continue with acceptance but log mismatch in response
    }
  }

  // Update conversation (set accepted_at for AHT calculation)
  const { data: updatedConv, error: updateError } = await supabase
    .from("conversations")
    .update({
      status: "in_progress",
      assigned_operator_id: operator_id,
      accepted_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
    .eq("id", conversation_id)
    .select()
    .single();

  if (updateError) {
    return NextResponse.json(
      { error: "Erro ao aceitar conversa", details: updateError.message },
      { status: 500 }
    );
  }

  // Atomically increment operator active_tickets
  await supabase.rpc("increment_active_tickets", { operator_id });

  return NextResponse.json({ conversation: updatedConv });
}
