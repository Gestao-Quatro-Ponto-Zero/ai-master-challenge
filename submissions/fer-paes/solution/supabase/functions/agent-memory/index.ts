import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  try {
    const url = new URL(req.url);

    if (req.method === "GET") {
      const action       = url.searchParams.get("action") ?? "list";
      const agentId      = url.searchParams.get("agent_id");
      const customerId   = url.searchParams.get("customer_id");
      const ticketId     = url.searchParams.get("ticket_id");
      const convId       = url.searchParams.get("conversation_id");
      const memType      = url.searchParams.get("memory_type");
      const runId        = url.searchParams.get("run_id");
      const limit        = parseInt(url.searchParams.get("limit") ?? "50");
      const offset       = parseInt(url.searchParams.get("offset") ?? "0");

      if (action === "stats") {
        const { data: counts } = await supabase
          .from("agent_memories")
          .select("memory_type");

        const stats: Record<string, number> = { conversation: 0, ticket: 0, customer: 0 };
        for (const row of counts ?? []) {
          stats[row.memory_type] = (stats[row.memory_type] ?? 0) + 1;
        }

        const { count: scratchpadCount } = await supabase
          .from("agent_scratchpads")
          .select("*", { count: "exact", head: true });

        return json({ stats, scratchpad_steps: scratchpadCount ?? 0 });
      }

      if (action === "scratchpads") {
        if (!runId) return json({ error: "run_id required" }, 400);
        const { data, error } = await supabase
          .from("agent_scratchpads")
          .select("*")
          .eq("run_id", runId)
          .order("step", { ascending: true });
        if (error) throw new Error(error.message);
        return json({ scratchpads: data ?? [] });
      }

      let query = supabase
        .from("agent_memories")
        .select(
          `id, memory_type, agent_id, ticket_id, conversation_id, customer_id,
           content, metadata, created_at, updated_at,
           agents!agent_id(name),
           customers!customer_id(name, email)`,
          { count: "exact" }
        )
        .order("updated_at", { ascending: false })
        .range(offset, offset + limit - 1);

      if (agentId)    query = query.eq("agent_id", agentId);
      if (customerId) query = query.eq("customer_id", customerId);
      if (ticketId)   query = query.eq("ticket_id", ticketId);
      if (convId)     query = query.eq("conversation_id", convId);
      if (memType)    query = query.eq("memory_type", memType);

      const { data, error, count } = await query;
      if (error) throw new Error(error.message);
      return json({ memories: data ?? [], total: count ?? 0 });
    }

    if (req.method === "POST") {
      const body = await req.json() as Record<string, unknown>;
      const action = (body.action as string) ?? "create";

      if (action === "create") {
        const { data, error } = await supabase
          .from("agent_memories")
          .insert({
            memory_type:     body.memory_type     as string,
            agent_id:        body.agent_id        as string | null ?? null,
            ticket_id:       body.ticket_id       as string | null ?? null,
            conversation_id: body.conversation_id as string | null ?? null,
            customer_id:     body.customer_id     as string | null ?? null,
            content:         body.content         as string,
            metadata:        body.metadata        as Record<string, unknown> ?? {},
          })
          .select()
          .single();

        if (error) throw new Error(error.message);
        return json({ memory: data });
      }

      if (action === "update") {
        const id = body.id as string;
        if (!id) return json({ error: "id required" }, 400);
        const { data, error } = await supabase
          .from("agent_memories")
          .update({
            content:  body.content  as string | undefined,
            metadata: body.metadata as Record<string, unknown> | undefined,
          })
          .eq("id", id)
          .select()
          .single();
        if (error) throw new Error(error.message);
        return json({ memory: data });
      }

      if (action === "delete") {
        const id = body.id as string;
        if (!id) return json({ error: "id required" }, 400);
        const { error } = await supabase.from("agent_memories").delete().eq("id", id);
        if (error) throw new Error(error.message);
        return json({ success: true });
      }

      return json({ error: "Unknown action" }, 400);
    }

    if (req.method === "DELETE") {
      const id = url.searchParams.get("id");
      if (!id) return json({ error: "id required" }, 400);
      const { error } = await supabase.from("agent_memories").delete().eq("id", id);
      if (error) throw new Error(error.message);
      return json({ success: true });
    }

    return json({ error: "Method not allowed" }, 405);
  } catch (err) {
    return json({ error: String(err) }, 500);
  }
});
