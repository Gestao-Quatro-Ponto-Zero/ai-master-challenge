import { NextResponse } from "next/server";
import { createServerClient } from "@/lib/supabase/server";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  try {
    const supabase = createServerClient();
    const { data, error } = await supabase
      .from("tickets")
      .select("*, ticket_messages(*)")
      .eq("id", id)
      .single();

    if (error) return NextResponse.json({ error: error.message }, { status: 404 });
    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Erro" },
      { status: 500 }
    );
  }
}

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  try {
    const body = await request.json();
    const supabase = createServerClient();

    const updates: Record<string, unknown> = {};
    if (body.status) updates.status = body.status;
    if (body.scenario) updates.scenario = body.scenario;
    if (body.resolved_by) {
      updates.resolved_by = body.resolved_by;
      updates.resolved_at = new Date().toISOString();
      updates.status = "closed";
      if (body.resolved_by === "auto_ia") updates.scenario = "auto_resolved";
    }

    const { data, error } = await supabase
      .from("tickets")
      .update(updates)
      .eq("id", id)
      .select()
      .single();

    if (error) return NextResponse.json({ error: error.message }, { status: 500 });

    if (body.status) {
      await supabase.from("ticket_events").insert({
        ticket_id: id,
        event_type: "status_changed",
        payload: updates,
      });
    }

    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Erro" },
      { status: 500 }
    );
  }
}
