import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

interface ToolContext {
  ticket_id?: string;
  conversation_id?: string;
  agent_id?: string;
}

async function executeTool(
  supabase: ReturnType<typeof createClient>,
  toolName: string,
  args: Record<string, string>,
  context: ToolContext
): Promise<{ result?: unknown; error?: string }> {
  switch (toolName) {
    case "search_knowledge_base": {
      const query    = (args.query ?? "").trim();
      const strategy = (args.strategy ?? "hybrid") as "semantic" | "keyword" | "hybrid";
      const topK     = parseInt(args.top_k ?? "5", 10);
      if (!query) return { error: "query is required" };
      try {
        const retrievalUrl = `${Deno.env.get("SUPABASE_URL")}/functions/v1/retrieval-service/context`;
        const res = await fetch(retrievalUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")}`,
            "Apikey": Deno.env.get("SUPABASE_ANON_KEY") ?? "",
          },
          body: JSON.stringify({
            query,
            top_k:    topK,
            strategy,
            threshold: 0.2,
            format:   "structured",
            agent_id: context.agent_id,
          }),
        });
        if (!res.ok) {
          const errBody = await res.json().catch(() => ({ error: "retrieval failed" }));
          throw new Error((errBody as { error?: string }).error ?? "retrieval failed");
        }
        const data = await res.json() as {
          query: string;
          context: string;
          sources: Array<{ document_title: string; section_title: string; score: number }>;
          total: number;
          latency_ms: number;
        };
        if (data.total === 0) {
          return { result: { query, results: [], total: 0, context: "No relevant knowledge base articles found.", message: "No relevant knowledge base articles found." } };
        }
        return {
          result: {
            query,
            context:  data.context,
            sources:  data.sources,
            total:    data.total,
            strategy,
          },
        };
      } catch (e) {
        return { error: `Knowledge search failed: ${String(e)}` };
      }
    }

    case "lookup_customer": {
      let query = supabase.from("customers").select("id, name, email, phone, created_at");
      if (args.customer_id) query = query.eq("id", args.customer_id);
      else if (args.email) query = query.ilike("email", `%${args.email}%`);
      else return { error: "Provide customer_id or email" };
      const { data, error } = await query.maybeSingle();
      if (error) return { error: error.message };
      if (!data) return { error: "Customer not found" };

      const { data: tickets, error: tErr } = await supabase
        .from("tickets")
        .select("id, subject, status, priority, created_at")
        .eq("customer_id", data.id)
        .order("created_at", { ascending: false })
        .limit(5);
      if (tErr) return { result: data };

      return { result: { ...data, recent_tickets: tickets ?? [] } };
    }

    case "get_ticket_info": {
      if (!args.ticket_id) return { error: "ticket_id is required" };
      const { data, error } = await supabase
        .from("tickets")
        .select("id, subject, status, priority, source, created_at, updated_at, customers(id, name, email, phone)")
        .eq("id", args.ticket_id)
        .maybeSingle();
      if (error) return { error: error.message };
      if (!data) return { error: "Ticket not found" };
      return { result: data };
    }

    case "update_ticket_status": {
      if (!args.ticket_id) return { error: "ticket_id is required" };
      if (!args.status) return { error: "status is required" };
      const { data, error } = await supabase
        .from("tickets")
        .update({ status: args.status, updated_at: new Date().toISOString() })
        .eq("id", args.ticket_id)
        .select("id, status, subject")
        .maybeSingle();
      if (error) return { error: error.message };
      return { result: { success: true, ticket_id: data?.id, new_status: data?.status, subject: data?.subject } };
    }

    case "add_ticket_note": {
      const ticketId = args.ticket_id ?? context.ticket_id;
      if (!ticketId) return { error: "ticket_id is required" };
      if (!args.note) return { error: "note is required" };

      const { data: conv, error: convErr } = await supabase
        .from("conversations")
        .select("id")
        .eq("ticket_id", ticketId)
        .maybeSingle();
      if (convErr) return { error: convErr.message };
      if (!conv) return { error: "No conversation found for this ticket" };

      const { data, error } = await supabase
        .from("messages")
        .insert({ conversation_id: conv.id, sender_type: "agent", message: args.note, message_type: "system", metadata: { note: true, agent_id: context.agent_id } })
        .select("id")
        .maybeSingle();
      if (error) return { error: error.message };
      return { result: { success: true, note_id: data?.id, ticket_id: ticketId } };
    }

    case "create_ticket": {
      if (!args.customer_id) return { error: "customer_id is required" };
      if (!args.subject) return { error: "subject is required" };
      if (!args.message) return { error: "message is required" };

      const { data: ticket, error: tErr } = await supabase
        .from("tickets")
        .insert({
          customer_id: args.customer_id,
          subject: args.subject,
          status: "open",
          priority: args.priority ?? "normal",
          source: "agent",
        })
        .select("id, subject, status, priority")
        .single();
      if (tErr) return { error: tErr.message };

      const { data: conv, error: convErr } = await supabase
        .from("conversations")
        .insert({ ticket_id: ticket.id, status: "open" })
        .select("id")
        .single();
      if (convErr) return { result: { success: true, ticket } };

      await supabase.from("messages").insert({
        conversation_id: conv.id,
        sender_type: "customer",
        message: args.message,
        message_type: "text",
      });

      return { result: { success: true, ticket_id: ticket.id, conversation_id: conv.id, subject: ticket.subject, status: ticket.status } };
    }

    case "lookup_order": {
      if (!args.order_id) return { error: "order_id is required" };
      const mockStatuses = ["processing", "shipped", "delivered", "returned", "cancelled"];
      const hash = args.order_id.split("").reduce((acc, c) => acc + c.charCodeAt(0), 0);
      const status = mockStatuses[hash % mockStatuses.length];
      const daysAgo = (hash % 14) + 1;
      const estimatedDelivery = new Date(Date.now() + (status === "shipped" ? 3 : 0) * 86400000).toISOString().split("T")[0];
      return {
        result: {
          order_id: args.order_id,
          status,
          created_at: new Date(Date.now() - daysAgo * 86400000).toISOString().split("T")[0],
          estimated_delivery: status === "delivered" ? null : estimatedDelivery,
          carrier: "FedEx",
          tracking_number: `TRK${args.order_id.slice(-6).toUpperCase()}`,
        },
      };
    }

    case "escalate_to_human": {
      const ticketId = args.ticket_id ?? context.ticket_id;
      if (ticketId) {
        await supabase.from("tickets").update({ status: "open", priority: "high", updated_at: new Date().toISOString() }).eq("id", ticketId);
      }
      return {
        result: {
          success: true,
          escalated: true,
          ticket_id: ticketId ?? null,
          reason: args.reason,
          message: "The conversation has been escalated to a human operator. An agent will respond shortly.",
        },
      };
    }

    default:
      return { error: `Unknown tool: ${toolName}` };
  }
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  const url = new URL(req.url);
  const path = url.pathname.replace(/\/agent-tools\/?/, "");

  try {
    if (req.method === "GET") {
      const agentId = url.searchParams.get("agent_id");
      let tools;

      if (agentId) {
        const { data: skills } = await supabase
          .from("agent_skills")
          .select("skill_name")
          .eq("agent_id", agentId);
        const skillNames = (skills ?? []).map((s: { skill_name: string }) => s.skill_name);

        const { data, error } = await supabase
          .from("tool_definitions")
          .select("*")
          .eq("is_active", true)
          .in("name", skillNames.length > 0 ? skillNames : ["__none__"])
          .order("category")
          .order("name");
        if (error) throw new Error(error.message);
        tools = data ?? [];
      } else {
        const { data, error } = await supabase
          .from("tool_definitions")
          .select("*")
          .eq("is_active", true)
          .order("category")
          .order("name");
        if (error) throw new Error(error.message);
        tools = data ?? [];
      }

      return new Response(JSON.stringify({ tools, total: tools.length }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    if (req.method === "POST") {
      const body = await req.json();

      if (path === "execute" || body.action === "execute") {
        const toolName: string = body.tool_name ?? body.tool ?? "";
        const toolArgs: Record<string, string> = body.arguments ?? body.args ?? {};
        const context: ToolContext = body.context ?? {};

        if (!toolName) {
          return new Response(JSON.stringify({ error: "tool_name is required" }), {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          });
        }

        const { data: toolDef } = await supabase
          .from("tool_definitions")
          .select("name, is_active")
          .eq("name", toolName)
          .maybeSingle();

        if (!toolDef) {
          return new Response(JSON.stringify({ error: `Tool '${toolName}' not found in registry` }), {
            status: 404,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          });
        }

        if (!toolDef.is_active) {
          return new Response(JSON.stringify({ error: `Tool '${toolName}' is currently disabled` }), {
            status: 403,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          });
        }

        const startTime = Date.now();
        const { result, error } = await executeTool(supabase, toolName, toolArgs, context);
        const duration = Date.now() - startTime;

        if (error) {
          return new Response(JSON.stringify({ error, tool_name: toolName, duration_ms: duration }), {
            status: 422,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          });
        }

        return new Response(JSON.stringify({ result, tool_name: toolName, duration_ms: duration }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }

      return new Response(JSON.stringify({ error: "Unknown POST action. Use { action: 'execute' } or POST /agent-tools/execute" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: String(err) }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
