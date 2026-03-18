import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

interface ToolContext {
  ticket_id?: string | null;
  conversation_id?: string | null;
  agent_id?: string;
}

async function loadAgentTools(
  supabase: ReturnType<typeof createClient>,
  agentId: string
): Promise<Array<{ name: string; description: string; input_schema: Record<string, unknown> }>> {
  const { data: skills } = await supabase
    .from("agent_skills")
    .select("skill_name")
    .eq("agent_id", agentId);

  const skillNames = (skills ?? []).map((s: { skill_name: string }) => s.skill_name);

  if (skillNames.length === 0) return [];

  const { data: toolDefs } = await supabase
    .from("tool_definitions")
    .select("name, description, input_schema")
    .eq("is_active", true)
    .in("name", skillNames)
    .order("category")
    .order("name");

  return (toolDefs ?? []) as Array<{ name: string; description: string; input_schema: Record<string, unknown> }>;
}

async function executeTool(
  supabase: ReturnType<typeof createClient>,
  toolName: string,
  toolInput: Record<string, string>,
  context: ToolContext
): Promise<unknown> {
  switch (toolName) {
    case "lookup_customer": {
      let query = supabase.from("customers").select("id, name, email, phone, created_at");
      if (toolInput.customer_id) query = query.eq("id", toolInput.customer_id);
      else if (toolInput.email) query = query.ilike("email", `%${toolInput.email}%`);
      const { data, error } = await query.maybeSingle();
      if (error) return { error: error.message };
      if (!data) return { error: "Customer not found" };

      const { data: tickets } = await supabase
        .from("tickets")
        .select("id, subject, status, priority, created_at")
        .eq("customer_id", (data as { id: string }).id)
        .order("created_at", { ascending: false })
        .limit(5);

      return { ...(data as object), recent_tickets: tickets ?? [] };
    }

    case "get_ticket_info": {
      const { data, error } = await supabase
        .from("tickets")
        .select("id, subject, status, priority, created_at, updated_at, source, customers(id, name, email)")
        .eq("id", toolInput.ticket_id)
        .maybeSingle();
      if (error) return { error: error.message };
      return data ?? { error: "Ticket not found" };
    }

    case "update_ticket_status": {
      const { data, error } = await supabase
        .from("tickets")
        .update({ status: toolInput.status, updated_at: new Date().toISOString() })
        .eq("id", toolInput.ticket_id)
        .select("id, status, subject")
        .maybeSingle();
      if (error) return { error: error.message };
      return { success: true, ticket_id: (data as { id: string } | null)?.id, new_status: toolInput.status, subject: (data as { subject: string } | null)?.subject };
    }

    case "add_ticket_note": {
      const ticketId = toolInput.ticket_id ?? context.ticket_id;
      if (!ticketId) return { error: "ticket_id is required" };
      if (!toolInput.note) return { error: "note is required" };

      const { data: conv } = await supabase
        .from("conversations")
        .select("id")
        .eq("ticket_id", ticketId)
        .maybeSingle();
      if (!conv) return { error: "No conversation found for this ticket" };

      const { data, error } = await supabase
        .from("messages")
        .insert({
          conversation_id: (conv as { id: string }).id,
          sender_type: "agent",
          message: toolInput.note,
          message_type: "system",
          metadata: { note: true, agent_id: context.agent_id },
        })
        .select("id")
        .maybeSingle();
      if (error) return { error: error.message };
      return { success: true, note_id: (data as { id: string } | null)?.id, ticket_id: ticketId };
    }

    case "search_knowledge_base": {
      const query = (toolInput.query ?? "").trim();
      if (!query) return { error: "query is required" };
      try {
        const session = new Supabase.ai.Session("gte-small");
        const embResult = await session.run(query.slice(0, 2000), { mean_pool: true, normalize: true });
        const embedding = `[${Array.from(embResult as Float32Array).join(",")}]`;
        const { data, error: rpcErr } = await supabase.rpc("match_knowledge_chunks", {
          query_embedding: embedding,
          match_count: 5,
          match_threshold: 0.25,
        });
        if (rpcErr) throw new Error(rpcErr.message);
        const chunks = (data ?? []) as Array<{ chunk_text: string; document_title: string; similarity: number }>;
        if (chunks.length === 0) {
          return { query, results: [], total: 0, message: "No relevant knowledge base articles found." };
        }
        return {
          query,
          results: chunks.map((c) => ({ title: c.document_title, snippet: c.chunk_text, similarity: Math.round(c.similarity * 100) / 100 })),
          total: chunks.length,
        };
      } catch (err) {
        return { error: `Knowledge search failed: ${String(err)}` };
      }
    }

    case "create_ticket": {
      if (!toolInput.customer_id) return { error: "customer_id is required" };
      if (!toolInput.subject) return { error: "subject is required" };
      if (!toolInput.message) return { error: "message is required" };

      const { data: ticket, error: tErr } = await supabase
        .from("tickets")
        .insert({
          customer_id: toolInput.customer_id,
          subject: toolInput.subject,
          status: "open",
          priority: toolInput.priority ?? "normal",
          source: "agent",
        })
        .select("id, subject, status, priority")
        .single();
      if (tErr) return { error: tErr.message };

      const { data: conv, error: convErr } = await supabase
        .from("conversations")
        .insert({ ticket_id: (ticket as { id: string }).id, status: "open" })
        .select("id")
        .single();
      if (convErr) return { success: true, ticket };

      await supabase.from("messages").insert({
        conversation_id: (conv as { id: string }).id,
        sender_type: "customer",
        message: toolInput.message,
        message_type: "text",
      });

      return {
        success: true,
        ticket_id: (ticket as { id: string }).id,
        conversation_id: (conv as { id: string }).id,
        subject: (ticket as { subject: string }).subject,
        status: (ticket as { status: string }).status,
      };
    }

    case "lookup_order": {
      if (!toolInput.order_id) return { error: "order_id is required" };
      const statuses = ["processing", "shipped", "delivered", "returned", "cancelled"];
      const hash = toolInput.order_id.split("").reduce((acc, c) => acc + c.charCodeAt(0), 0);
      const status = statuses[hash % statuses.length];
      const daysAgo = (hash % 14) + 1;
      const estimatedDelivery = new Date(Date.now() + (status === "shipped" ? 3 : 0) * 86400000).toISOString().split("T")[0];
      return {
        order_id: toolInput.order_id,
        status,
        created_at: new Date(Date.now() - daysAgo * 86400000).toISOString().split("T")[0],
        estimated_delivery: status === "delivered" ? null : estimatedDelivery,
        carrier: "FedEx",
        tracking_number: `TRK${toolInput.order_id.slice(-6).toUpperCase()}`,
      };
    }

    case "escalate_to_human": {
      const ticketId = toolInput.ticket_id ?? context.ticket_id;
      if (ticketId) {
        await supabase
          .from("tickets")
          .update({ status: "open", priority: "high", updated_at: new Date().toISOString() })
          .eq("id", ticketId);
      }
      return {
        success: true,
        escalated: true,
        ticket_id: ticketId ?? null,
        reason: toolInput.reason,
        message: "The conversation has been escalated to a human operator. An agent will respond shortly.",
      };
    }

    default:
      return { error: `Unknown tool: ${toolName}. This tool may not be registered.` };
  }
}

function buildSystemPrompt(
  agent: Record<string, unknown>,
  context: Record<string, unknown>,
  toolNames: string[],
  memories?: { conversation: string; ticket: string; customer: string }
): string {
  const agentTypeDescriptions: Record<string, string> = {
    triage_agent: "You analyze and categorize incoming customer requests, routing them appropriately and gathering necessary information.",
    support_agent: "You provide general customer support, answering questions and helping resolve common issues.",
    technical_agent: "You handle technical issues, troubleshoot problems, and guide customers through technical solutions.",
    billing_agent: "You handle billing inquiries, payment issues, refund requests, and subscription management.",
    sales_agent: "You assist with pricing inquiries, plan upgrades, and help customers find the best solution for their needs.",
    qa_agent: "You handle quality assurance inquiries, testing feedback, and verification requests.",
  };

  const typeDesc = agentTypeDescriptions[agent.type as string] ?? "You are a helpful support agent.";
  let prompt = `You are ${agent.name}, an AI support agent.\n${typeDesc}\n`;

  if (agent.description) {
    prompt += `\nAgent guidelines: ${agent.description}\n`;
  }

  const customer = context.customer as Record<string, string> | null;
  if (customer) {
    prompt += `\nCustomer: ${customer.name ?? "Unknown"} (${customer.email ?? "no email"})`;
    if (customer.phone) prompt += ` | Phone: ${customer.phone}`;
    prompt += "\n";
  }

  const ticket = context.ticket as Record<string, string> | null;
  if (ticket) {
    prompt += `\nTicket: "${ticket.subject ?? "No subject"}" | Status: ${ticket.status} | Priority: ${ticket.priority}\n`;
  }

  if (toolNames.length > 0) {
    prompt += `\nAvailable tools: ${toolNames.join(", ")}`;
    prompt += "\nUse tools when needed to look up information or take actions. Always confirm actions taken.";
  } else {
    prompt += "\nNo tools are available for this agent. Respond based on your knowledge and the conversation context.";
  }

  if (memories) {
    const memParts: string[] = [];
    if (memories.customer)     memParts.push(`Customer Memory:\n${memories.customer}`);
    if (memories.ticket)       memParts.push(`Ticket Memory:\n${memories.ticket}`);
    if (memories.conversation) memParts.push(`Conversation Memory:\n${memories.conversation}`);
    if (memParts.length > 0) {
      prompt += `\n\n--- Recalled Memory ---\n${memParts.join("\n\n")}\n--- End Memory ---`;
    }
  }

  prompt += "\n\nBe professional, concise, and empathetic.";
  return prompt;
}

async function loadContext(
  supabase: ReturnType<typeof createClient>,
  ticketId: string | null,
  conversationId: string | null
): Promise<Record<string, unknown>> {
  const ctx: Record<string, unknown> = {};

  if (ticketId) {
    const { data: ticket } = await supabase
      .from("tickets")
      .select("id, subject, status, priority, source, customer_id, customers(id, name, email, phone)")
      .eq("id", ticketId)
      .maybeSingle();

    if (ticket) {
      ctx.ticket = ticket;
      ctx.customer = (ticket as Record<string, unknown>).customers ?? null;
    }
  }

  if (conversationId) {
    const { data: messages } = await supabase
      .from("messages")
      .select("sender_type, message, created_at")
      .eq("conversation_id", conversationId)
      .order("created_at", { ascending: true })
      .limit(30);

    ctx.conversation_history = messages ?? [];
  }

  return ctx;
}

async function loadMemories(
  supabase: ReturnType<typeof createClient>,
  params: { conversationId?: string | null; ticketId?: string | null; customerId?: string | null }
): Promise<{ conversation: string; ticket: string; customer: string }> {
  const results = await Promise.all([
    params.conversationId
      ? supabase
          .from("agent_memories")
          .select("content, updated_at")
          .eq("memory_type", "conversation")
          .eq("conversation_id", params.conversationId)
          .order("updated_at", { ascending: false })
          .limit(5)
      : Promise.resolve({ data: [] }),

    params.ticketId
      ? supabase
          .from("agent_memories")
          .select("content, updated_at")
          .eq("memory_type", "ticket")
          .eq("ticket_id", params.ticketId)
          .order("updated_at", { ascending: false })
          .limit(5)
      : Promise.resolve({ data: [] }),

    params.customerId
      ? supabase
          .from("agent_memories")
          .select("content, updated_at")
          .eq("memory_type", "customer")
          .eq("customer_id", params.customerId)
          .order("updated_at", { ascending: false })
          .limit(10)
      : Promise.resolve({ data: [] }),
  ]);

  const format = (rows: Array<{ content: string }> | null) =>
    (rows ?? []).map((r) => r.content).filter(Boolean).join("\n");

  return {
    conversation: format(results[0].data as Array<{ content: string }> | null),
    ticket:       format(results[1].data as Array<{ content: string }> | null),
    customer:     format(results[2].data as Array<{ content: string }> | null),
  };
}

async function storeMemory(
  supabase: ReturnType<typeof createClient>,
  params: {
    memory_type: "conversation" | "ticket" | "customer";
    agent_id?: string;
    ticket_id?: string | null;
    conversation_id?: string | null;
    customer_id?: string | null;
    content: string;
    metadata?: Record<string, unknown>;
  }
) {
  try {
    await supabase.from("agent_memories").insert({
      memory_type:     params.memory_type,
      agent_id:        params.agent_id        ?? null,
      ticket_id:       params.ticket_id       ?? null,
      conversation_id: params.conversation_id ?? null,
      customer_id:     params.customer_id     ?? null,
      content:         params.content,
      metadata:        params.metadata ?? {},
    });
  } catch { /* non-fatal */ }
}

async function storeScratchpad(
  supabase: ReturnType<typeof createClient>,
  runId: string,
  step: number,
  stepType: "thought" | "tool_call" | "tool_result" | "observation" | "memory_load",
  content: string,
  metadata?: Record<string, unknown>
) {
  try {
    await supabase.from("agent_scratchpads").insert({
      run_id:    runId,
      step,
      step_type: stepType,
      content,
      metadata:  metadata ?? {},
    });
  } catch { /* non-fatal */ }
}

async function logExecution(
  supabase: ReturnType<typeof createClient>,
  params: {
    agent_id: string;
    run_id: string | null;
    ticket_id: string | null;
    conversation_id: string | null;
    model_provider: string;
    model_name: string;
    latency_ms: number;
    input_tokens: number;
    output_tokens: number;
    tool_calls_count: number;
    iterations: number;
    status: "success" | "error" | "timeout" | "cancelled";
    error_message?: string;
  }
) {
  try {
    await supabase.from("agent_execution_logs").insert({
      agent_id:        params.agent_id,
      run_id:          params.run_id,
      ticket_id:       params.ticket_id,
      conversation_id: params.conversation_id,
      model_provider:  params.model_provider,
      model_name:      params.model_name,
      latency_ms:      params.latency_ms,
      input_tokens:    params.input_tokens,
      output_tokens:   params.output_tokens,
      tool_calls_count: params.tool_calls_count,
      iterations:      params.iterations,
      status:          params.status,
      error_message:   params.error_message ?? "",
    });
  } catch { /* non-fatal */ }
}

async function logToolCall(
  supabase: ReturnType<typeof createClient>,
  params: {
    run_id: string;
    agent_id: string;
    tool_name: string;
    arguments: Record<string, unknown>;
    result: unknown;
    latency_ms: number;
    success: boolean;
  }
) {
  try {
    await supabase.from("agent_tool_calls").insert({
      run_id:     params.run_id,
      agent_id:   params.agent_id,
      tool_name:  params.tool_name,
      arguments:  params.arguments,
      result:     params.result ?? {},
      latency_ms: params.latency_ms,
      success:    params.success,
    });
  } catch { /* non-fatal */ }
}

async function updateMetrics(
  supabase: ReturnType<typeof createClient>,
  params: {
    agent_id: string;
    latency_ms: number;
    input_tokens: number;
    output_tokens: number;
    tool_calls: number;
    success: boolean;
  }
) {
  try {
    await supabase.rpc("upsert_agent_metrics", {
      p_agent_id:      params.agent_id,
      p_latency_ms:    params.latency_ms,
      p_input_tokens:  params.input_tokens,
      p_output_tokens: params.output_tokens,
      p_tool_calls:    params.tool_calls,
      p_success:       params.success,
    });
  } catch { /* non-fatal */ }
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  let runId: string | null = null;

  try {
    const body = await req.json();
    const agentId: string = body.agent_id ?? "";
    const ticketId: string | null = body.ticket_id ?? null;
    const conversationId: string | null = body.conversation_id ?? null;
    const userMessage: string = body.message ?? "";

    if (!agentId || !userMessage.trim()) {
      return new Response(JSON.stringify({ error: "agent_id and message are required" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const { data: agent, error: agentError } = await supabase
      .from("agents")
      .select("id, name, type, description, status, default_model_provider, default_model_name, temperature, max_tokens")
      .eq("id", agentId)
      .maybeSingle();

    if (agentError || !agent) {
      return new Response(JSON.stringify({ error: "Agent not found" }), {
        status: 404,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const modelProvider = (agent.default_model_provider as string) ?? "anthropic";
    const modelName = (agent.default_model_name as string) ?? "claude-3-haiku-20240307";
    const temperature = (agent.temperature as number) ?? 0.2;
    const maxTokens = (agent.max_tokens as number) ?? 2000;

    const [agentTools, context] = await Promise.all([
      loadAgentTools(supabase, agentId),
      loadContext(supabase, ticketId, conversationId),
    ]);

    const toolNames = agentTools.map((t) => t.name);
    const customerId = (context.customer as Record<string, string> | null)?.id ?? null;

    const memories = await loadMemories(supabase, {
      conversationId,
      ticketId,
      customerId,
    });

    const { data: runData } = await supabase
      .from("agent_runs")
      .insert({
        agent_id: agentId,
        ticket_id: ticketId,
        conversation_id: conversationId,
        model_provider: modelProvider,
        model_name: modelName,
        status: "running",
        started_at: new Date().toISOString(),
      })
      .select("id")
      .single();

    runId = runData?.id ?? null;

    const systemPrompt = buildSystemPrompt(agent as Record<string, unknown>, context, toolNames, memories);

    const saveMessage = async (role: string, content: string, meta?: Record<string, unknown>) => {
      await supabase.from("agent_messages").insert({
        run_id: runId,
        role,
        content,
        metadata: meta ?? null,
      });
    };

    await saveMessage("system", systemPrompt);
    await saveMessage("user", userMessage);

    if (runId) {
      const memParts: string[] = [];
      if (memories.customer)     memParts.push(`customer(${customerId}): ${memories.customer.substring(0, 200)}`);
      if (memories.ticket)       memParts.push(`ticket(${ticketId}): ${memories.ticket.substring(0, 200)}`);
      if (memories.conversation) memParts.push(`conversation(${conversationId}): ${memories.conversation.substring(0, 200)}`);
      await storeScratchpad(supabase, runId, 0, "memory_load",
        memParts.length > 0 ? `Loaded memories:\n${memParts.join("\n")}` : "No prior memories found.",
        { has_customer: !!memories.customer, has_ticket: !!memories.ticket, has_conversation: !!memories.conversation }
      );
    }

    const llmManagerUrl = `${Deno.env.get("SUPABASE_URL")}/functions/v1/llm-manager`;
    const llmManagerKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";

    const callLLM = async (
      messages: Array<Record<string, unknown>>,
      tools: Array<Record<string, unknown>>
    ) => {
      const body: Record<string, unknown> = {
        action:      "call",
        provider:    modelProvider,
        model:       modelName,
        system:      systemPrompt,
        messages,
        temperature,
        max_tokens:  maxTokens,
        agent_id:    agentId,
        ticket_id:   ticketId ?? null,
      };
      if (tools.length > 0) {
        body.tools = tools;
        body.tool_choice = { type: "auto" };
      }
      const res = await fetch(llmManagerUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${llmManagerKey}`,
          "Apikey": llmManagerKey,
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.text();
        throw new Error(`LLM Manager error ${res.status}: ${err}`);
      }
      return res.json();
    };

    const historyMessages = (context.conversation_history as Array<Record<string, string>>) ?? [];
    const anthropicMessages: Array<Record<string, unknown>> = [];

    for (const msg of historyMessages.slice(-10)) {
      if (msg.sender_type === "customer") {
        anthropicMessages.push({ role: "user", content: msg.message ?? "" });
      } else if (msg.sender_type === "agent" || msg.sender_type === "operator") {
        anthropicMessages.push({ role: "assistant", content: msg.message ?? "" });
      }
    }
    anthropicMessages.push({ role: "user", content: userMessage });

    let totalInput = 0;
    let totalOutput = 0;
    let finalResponse = "";
    let totalToolCalls = 0;
    let iterations = 0;
    const MAX_ITERATIONS = 6;
    const execStartMs = Date.now();

    for (let i = 0; i < MAX_ITERATIONS; i++) {
      iterations = i + 1;
      const llmData = await callLLM(anthropicMessages, agentTools);
      totalInput += llmData.usage?.input_tokens ?? 0;
      totalOutput += llmData.usage?.output_tokens ?? 0;

      const stopReason: string = llmData.stop_reason ?? "end_turn";
      const contentBlocks: Array<Record<string, unknown>> = llmData.content ?? [];

      const textContent = contentBlocks
        .filter((b) => b.type === "text")
        .map((b) => b.text as string)
        .join("\n")
        .trim();

      const toolUseBlocks = contentBlocks.filter((b) => b.type === "tool_use");

      if (textContent) {
        await saveMessage("assistant", textContent, {
          stop_reason: stopReason,
          tool_calls: toolUseBlocks.length > 0 ? toolUseBlocks.map((t) => t.name) : undefined,
        });
        finalResponse = textContent;
      }

      if (stopReason !== "tool_use" || toolUseBlocks.length === 0) break;

      anthropicMessages.push({ role: "assistant", content: contentBlocks });

      const toolResults: Array<Record<string, unknown>> = [];
      for (const toolBlock of toolUseBlocks) {
        const toolName = toolBlock.name as string;
        const toolInputData = (toolBlock.input ?? {}) as Record<string, string>;
        const toolUseId = toolBlock.id as string;

        if (runId) {
          await storeScratchpad(supabase, runId, (i * 10) + 1, "tool_call",
            `Calling tool: ${toolName}`,
            { tool_name: toolName, tool_input: toolInputData, tool_use_id: toolUseId }
          );
        }

        const toolStartMs = Date.now();
        const result = await executeTool(supabase, toolName, toolInputData, {
          ticket_id: ticketId,
          conversation_id: conversationId,
          agent_id: agentId,
        });
        const toolLatency = Date.now() - toolStartMs;
        totalToolCalls++;

        if (runId) {
          await Promise.all([
            storeScratchpad(supabase, runId, (i * 10) + 2, "tool_result",
              `Tool ${toolName} returned: ${JSON.stringify(result).substring(0, 300)}`,
              { tool_name: toolName, tool_use_id: toolUseId }
            ),
            logToolCall(supabase, {
              run_id:    runId,
              agent_id:  agentId,
              tool_name: toolName,
              arguments: toolInputData as Record<string, unknown>,
              result,
              latency_ms: toolLatency,
              success:   !(result as Record<string, unknown>)?.error,
            }),
          ]);
        }

        await saveMessage("tool", JSON.stringify(result), {
          tool_name: toolName,
          tool_input: toolInputData,
          tool_result: result,
          tool_use_id: toolUseId,
        });

        toolResults.push({
          type: "tool_result",
          tool_use_id: toolUseId,
          content: JSON.stringify(result),
        });
      }

      anthropicMessages.push({ role: "user", content: toolResults });
    }

    if (finalResponse && runId) {
      await storeScratchpad(supabase, runId, 999, "observation",
        `Final response (${finalResponse.length} chars): ${finalResponse.substring(0, 400)}`,
        { total_input_tokens: totalInput, total_output_tokens: totalOutput }
      );
    }

    if (finalResponse) {
      const memoryContent = `User asked: "${userMessage.substring(0, 200)}". Agent responded: "${finalResponse.substring(0, 400)}".`;
      const memMeta = { agent_id: agentId, model: modelName, input_tokens: totalInput, output_tokens: totalOutput };

      await Promise.all([
        conversationId
          ? storeMemory(supabase, { memory_type: "conversation", agent_id: agentId, conversation_id: conversationId, ticket_id: ticketId, customer_id: customerId, content: memoryContent, metadata: memMeta })
          : Promise.resolve(),
        ticketId
          ? storeMemory(supabase, { memory_type: "ticket", agent_id: agentId, ticket_id: ticketId, conversation_id: conversationId, customer_id: customerId, content: memoryContent, metadata: memMeta })
          : Promise.resolve(),
      ]);
    }

    if (conversationId && finalResponse) {
      await supabase.from("messages").insert({
        conversation_id: conversationId,
        sender_type: "agent",
        message: finalResponse,
        message_type: "text",
        metadata: {
          agent_id: agentId,
          agent_run_id: runId,
          model_provider: modelProvider,
          model_name: modelName,
          input_tokens: totalInput,
          output_tokens: totalOutput,
        },
      });
      await supabase.from("conversations").update({ last_message_at: new Date().toISOString() }).eq("id", conversationId);
    }

    const execLatencyMs = Date.now() - execStartMs;

    if (runId) {
      await supabase.from("agent_runs").update({
        status: "completed",
        input_tokens: totalInput,
        output_tokens: totalOutput,
        finished_at: new Date().toISOString(),
      }).eq("id", runId);
    }

    await Promise.all([
      logExecution(supabase, {
        agent_id: agentId, run_id: runId, ticket_id: ticketId,
        conversation_id: conversationId, model_provider: modelProvider,
        model_name: modelName, latency_ms: execLatencyMs,
        input_tokens: totalInput, output_tokens: totalOutput,
        tool_calls_count: totalToolCalls, iterations,
        status: "success",
      }),
      updateMetrics(supabase, {
        agent_id: agentId, latency_ms: execLatencyMs,
        input_tokens: totalInput, output_tokens: totalOutput,
        tool_calls: totalToolCalls, success: true,
      }),
    ]);

    return new Response(
      JSON.stringify({
        response: finalResponse,
        agent_run_id: runId,
        agent_id: agentId,
        agent_name: agent.name,
        model_provider: modelProvider,
        model_name: modelName,
        input_tokens: totalInput,
        output_tokens: totalOutput,
        tools_available: agentTools.length,
        tools_used: toolNames,
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (err) {
    const errMsg = String(err);
    if (runId) {
      await supabase.from("agent_runs").update({
        status: "failed",
        error_message: errMsg,
        finished_at: new Date().toISOString(),
      }).eq("id", runId);
    }
    await Promise.all([
      logExecution(supabase, {
        agent_id: (supabase as unknown as { _agentId?: string })._agentId ?? "",
        run_id: runId, ticket_id: null, conversation_id: null,
        model_provider: "", model_name: "",
        latency_ms: 0, input_tokens: 0, output_tokens: 0,
        tool_calls_count: 0, iterations: 0,
        status: "error", error_message: errMsg,
      }).catch(() => {}),
    ]);
    return new Response(JSON.stringify({ error: errMsg }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
