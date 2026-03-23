import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get("id");

  if (!id) {
    return NextResponse.json(
      { error: "Parâmetro 'id' obrigatório" },
      { status: 400 }
    );
  }

  const supabase = await createClient();

  const { data, error } = await supabase
    .from("simulation_runs")
    .select("*")
    .eq("id", id)
    .single();

  if (error || !data) {
    return NextResponse.json(
      { error: "Simulação não encontrada", details: error?.message },
      { status: 404 }
    );
  }

  return NextResponse.json({
    id: data.id,
    status: data.status,
    config: data.config,
    tickets_generated: data.tickets_generated,
    tickets_classified: data.tickets_classified,
    tickets_resolved: data.tickets_resolved,
    started_at: data.started_at,
    completed_at: data.completed_at,
  });
}
