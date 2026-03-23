import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

/**
 * TEST-ONLY endpoint: Backdate a conversation's created_at and sla_deadline
 * to simulate SLA threshold conditions.
 *
 * POST /api/prototype/test/backdate
 * Body: { conversation_id, minutes_ago, sla_minutes }
 *
 * Sets created_at to (now - minutes_ago) and sla_deadline to
 * (created_at + sla_minutes), so the SLA is at (minutes_ago / sla_minutes * 100)% elapsed.
 */
export async function POST(request: NextRequest) {
  const body = await request.json();
  const { conversation_id, minutes_ago, sla_minutes } = body;

  if (!conversation_id || !minutes_ago || !sla_minutes) {
    return NextResponse.json(
      { error: "Missing required fields: conversation_id, minutes_ago, sla_minutes" },
      { status: 400 }
    );
  }

  const supabase = await createClient();

  const createdAt = new Date(Date.now() - minutes_ago * 60 * 1000).toISOString();
  const slaDeadline = new Date(
    Date.now() - minutes_ago * 60 * 1000 + sla_minutes * 60 * 1000
  ).toISOString();

  const pctUsed = minutes_ago / sla_minutes;

  const { error } = await supabase
    .from("conversations")
    .update({
      created_at: createdAt,
      sla_deadline: slaDeadline,
    })
    .eq("id", conversation_id);

  if (error) {
    return NextResponse.json(
      { error: "Failed to backdate", details: error.message },
      { status: 500 }
    );
  }

  return NextResponse.json({
    ok: true,
    conversation_id,
    created_at: createdAt,
    sla_deadline: slaDeadline,
    pct_used: Math.round(pctUsed * 100),
  });
}
