import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
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
    const url    = new URL(req.url);
    const action = url.searchParams.get("action") ?? "metrics";

    if (action === "metrics") {
      const { data, error } = await supabase.rpc("get_agents_metrics_summary");
      if (error) throw new Error(error.message);
      return json({ metrics: data ?? [] });
    }

    if (action === "overview") {
      const days = parseInt(url.searchParams.get("days") ?? "7");

      const [summary, timeline, toolUsage] = await Promise.all([
        supabase
          .from("agent_execution_logs")
          .select("status, latency_ms, input_tokens, output_tokens, tool_calls_count")
          .gte("created_at", new Date(Date.now() - days * 86400000).toISOString()),
        supabase.rpc("get_execution_timeline", { p_days: days }),
        supabase.rpc("get_tool_usage_summary"),
      ]);

      const rows = summary.data ?? [];
      const total    = rows.length;
      const success  = rows.filter((r: Record<string,unknown>) => r.status === "success").length;
      const avgLat   = total > 0 ? Math.round(rows.reduce((a: number, r: Record<string,unknown>) => a + (r.latency_ms as number), 0) / total) : 0;
      const tokensIn  = rows.reduce((a: number, r: Record<string,unknown>) => a + (r.input_tokens  as number), 0);
      const tokensOut = rows.reduce((a: number, r: Record<string,unknown>) => a + (r.output_tokens as number), 0);
      const toolCalls = rows.reduce((a: number, r: Record<string,unknown>) => a + (r.tool_calls_count as number), 0);

      return json({
        overview: {
          total_runs:     total,
          successful_runs: success,
          failed_runs:    total - success,
          success_rate:   total > 0 ? Math.round((success / total) * 1000) / 10 : 0,
          avg_latency_ms: avgLat,
          total_tokens:   tokensIn + tokensOut,
          input_tokens:   tokensIn,
          output_tokens:  tokensOut,
          total_tool_calls: toolCalls,
        },
        timeline:   timeline.data  ?? [],
        tool_usage: toolUsage.data ?? [],
      });
    }

    if (action === "executions") {
      const agentId = url.searchParams.get("agent_id");
      const ticketId = url.searchParams.get("ticket_id");
      const status  = url.searchParams.get("status");
      const limit   = parseInt(url.searchParams.get("limit")  ?? "50");
      const offset  = parseInt(url.searchParams.get("offset") ?? "0");

      let query = supabase
        .from("agent_execution_logs")
        .select(
          `id, agent_id, run_id, ticket_id, conversation_id,
           model_provider, model_name, latency_ms,
           input_tokens, output_tokens, tool_calls_count,
           iterations, status, error_message, created_at,
           agents!agent_id(name, type)`,
          { count: "exact" }
        )
        .order("created_at", { ascending: false })
        .range(offset, offset + limit - 1);

      if (agentId)  query = query.eq("agent_id", agentId);
      if (ticketId) query = query.eq("ticket_id", ticketId);
      if (status)   query = query.eq("status", status);

      const { data, error, count } = await query;
      if (error) throw new Error(error.message);
      return json({ executions: data ?? [], total: count ?? 0 });
    }

    if (action === "tool-calls") {
      const runId   = url.searchParams.get("run_id");
      const agentId = url.searchParams.get("agent_id");
      const limit   = parseInt(url.searchParams.get("limit")  ?? "100");
      const offset  = parseInt(url.searchParams.get("offset") ?? "0");

      let query = supabase
        .from("agent_tool_calls")
        .select("id, run_id, agent_id, tool_name, arguments, result, latency_ms, success, created_at", { count: "exact" })
        .order("created_at", { ascending: false })
        .range(offset, offset + limit - 1);

      if (runId)   query = query.eq("run_id", runId);
      if (agentId) query = query.eq("agent_id", agentId);

      const { data, error, count } = await query;
      if (error) throw new Error(error.message);
      return json({ tool_calls: data ?? [], total: count ?? 0 });
    }

    if (action === "agent-metrics") {
      const { data, error } = await supabase
        .from("agent_metrics")
        .select(`*, agents!agent_id(name, type, status)`);
      if (error) throw new Error(error.message);
      return json({ agent_metrics: data ?? [] });
    }

    return json({ error: "Unknown action" }, 400);
  } catch (err) {
    return json({ error: String(err) }, 500);
  }
});
