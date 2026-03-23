import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

// ─── GET: Get conversation with all messages ────────────────────────

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: conversation, error: convError } = await supabase
    .from("conversations")
    .select("*")
    .eq("id", id)
    .single();

  if (convError || !conversation) {
    return NextResponse.json(
      { error: "Conversa não encontrada" },
      { status: 404 }
    );
  }

  const { data: messages, error: msgError } = await supabase
    .from("messages")
    .select("*")
    .eq("conversation_id", id)
    .order("created_at", { ascending: true });

  if (msgError) {
    return NextResponse.json(
      { error: "Erro ao carregar mensagens", details: msgError.message },
      { status: 500 }
    );
  }

  return NextResponse.json({ conversation, messages: messages || [] });
}

// ─── PATCH: Update conversation ─────────────────────────────────────

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: "Corpo da requisição inválido" },
      { status: 400 }
    );
  }

  const supabase = await createClient();

  // Only allow updating specific fields
  const allowedFields = [
    "status",
    "assigned_operator_id",
    "summary",
    "subject_classified",
    "category_classified",
    "scenario",
    "confidence",
    "escalation_channel",
    "turn_count",
  ];

  const updates: Record<string, unknown> = { updated_at: new Date().toISOString() };
  const bodyObj = body as Record<string, unknown>;

  for (const field of allowedFields) {
    if (field in bodyObj) {
      updates[field] = bodyObj[field];
    }
  }

  // Set resolved_at when status changes to resolved
  if (updates.status === "resolved") {
    updates.resolved_at = new Date().toISOString();
  }

  const { data, error } = await supabase
    .from("conversations")
    .update(updates)
    .eq("id", id)
    .select()
    .single();

  if (error) {
    return NextResponse.json(
      { error: "Erro ao atualizar conversa", details: error.message },
      { status: 500 }
    );
  }

  return NextResponse.json({ conversation: data });
}
