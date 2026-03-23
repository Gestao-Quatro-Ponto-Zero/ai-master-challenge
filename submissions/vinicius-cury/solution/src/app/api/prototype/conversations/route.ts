import { NextRequest, NextResponse } from "next/server";
import { z } from "zod/v4";
import { createClient } from "@/lib/supabase/server";
import { IDENTITY_MESSAGES } from "@/lib/prototype/identity-flow";

// ─── Input Validation ────────────────────────────────────────────────

const CreateConversationInput = z.object({
  channel: z.string().min(1, "Canal obrigatório"),
  customer_name: z.string().optional(),
  customer_email: z.string().optional(),
  // When true, skip identity flow (used by simulation)
  skip_identity: z.boolean().optional(),
});

// ─── POST: Create new conversation ──────────────────────────────────

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

  const parsed = CreateConversationInput.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Dados inválidos", details: parsed.error.issues },
      { status: 400 }
    );
  }

  const { channel, customer_name, customer_email, skip_identity } = parsed.data;
  const supabase = await createClient();

  // Determine identity state based on caller
  const isSimulation = skip_identity || (!!customer_name && customer_name !== "Cliente");
  const identityState = isSimulation ? "support" : "greeting";

  // Create conversation
  const { data: conversation, error: convError } = await supabase
    .from("conversations")
    .insert({
      channel,
      customer_name: customer_name || null,
      customer_email: customer_email || null,
      status: "active",
      turn_count: 0,
      identity_state: identityState,
    })
    .select()
    .single();

  if (convError || !conversation) {
    return NextResponse.json(
      { error: "Erro ao criar conversa", details: convError?.message },
      { status: 500 }
    );
  }

  // Insert welcome message
  const welcomeContent = isSimulation
    ? "Olá! Sou o assistente virtual da OptiFlow. Como posso ajudá-lo hoje?"
    : IDENTITY_MESSAGES.welcome;

  const { data: welcomeMessage, error: msgError } = await supabase
    .from("messages")
    .insert({
      conversation_id: conversation.id,
      role: "assistant",
      content: welcomeContent,
    })
    .select()
    .single();

  if (msgError) {
    return NextResponse.json(
      { error: "Erro ao criar mensagem de boas-vindas", details: msgError.message },
      { status: 500 }
    );
  }

  return NextResponse.json({
    conversation,
    messages: [welcomeMessage],
  });
}

// ─── GET: List conversations ────────────────────────────────────────

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const status = searchParams.get("status");
  const email = searchParams.get("email");
  const category = searchParams.get("category");
  const scenario = searchParams.get("scenario");
  const operator = searchParams.get("operator");
  const limit = searchParams.get("limit");

  const supabase = await createClient();

  let query = supabase
    .from("conversations")
    .select("*")
    .order("created_at", { ascending: false });

  if (status) {
    query = query.eq("status", status);
  }

  if (email) {
    query = query.eq("customer_email", email);
  }

  if (category) {
    query = query.eq("category_classified", category);
  }

  if (scenario) {
    query = query.eq("scenario", scenario);
  }

  if (operator) {
    if (operator === "ia") {
      query = query.is("assigned_operator_id", null);
    } else {
      query = query.eq("assigned_operator_id", operator);
    }
  }

  if (limit) {
    query = query.limit(parseInt(limit, 10));
  }

  const { data, error } = await query;

  if (error) {
    return NextResponse.json(
      { error: "Erro ao listar conversas", details: error.message },
      { status: 500 }
    );
  }

  return NextResponse.json({ conversations: data });
}
