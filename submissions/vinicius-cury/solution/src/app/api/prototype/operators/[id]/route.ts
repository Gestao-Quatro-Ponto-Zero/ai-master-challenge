import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

// ─── PATCH: Update operator status ──────────────────────────────────

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: "Corpo da requisição inválido" },
      { status: 400 }
    );
  }

  const supabase = await createClient();
  const bodyObj = body as Record<string, unknown>;

  // Allow updating status and level
  const updates: Record<string, unknown> = {};
  if ("status" in bodyObj) {
    const validStatuses = ["available", "busy", "offline"];
    if (!validStatuses.includes(bodyObj.status as string)) {
      return NextResponse.json(
        { error: "Status inválido" },
        { status: 400 }
      );
    }
    updates.status = bodyObj.status;
  }

  if ("level" in bodyObj) {
    const validLevels = ["junior", "senior", "lead"];
    if (!validLevels.includes(bodyObj.level as string)) {
      return NextResponse.json(
        { error: "Nível inválido. Use: junior, senior ou lead" },
        { status: 400 }
      );
    }
    updates.level = bodyObj.level;
  }

  if (Object.keys(updates).length === 0) {
    return NextResponse.json(
      { error: "Nenhum campo válido para atualizar" },
      { status: 400 }
    );
  }

  const { data, error } = await supabase
    .from("operators")
    .update(updates)
    .eq("id", id)
    .select()
    .single();

  if (error) {
    return NextResponse.json(
      { error: "Erro ao atualizar operador", details: error.message },
      { status: 500 }
    );
  }

  return NextResponse.json({ operator: data });
}
