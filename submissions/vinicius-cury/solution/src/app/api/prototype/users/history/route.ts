import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

// ─── GET: Fetch conversation history for a user by email ─────────────

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const email = searchParams.get("email");

  if (!email || !email.includes("@")) {
    return NextResponse.json(
      { error: "Email obrigatório e válido" },
      { status: 400 }
    );
  }

  const supabase = await createClient();

  // Get all conversations for this email, most recent first
  const { data: conversations, error } = await supabase
    .from("conversations")
    .select("id, channel, status, customer_name, subject_classified, category_classified, scenario, confidence, turn_count, summary, created_at, updated_at, resolved_at")
    .eq("customer_email", email.toLowerCase().trim())
    .order("created_at", { ascending: false });

  if (error) {
    return NextResponse.json(
      { error: "Erro ao buscar histórico", details: error.message },
      { status: 500 }
    );
  }

  // Compute user summary stats
  const total = conversations?.length || 0;
  const resolved = conversations?.filter((c) => c.status === "resolved").length || 0;
  const escalated = conversations?.filter((c) => c.status === "escalated").length || 0;
  const active = conversations?.filter((c) => c.status === "active" || c.status === "in_progress").length || 0;

  // Get unique categories and scenarios
  const categories = [...new Set(conversations?.map((c) => c.category_classified).filter(Boolean) || [])];
  const scenarios = [...new Set(conversations?.map((c) => c.scenario).filter(Boolean) || [])];

  return NextResponse.json({
    email: email.toLowerCase().trim(),
    stats: {
      total,
      resolved,
      escalated,
      active,
      categories,
      scenarios,
    },
    conversations: conversations || [],
  });
}
