import { NextRequest, NextResponse } from "next/server";
import { z } from "zod/v4";
import { createClient } from "@/lib/supabase/server";

const StopInput = z.object({
  simulation_id: z.string().uuid("ID de simulação inválido"),
});

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

  const parsed = StopInput.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Dados inválidos", details: parsed.error.issues },
      { status: 400 }
    );
  }

  const { simulation_id } = parsed.data;
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("simulation_runs")
    .update({
      status: "cancelled",
      completed_at: new Date().toISOString(),
    })
    .eq("id", simulation_id)
    .select()
    .single();

  if (error || !data) {
    return NextResponse.json(
      { error: "Erro ao cancelar simulação", details: error?.message },
      { status: 500 }
    );
  }

  return NextResponse.json({ simulation: data });
}
