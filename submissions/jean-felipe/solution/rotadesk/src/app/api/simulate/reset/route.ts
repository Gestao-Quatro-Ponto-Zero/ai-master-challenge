import { NextResponse } from "next/server";
import { createServerClient } from "@/lib/supabase/server";

export async function POST() {
  try {
    const supabase = createServerClient();
    const { error } = await supabase
      .from("tickets")
      .delete()
      .gte("created_at", "1970-01-01");

    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
    return NextResponse.json({ ok: true });
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Erro ao resetar" },
      { status: 500 }
    );
  }
}
