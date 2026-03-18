import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

const ROUTING_RULES: { keywords: string[]; agentType: string }[] = [
  {
    keywords: ["refund", "payment", "billing", "invoice", "charge", "charged", "overcharged", "subscription", "money back", "cancel subscription"],
    agentType: "billing_agent",
  },
  {
    keywords: ["bug", "error", "not working", "broken", "crash", "technical", "issue", "glitch", "fix", "404", "500", "outage", "down"],
    agentType: "technical_agent",
  },
  {
    keywords: ["pricing", "plans", "buy", "upgrade", "discount", "trial", "demo", "purchase", "quote", "enterprise"],
    agentType: "sales_agent",
  },
  {
    keywords: ["quality", "test", "testing", "qa", "review", "check", "verify", "validation"],
    agentType: "qa_agent",
  },
  {
    keywords: ["help", "support", "question", "how to", "how do", "assist", "info", "information"],
    agentType: "support_agent",
  },
];

interface AgentRecord {
  id: string;
  name: string;
  type: string | null;
  status: string;
}

function ruleRouter(message: string, agents: AgentRecord[]): AgentRecord | null {
  const lower = message.toLowerCase();
  for (const rule of ROUTING_RULES) {
    if (rule.keywords.some((kw) => lower.includes(kw))) {
      const match = agents.find((a) => a.type === rule.agentType);
      if (match) return match;
    }
  }
  return null;
}

async function llmRouter(message: string, agents: AgentRecord[], apiKey: string): Promise<AgentRecord | null> {
  const agentTypes = [...new Set(agents.map((a) => a.type).filter(Boolean))];
  if (agentTypes.length === 0) return null;

  const prompt = `You are an intent classifier for a customer support system.\n\nAvailable agent types:\n${agentTypes.join("\n")}\n\nUser message: "${message}"\n\nReturn ONLY the agent type name that best matches this request. No explanation, no punctuation, just the exact agent type name from the list above.`;

  try {
    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: "claude-3-haiku-20240307",
        max_tokens: 30,
        messages: [{ role: "user", content: prompt }],
      }),
    });

    if (!response.ok) return null;

    const data = await response.json();
    const raw = data.content?.[0]?.text?.trim() ?? "";
    const agentType = raw.toLowerCase().replace(/[^a-z_]/g, "");
    return agents.find((a) => a.type === agentType) ?? null;
  } catch {
    return null;
  }
}

function fallbackRouter(agents: AgentRecord[]): AgentRecord | null {
  return agents.find((a) => a.type === "triage_agent") ?? agents[0] ?? null;
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    );

    const body = await req.json();
    const message: string = body.message ?? "";
    const conversation_id: string | null = body.conversation_id ?? null;
    const ticket_id: string | null = body.ticket_id ?? null;

    if (!message.trim()) {
      return new Response(JSON.stringify({ error: "message is required" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const { data: agentsData } = await supabase
      .from("agents")
      .select("id, name, type, status")
      .eq("status", "active");

    const activeAgents: AgentRecord[] = agentsData ?? [];

    const ruleResult = ruleRouter(message, activeAgents);
    if (ruleResult) {
      return new Response(
        JSON.stringify({
          agent_id: ruleResult.id,
          agent_type: ruleResult.type,
          agent_name: ruleResult.name,
          routing_layer: "rule",
          matched_rule: true,
          conversation_id,
          ticket_id,
        }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const anthropicKey = Deno.env.get("ANTHROPIC_API_KEY");
    if (anthropicKey && activeAgents.length > 0) {
      const llmResult = await llmRouter(message, activeAgents, anthropicKey);
      if (llmResult) {
        return new Response(
          JSON.stringify({
            agent_id: llmResult.id,
            agent_type: llmResult.type,
            agent_name: llmResult.name,
            routing_layer: "llm",
            matched_rule: false,
            conversation_id,
            ticket_id,
          }),
          { headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }
    }

    const fallbackResult = fallbackRouter(activeAgents);
    return new Response(
      JSON.stringify({
        agent_id: fallbackResult?.id ?? null,
        agent_type: fallbackResult?.type ?? "triage_agent",
        agent_name: fallbackResult?.name ?? "Triage Agent",
        routing_layer: "fallback",
        matched_rule: false,
        conversation_id,
        ticket_id,
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (err) {
    return new Response(JSON.stringify({ error: String(err) }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
