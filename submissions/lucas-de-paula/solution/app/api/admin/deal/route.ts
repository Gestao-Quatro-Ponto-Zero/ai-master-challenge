/**
 * PUT /api/admin/deal
 * Update an existing deal in Supabase.
 *
 * Body: {
 *   id: string              — opportunity_id (required)
 *   deal_stage?: string
 *   engage_date?: string    — YYYY-MM-DD
 *   close_date?: string     — YYYY-MM-DD
 *   close_value?: string
 * }
 */

import { NextRequest, NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";

export const dynamic = "force-dynamic";

export async function PUT(req: NextRequest) {
  const body = await req.json() as {
    id: string;
    deal_stage?: string;
    engage_date?: string;
    close_date?: string;
    close_value?: string;
  };

  const { id, deal_stage, engage_date, close_date, close_value } = body;
  if (!id) return NextResponse.json({ error: "ID obrigatório" }, { status: 400 });

  const updates: Record<string, unknown> = {};
  if (deal_stage  !== undefined) updates.deal_stage  = deal_stage;
  if (engage_date !== undefined) updates.engage_date = engage_date || null;
  if (close_date  !== undefined) updates.close_date  = close_date  || null;
  if (close_value !== undefined) updates.close_value = parseFloat(close_value) || 0;

  const { data, error } = await supabaseAdmin
    .from("sales_pipeline")
    .update(updates)
    .eq("opportunity_id", id)
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  if (!data)  return NextResponse.json({ error: "Deal não encontrado" }, { status: 404 });

  return NextResponse.json({ success: true });
}
