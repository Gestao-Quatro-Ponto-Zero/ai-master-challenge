import { NextRequest, NextResponse } from "next/server";
import { z } from "zod/v4";
import { createClient } from "@/lib/supabase/server";

const ResolveInput = z.object({
  operator_id: z.string().uuid("ID de operador inválido"),
  csat_rating: z.number().int().min(1).max(5).optional(),
});

// ─── POST: Resolve a conversation ───────────────────────────────────

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: conversationId } = await params;

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: "Corpo da requisição inválido" },
      { status: 400 }
    );
  }

  const parsed = ResolveInput.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Dados inválidos", details: parsed.error.issues },
      { status: 400 }
    );
  }

  const { operator_id, csat_rating } = parsed.data;
  const supabase = await createClient();

  // Verify conversation
  const { data: conversation, error: convError } = await supabase
    .from("conversations")
    .select("id, status, assigned_operator_id")
    .eq("id", conversationId)
    .single();

  if (convError || !conversation) {
    return NextResponse.json(
      { error: "Conversa não encontrada" },
      { status: 404 }
    );
  }

  if (conversation.assigned_operator_id !== operator_id) {
    return NextResponse.json(
      { error: "Conversa não está atribuída a este operador" },
      { status: 400 }
    );
  }

  // Resolve conversation (with optional CSAT rating)
  const updatePayload: Record<string, unknown> = {
    status: "resolved",
    resolved_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  if (csat_rating !== undefined) {
    updatePayload.csat_rating = csat_rating;
  }

  const { data: updatedConv, error: updateError } = await supabase
    .from("conversations")
    .update(updatePayload)
    .eq("id", conversationId)
    .select()
    .single();

  if (updateError) {
    return NextResponse.json(
      { error: "Erro ao resolver conversa", details: updateError.message },
      { status: 500 }
    );
  }

  // Atomically decrement active_tickets, then increment total_resolved
  await supabase.rpc("decrement_active_tickets", { operator_id });

  const { data: operator } = await supabase
    .from("operators")
    .select("total_resolved")
    .eq("id", operator_id)
    .single();

  if (operator) {
    await supabase
      .from("operators")
      .update({
        total_resolved: (operator.total_resolved || 0) + 1,
      })
      .eq("id", operator_id);
  }

  return NextResponse.json({ conversation: updatedConv });
}
