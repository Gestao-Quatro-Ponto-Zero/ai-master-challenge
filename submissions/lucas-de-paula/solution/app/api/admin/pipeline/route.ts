/**
 * /api/admin/pipeline
 *
 * GET    — pipeline stats (total, active, won, lost)
 * POST   — upload CSV { csv: string, mode: "replace" | "append" }
 * PATCH  — add single deal { opportunity_id?, sales_agent, product, ... }
 * DELETE — remove deal by id { id: string }
 */

import { NextRequest, NextResponse } from "next/server";
import { loadDeals } from "@/lib/data";
import { supabaseAdmin } from "@/lib/supabase";

export const dynamic = "force-dynamic";

const REQUIRED_HEADERS = [
  "opportunity_id", "sales_agent", "product", "account",
  "deal_stage", "engage_date", "close_date", "close_value",
];

// ── GET — stats ───────────────────────────────────────────────────────────────
export async function GET() {
  const deals = await loadDeals();
  const active = deals.filter((d) => d.deal_stage === "Engaging" || d.deal_stage === "Prospecting").length;
  const won    = deals.filter((d) => d.deal_stage === "Won").length;
  const lost   = deals.filter((d) => d.deal_stage === "Lost").length;
  return NextResponse.json({ total: deals.length, active, won, lost });
}

// ── POST — upload CSV ─────────────────────────────────────────────────────────
export async function POST(req: NextRequest) {
  const { csv, mode } = await req.json() as { csv: string; mode: "replace" | "append" };

  const lines = csv.trim().split("\n");
  if (lines.length < 2) {
    return NextResponse.json({ error: "CSV deve ter pelo menos uma linha de dados além do cabeçalho." }, { status: 400 });
  }

  // Normalize: strip BOM, carriage returns, surrounding quotes
  const normalize = (s: string) =>
    s.replace(/^\uFEFF/, "").replace(/\r/g, "").replace(/^["']|["']$/g, "").trim().toLowerCase();

  // Auto-detect delimiter: semicolon (BR/Excel), tab, or comma
  const firstLine = lines[0].replace(/\r/g, "").replace(/^\uFEFF/, "");
  const sep = firstLine.includes(";") ? ";" : firstLine.includes("\t") ? "\t" : ",";

  const headers = firstLine.split(sep).map(normalize);
  const missing = REQUIRED_HEADERS.filter((h) => !headers.includes(h));
  if (missing.length > 0) {
    return NextResponse.json({ error: `Colunas obrigatórias faltando: ${missing.join(", ")}` }, { status: 400 });
  }

  const rows = lines.slice(1).map((line) => {
    const values = line.split(sep).map((v) => v.replace(/\r/g, "").replace(/^["']|["']$/g, "").trim());
    const obj: Record<string, string> = {};
    headers.forEach((h, i) => { obj[h] = values[i] ?? ""; });
    return {
      opportunity_id: obj.opportunity_id,
      sales_agent:    obj.sales_agent,
      product:        obj.product,
      account:        obj.account,
      deal_stage:     obj.deal_stage,
      engage_date:    obj.engage_date || null,
      close_date:     obj.close_date  || null,
      close_value:    parseFloat(obj.close_value) || 0,
    };
  }).filter((r) => r.opportunity_id);

  if (mode === "replace") {
    await supabaseAdmin.from("sales_pipeline").delete().neq("opportunity_id", "");
  }

  const { error } = await supabaseAdmin.from("sales_pipeline").upsert(rows, { onConflict: "opportunity_id" });
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json({ success: true, rows: rows.length });
}

// ── PATCH — add single deal ───────────────────────────────────────────────────
export async function PATCH(req: NextRequest) {
  const deal = await req.json();

  if (!deal.opportunity_id) {
    deal.opportunity_id = Math.random().toString(36).substring(2, 10).toUpperCase();
  }

  const { error } = await supabaseAdmin.from("sales_pipeline").insert({
    opportunity_id: deal.opportunity_id,
    sales_agent:    deal.sales_agent,
    product:        deal.product,
    account:        deal.account ?? "",
    deal_stage:     deal.deal_stage,
    engage_date:    deal.engage_date || null,
    close_date:     deal.close_date  || null,
    close_value:    parseFloat(deal.close_value) || 0,
  });

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ success: true, opportunity_id: deal.opportunity_id });
}

// ── DELETE — remove deal ──────────────────────────────────────────────────────
export async function DELETE(req: NextRequest) {
  const { id } = await req.json() as { id: string };
  if (!id) return NextResponse.json({ error: "ID obrigatório" }, { status: 400 });

  const { error } = await supabaseAdmin
    .from("sales_pipeline")
    .delete()
    .eq("opportunity_id", id);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ success: true });
}
