/**
 * GET    /api/admin/agents  — list all agents from sales_teams
 * POST   /api/admin/agents  — add a new agent
 * DELETE /api/admin/agents  — remove an agent by name
 */

import { NextRequest, NextResponse } from "next/server";
import { supabase, supabaseAdmin } from "@/lib/supabase";

export const dynamic = "force-dynamic";

export async function GET() {
  const { data, error } = await supabase
    .from("sales_teams")
    .select("sales_agent, manager, regional_office")
    .order("sales_agent");

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ agents: data ?? [] });
}

export async function POST(req: NextRequest) {
  const { sales_agent, manager, regional_office } = await req.json();

  if (!sales_agent?.trim()) {
    return NextResponse.json({ error: "Nome do vendedor é obrigatório" }, { status: 400 });
  }

  // Check duplicate
  const { data: existing } = await supabase
    .from("sales_teams")
    .select("sales_agent")
    .ilike("sales_agent", sales_agent.trim())
    .limit(1);

  if (existing && existing.length > 0) {
    return NextResponse.json({ error: "Vendedor já existe" }, { status: 409 });
  }

  const { error } = await supabaseAdmin.from("sales_teams").insert({
    sales_agent:     sales_agent.trim(),
    manager:         (manager ?? "").trim(),
    regional_office: (regional_office ?? "").trim(),
  });

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ success: true });
}

export async function DELETE(req: NextRequest) {
  const { sales_agent } = await req.json();

  if (!sales_agent) {
    return NextResponse.json({ error: "Nome é obrigatório" }, { status: 400 });
  }

  const { error } = await supabaseAdmin
    .from("sales_teams")
    .delete()
    .ilike("sales_agent", sales_agent);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ success: true });
}
