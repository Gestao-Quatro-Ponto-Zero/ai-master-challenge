import { NextResponse } from "next/server";
import { processNewTicket } from "@/lib/ticket-pipeline";
import { createServerClient } from "@/lib/supabase/server";
import type { CreateTicketInput } from "@/lib/ticket-pipeline";

export async function GET() {
  try {
    const supabase = createServerClient();
    const { data, error } = await supabase
      .from("tickets")
      .select("*")
      .order("created_at", { ascending: false });

    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Erro" },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as CreateTicketInput;
    const ticket = await processNewTicket(body);
    return NextResponse.json(ticket, { status: 201 });
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Erro ao criar ticket" },
      { status: 500 }
    );
  }
}
