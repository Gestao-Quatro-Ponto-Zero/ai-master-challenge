import { NextRequest } from "next/server";
import { fail, ok, readBody } from "@/lib/api";
import { isAdmin, getDemoUser } from "@/lib/auth";
import { createSupabaseAdminClient } from "@/lib/supabase/admin";
import { embedText } from "@/lib/vector-search";

type KbUpdateBody = {
  description?: string;
  resolution?: string;
  category?: string;
  priority?: string;
  channel?: string;
};

export async function PUT(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const user = getDemoUser(request);
  if (!user || !isAdmin(user)) return fail("Acesso negado", 403);

  const { id } = await params;
  const numId = parseInt(id, 10);
  if (isNaN(numId)) return fail("ID inválido", 400);

  const body = await readBody<KbUpdateBody>(request);
  if (!body) return fail("Body inválido", 400);

  const supabase = createSupabaseAdminClient();
  if (!supabase) return fail("Supabase indisponível", 503);

  const updates: Record<string, unknown> = {};
  if (body.description !== undefined) updates.description = body.description;
  if (body.resolution !== undefined) updates.resolution = body.resolution;
  if (body.category !== undefined) updates.category = body.category;
  if (body.priority !== undefined) updates.priority = body.priority;
  if (body.channel !== undefined) updates.channel = body.channel;

  if (Object.keys(updates).length === 0) return fail("Nenhum campo para atualizar", 400);

  if (body.description !== undefined || body.resolution !== undefined) {
    const { data: current } = await supabase
      .from("support_tickets_kb")
      .select("description, resolution")
      .eq("id", numId)
      .single();

    const desc = body.description ?? current?.description ?? "";
    const res = body.resolution ?? current?.resolution ?? "";
    updates.embedding = await embedText(`${desc}\n${res}`);
  }

  const { data, error } = await supabase
    .from("support_tickets_kb")
    .update(updates)
    .eq("id", numId)
    .select("id, source_ticket_id, description, resolution, category, priority, channel, created_at")
    .single();

  if (error) return fail(error.message, 500);
  return ok({ item: data });
}

export async function DELETE(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const user = getDemoUser(request);
  if (!user || !isAdmin(user)) return fail("Acesso negado", 403);

  const { id } = await params;
  const numId = parseInt(id, 10);
  if (isNaN(numId)) return fail("ID inválido", 400);

  const supabase = createSupabaseAdminClient();
  if (!supabase) return fail("Supabase indisponível", 503);

  const { error } = await supabase.from("support_tickets_kb").delete().eq("id", numId);
  if (error) return fail(error.message, 500);

  return ok({ deleted: true });
}
