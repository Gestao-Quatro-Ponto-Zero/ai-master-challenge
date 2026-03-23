import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

export async function GET() {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("experiment_results")
    .select("*")
    .order("d2_category", { ascending: true })
    .order("id", { ascending: true });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(data);
}

export async function PATCH(request: Request) {
  const supabase = await createClient();
  const body = await request.json();

  const { id, human_evaluation, human_correct_subject, human_notes } = body;

  if (!id || !human_evaluation) {
    return NextResponse.json(
      { error: "id and human_evaluation are required" },
      { status: 400 }
    );
  }

  const { data, error } = await supabase
    .from("experiment_results")
    .update({
      human_evaluation,
      human_correct_subject: human_correct_subject || null,
      human_notes: human_notes || null,
      evaluated_at: new Date().toISOString(),
    })
    .eq("id", id)
    .select()
    .single();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(data);
}
