import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

// ─── GET: List all operators ────────────────────────────────────────

export async function GET() {
  const supabase = await createClient();

  const { data: operators, error } = await supabase
    .from("operators")
    .select("*")
    .order("name", { ascending: true });

  if (error) {
    return NextResponse.json(
      { error: "Erro ao carregar operadores", details: error.message },
      { status: 500 }
    );
  }

  return NextResponse.json({ operators: operators || [] });
}
