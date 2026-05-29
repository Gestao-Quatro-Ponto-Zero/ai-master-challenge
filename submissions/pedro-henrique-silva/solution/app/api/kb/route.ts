import { NextRequest } from "next/server";
import { fail, ok, readBody } from "@/lib/api";
import { isAdmin, getDemoUser } from "@/lib/auth";
import { createSupabaseAdminClient } from "@/lib/supabase/admin";
import { embedText } from "@/lib/vector-search";

type KbBody = {
  description?: string;
  resolution?: string;
  category?: string;
  priority?: string;
  channel?: string;
};

export async function GET(request: NextRequest) {
  const user = getDemoUser(request);
  if (!user || !isAdmin(user)) return fail("Acesso negado", 403);

  const supabase = createSupabaseAdminClient();
  if (!supabase) return fail("Supabase indisponível", 503);

  const { data, error } = await supabase
    .from("support_tickets_kb")
    .select("id, source_ticket_id, description, resolution, category, priority, channel, created_at")
    .order("created_at", { ascending: false });

  if (error) return fail(error.message, 500);
  return ok({ items: data ?? [], total: (data ?? []).length });
}

export async function POST(request: NextRequest) {
  const user = getDemoUser(request);
  if (!user || !isAdmin(user)) return fail("Acesso negado", 403);

  const body = await readBody<KbBody>(request);
  if (!body?.description || !body.resolution) return fail("description e resolution são obrigatórios", 400);

  const supabase = createSupabaseAdminClient();
  if (!supabase) return fail("Supabase indisponível", 503);

  const embedding = await embedText(`${body.description}\n${body.resolution}`);

  const { data, error } = await supabase
    .from("support_tickets_kb")
    .insert({
      description: body.description,
      resolution: body.resolution,
      category: body.category ?? "Other",
      priority: body.priority ?? "medium",
      channel: body.channel ?? "Web",
      embedding,
    })
    .select("id, source_ticket_id, description, resolution, category, priority, channel, created_at")
    .single();

  if (error) return fail(error.message, 500);
  return ok({ item: data }, 201);
}
