import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

interface ModelConfig {
  id: string;
  name: string;
  context_window: number;
  cost_per_input_token: number;
  cost_per_output_token: number;
  supports_tools: boolean;
  supports_vision: boolean;
}

interface ProviderConfig {
  id: string;
  name: string;
  models: ModelConfig[];
  env_key: string;
}

const PROVIDERS: Record<string, ProviderConfig> = {
  anthropic: {
    id: "anthropic",
    name: "Anthropic",
    env_key: "ANTHROPIC_API_KEY",
    models: [
      { id: "claude-3-5-sonnet-20241022", name: "Claude 3.5 Sonnet", context_window: 200000, cost_per_input_token: 0.000003, cost_per_output_token: 0.000015, supports_tools: true, supports_vision: true },
      { id: "claude-3-5-haiku-20241022",  name: "Claude 3.5 Haiku",  context_window: 200000, cost_per_input_token: 0.0000008, cost_per_output_token: 0.000004, supports_tools: true, supports_vision: true },
      { id: "claude-3-opus-20240229",     name: "Claude 3 Opus",     context_window: 200000, cost_per_input_token: 0.000015, cost_per_output_token: 0.000075, supports_tools: true, supports_vision: true },
      { id: "claude-3-haiku-20240307",    name: "Claude 3 Haiku",    context_window: 200000, cost_per_input_token: 0.00000025, cost_per_output_token: 0.00000125, supports_tools: true, supports_vision: false },
    ],
  },
  openai: {
    id: "openai",
    name: "OpenAI",
    env_key: "OPENAI_API_KEY",
    models: [
      { id: "gpt-4o",           name: "GPT-4o",           context_window: 128000, cost_per_input_token: 0.0000025,  cost_per_output_token: 0.000010,  supports_tools: true, supports_vision: true },
      { id: "gpt-4o-mini",      name: "GPT-4o Mini",      context_window: 128000, cost_per_input_token: 0.00000015, cost_per_output_token: 0.0000006, supports_tools: true, supports_vision: true },
      { id: "gpt-4-turbo",      name: "GPT-4 Turbo",      context_window: 128000, cost_per_input_token: 0.000010,   cost_per_output_token: 0.000030,  supports_tools: true, supports_vision: true },
      { id: "gpt-3.5-turbo",    name: "GPT-3.5 Turbo",    context_window: 16385,  cost_per_input_token: 0.0000005,  cost_per_output_token: 0.0000015, supports_tools: true, supports_vision: false },
    ],
  },
  google: {
    id: "google",
    name: "Google",
    env_key: "GOOGLE_API_KEY",
    models: [
      { id: "gemini-1.5-pro",   name: "Gemini 1.5 Pro",   context_window: 1000000, cost_per_input_token: 0.00000125, cost_per_output_token: 0.000005,  supports_tools: true, supports_vision: true },
      { id: "gemini-1.5-flash", name: "Gemini 1.5 Flash",  context_window: 1000000, cost_per_input_token: 0.000000075, cost_per_output_token: 0.0000003, supports_tools: true, supports_vision: true },
      { id: "gemini-2.0-flash", name: "Gemini 2.0 Flash",  context_window: 1000000, cost_per_input_token: 0.0000001, cost_per_output_token: 0.0000004, supports_tools: false, supports_vision: true },
    ],
  },
};

const DEFAULT_FALLBACK_CHAINS: Record<string, string[]> = {
  anthropic: ["openai", "google"],
  openai:    ["anthropic", "google"],
  google:    ["anthropic", "openai"],
};

function getModelConfig(provider: string, modelId: string): ModelConfig | undefined {
  return PROVIDERS[provider]?.models.find((m) => m.id === modelId);
}

function getDefaultModel(provider: string): string {
  const models = PROVIDERS[provider]?.models;
  if (!models?.length) return "";
  return models[0].id;
}

type AnthropicContentBlock =
  | { type: "text"; text: string }
  | { type: "tool_use"; id: string; name: string; input: Record<string, unknown> }
  | { type: "tool_result"; tool_use_id: string; content: string };

type AnthropicMessage = {
  role: "user" | "assistant";
  content: string | AnthropicContentBlock[];
};

interface NormalizedRequest {
  provider: string;
  model: string;
  messages: AnthropicMessage[];
  system?: string;
  temperature?: number;
  max_tokens?: number;
  tools?: Array<{ name: string; description: string; input_schema: Record<string, unknown> }>;
  tool_choice?: unknown;
  agent_id?: string;
  ticket_id?: string;
}

interface NormalizedResponse {
  content: AnthropicContentBlock[];
  usage: { input_tokens: number; output_tokens: number };
  model: string;
  stop_reason: string;
  provider: string;
}

function msgToText(content: string | AnthropicContentBlock[]): string {
  if (typeof content === "string") return content;
  return content
    .filter((b) => b.type === "text")
    .map((b) => (b as { type: "text"; text: string }).text)
    .join("\n");
}

async function callAnthropic(req: NormalizedRequest, apiKey: string): Promise<NormalizedResponse> {
  const body: Record<string, unknown> = {
    model:       req.model,
    messages:    req.messages,
    temperature: req.temperature ?? 0.7,
    max_tokens:  req.max_tokens ?? 1024,
  };
  if (req.system)      body.system = req.system;
  if (req.tools)       body.tools = req.tools;
  if (req.tool_choice) body.tool_choice = req.tool_choice;

  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Anthropic API error ${res.status}: ${err}`);
  }

  const data = await res.json() as {
    content: AnthropicContentBlock[];
    usage: { input_tokens: number; output_tokens: number };
    model: string;
    stop_reason: string;
  };

  return {
    content:     data.content,
    usage:       data.usage,
    model:       data.model,
    stop_reason: data.stop_reason,
    provider:    "anthropic",
  };
}

function anthropicMessagesToOpenAI(messages: AnthropicMessage[]): Array<Record<string, unknown>> {
  const result: Array<Record<string, unknown>> = [];
  for (const msg of messages) {
    if (typeof msg.content === "string") {
      result.push({ role: msg.role, content: msg.content });
      continue;
    }

    const textBlocks = msg.content.filter((b) => b.type === "text");
    const toolUse    = msg.content.filter((b) => b.type === "tool_use") as Array<{ type: "tool_use"; id: string; name: string; input: Record<string, unknown> }>;
    const toolResult = msg.content.filter((b) => b.type === "tool_result") as Array<{ type: "tool_result"; tool_use_id: string; content: string }>;

    if (toolResult.length > 0) {
      for (const tr of toolResult) {
        result.push({ role: "tool", tool_call_id: tr.tool_use_id, content: typeof tr.content === "string" ? tr.content : JSON.stringify(tr.content) });
      }
      continue;
    }

    if (toolUse.length > 0) {
      result.push({
        role: "assistant",
        content: textBlocks.length > 0 ? textBlocks.map((b) => (b as { type: "text"; text: string }).text).join("\n") : null,
        tool_calls: toolUse.map((tu) => ({
          id:       tu.id,
          type:     "function",
          function: { name: tu.name, arguments: JSON.stringify(tu.input) },
        })),
      });
      continue;
    }

    const textContent = textBlocks.map((b) => (b as { type: "text"; text: string }).text).join("\n");
    result.push({ role: msg.role, content: textContent });
  }
  return result;
}

function anthropicToolsToOpenAI(tools: Array<{ name: string; description: string; input_schema: Record<string, unknown> }>): Array<Record<string, unknown>> {
  return tools.map((t) => ({
    type: "function",
    function: { name: t.name, description: t.description, parameters: t.input_schema },
  }));
}

function openAIResponseToAnthropic(data: Record<string, unknown>): NormalizedResponse {
  const choice = (data.choices as Array<Record<string, unknown>>)?.[0];
  const message = choice?.message as Record<string, unknown> | undefined;
  const usage = data.usage as { prompt_tokens: number; completion_tokens: number } | undefined;

  const content: AnthropicContentBlock[] = [];

  if (message?.content) {
    content.push({ type: "text", text: message.content as string });
  }

  if (message?.tool_calls) {
    for (const tc of message.tool_calls as Array<Record<string, unknown>>) {
      const fn = tc.function as Record<string, unknown>;
      let input: Record<string, unknown> = {};
      try { input = JSON.parse(fn.arguments as string); } catch { /* ignore */ }
      content.push({ type: "tool_use", id: tc.id as string, name: fn.name as string, input });
    }
  }

  const stopReason = (choice?.finish_reason as string) === "tool_calls" ? "tool_use" : "end_turn";

  return {
    content,
    usage: { input_tokens: usage?.prompt_tokens ?? 0, output_tokens: usage?.completion_tokens ?? 0 },
    model: data.model as string,
    stop_reason: stopReason,
    provider: "openai",
  };
}

async function callOpenAI(req: NormalizedRequest, apiKey: string): Promise<NormalizedResponse> {
  const messages: Array<Record<string, unknown>> = [];
  if (req.system) messages.push({ role: "system", content: req.system });
  messages.push(...anthropicMessagesToOpenAI(req.messages));

  const body: Record<string, unknown> = {
    model:       req.model,
    messages,
    temperature: req.temperature ?? 0.7,
    max_tokens:  req.max_tokens ?? 1024,
  };

  if (req.tools && req.tools.length > 0) {
    body.tools = anthropicToolsToOpenAI(req.tools);
    body.tool_choice = "auto";
  }

  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`,
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`OpenAI API error ${res.status}: ${err}`);
  }

  const data = await res.json() as Record<string, unknown>;
  return openAIResponseToAnthropic(data);
}

function anthropicMessagesToGemini(messages: AnthropicMessage[], system?: string): Array<Record<string, unknown>> {
  const result: Array<Record<string, unknown>> = [];
  if (system) {
    result.push({ role: "user", parts: [{ text: `System: ${system}` }] });
    result.push({ role: "model", parts: [{ text: "Understood." }] });
  }
  for (const msg of messages) {
    result.push({
      role: msg.role === "assistant" ? "model" : "user",
      parts: [{ text: msgToText(msg.content) }],
    });
  }
  return result;
}

async function callGoogle(req: NormalizedRequest, apiKey: string): Promise<NormalizedResponse> {
  const contents = anthropicMessagesToGemini(req.messages, req.system);
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${req.model}:generateContent?key=${apiKey}`;

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents,
      generationConfig: {
        temperature:     req.temperature ?? 0.7,
        maxOutputTokens: req.max_tokens ?? 1024,
      },
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Google API error ${res.status}: ${err}`);
  }

  const data = await res.json() as {
    candidates: Array<{ content: { parts: Array<{ text: string }> }; finishReason: string }>;
    usageMetadata: { promptTokenCount: number; candidatesTokenCount: number };
  };

  const text = data.candidates?.[0]?.content?.parts?.map((p) => p.text).join("") ?? "";
  const usage = data.usageMetadata;

  return {
    content: [{ type: "text", text }],
    usage: { input_tokens: usage?.promptTokenCount ?? 0, output_tokens: usage?.candidatesTokenCount ?? 0 },
    model: req.model,
    stop_reason: "end_turn",
    provider: "google",
  };
}

async function executeProvider(req: NormalizedRequest, overrideProvider?: string): Promise<NormalizedResponse> {
  const providerKey = overrideProvider ?? req.provider;
  const providerCfg = PROVIDERS[providerKey];
  if (!providerCfg) throw new Error(`Unknown provider: ${providerKey}`);

  const apiKey = Deno.env.get(providerCfg.env_key) ?? "";
  if (!apiKey) throw new Error(`API key not configured for provider: ${providerKey}`);

  const model = req.model || getDefaultModel(providerKey);

  const callReq: NormalizedRequest = { ...req, provider: providerKey, model };

  switch (providerKey) {
    case "anthropic": return callAnthropic(callReq, apiKey);
    case "openai":    return callOpenAI(callReq, apiKey);
    case "google":    return callGoogle(callReq, apiKey);
    default:          throw new Error(`Unsupported provider: ${providerKey}`);
  }
}

async function trackCost(
  supabase: ReturnType<typeof createClient>,
  provider: string,
  model: string,
  usage: { input_tokens: number; output_tokens: number },
  latencyMs: number,
  status: "success" | "error" | "fallback",
  agentId?: string,
  ticketId?: string,
  fallbackFrom?: string,
  errorMessage?: string
) {
  const cfg = getModelConfig(provider, model);
  const costInput  = (usage.input_tokens  ?? 0) * (cfg?.cost_per_input_token  ?? 0);
  const costOutput = (usage.output_tokens ?? 0) * (cfg?.cost_per_output_token ?? 0);

  try {
    await supabase.from("llm_usage_logs").insert({
      provider,
      model_name:     model,
      input_tokens:   usage.input_tokens,
      output_tokens:  usage.output_tokens,
      cost_input:     costInput,
      cost_output:    costOutput,
      latency_ms:     latencyMs,
      status,
      agent_id:       agentId ?? null,
      ticket_id:      ticketId ?? null,
      fallback_from:  fallbackFrom ?? null,
      error_message:  errorMessage ?? null,
    });
  } catch {
    // Non-fatal: don't break the response flow
  }
}

async function callModel(
  supabase: ReturnType<typeof createClient>,
  req: NormalizedRequest
): Promise<NormalizedResponse & { fallback?: boolean; original_provider?: string }> {
  const startTime = Date.now();
  let lastError = "";

  try {
    const response = await executeProvider(req);
    const latency = Date.now() - startTime;
    await trackCost(supabase, req.provider, response.model, response.usage, latency, "success", req.agent_id, req.ticket_id);
    return response;
  } catch (primaryErr) {
    lastError = String(primaryErr);
  }

  const fallbackChain = DEFAULT_FALLBACK_CHAINS[req.provider] ?? [];
  for (const fallbackProvider of fallbackChain) {
    const providerCfg = PROVIDERS[fallbackProvider];
    if (!providerCfg) continue;

    const apiKey = Deno.env.get(providerCfg.env_key) ?? "";
    if (!apiKey) continue;

    const fallbackModel = getDefaultModel(fallbackProvider);

    try {
      const fallbackReq: NormalizedRequest = {
        ...req,
        provider: fallbackProvider,
        model:    fallbackModel,
        tools:    fallbackProvider === "google" ? undefined : req.tools,
      };
      const response = await executeProvider(fallbackReq);
      const latency = Date.now() - startTime;
      await trackCost(supabase, fallbackProvider, response.model, response.usage, latency, "fallback", req.agent_id, req.ticket_id, `${req.provider}/${req.model}`);
      return { ...response, fallback: true, original_provider: req.provider };
    } catch {
      // Try next fallback
    }
  }

  const latency = Date.now() - startTime;
  await trackCost(supabase, req.provider, req.model, { input_tokens: 0, output_tokens: 0 }, latency, "error", req.agent_id, req.ticket_id, undefined, lastError);
  throw new Error(`All providers failed. Last error: ${lastError}`);
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  const json = (data: unknown, status = 200) =>
    new Response(JSON.stringify(data), { status, headers: { ...corsHeaders, "Content-Type": "application/json" } });

  try {
    const url = new URL(req.url);

    if (req.method === "GET") {
      const action = url.searchParams.get("action") ?? "providers";

      if (action === "providers") {
        const result = Object.values(PROVIDERS).map((p) => ({
          ...p,
          available: !!(Deno.env.get(p.env_key)),
        }));
        return json({ providers: result });
      }

      if (action === "models") {
        const models: Array<ModelConfig & { provider: string }> = [];
        for (const [pId, p] of Object.entries(PROVIDERS)) {
          for (const m of p.models) {
            models.push({ ...m, provider: pId });
          }
        }
        return json({ models });
      }

      if (action === "usage") {
        const range = url.searchParams.get("range") ?? "30d";
        const days  = range === "7d" ? 7 : range === "1d" ? 1 : 30;
        const since = new Date(Date.now() - days * 86400000).toISOString();

        const { data: rows, error } = await supabase
          .from("llm_usage_logs")
          .select("provider, model_name, input_tokens, output_tokens, total_cost, status, created_at")
          .gte("created_at", since)
          .order("created_at", { ascending: false });

        if (error) throw new Error(error.message);

        const summary = (rows ?? []).reduce(
          (acc: Record<string, { calls: number; input_tokens: number; output_tokens: number; total_cost: number; errors: number }>, row) => {
            const key = row.provider;
            if (!acc[key]) acc[key] = { calls: 0, input_tokens: 0, output_tokens: 0, total_cost: 0, errors: 0 };
            acc[key].calls++;
            acc[key].input_tokens  += row.input_tokens  ?? 0;
            acc[key].output_tokens += row.output_tokens ?? 0;
            acc[key].total_cost    += Number(row.total_cost) ?? 0;
            if (row.status === "error") acc[key].errors++;
            return acc;
          },
          {}
        );

        const totalCost   = (rows ?? []).reduce((s, r) => s + (Number(r.total_cost) ?? 0), 0);
        const totalCalls  = (rows ?? []).length;
        const totalTokens = (rows ?? []).reduce((s, r) => s + (r.input_tokens ?? 0) + (r.output_tokens ?? 0), 0);

        return json({ summary, totalCost, totalCalls, totalTokens, range });
      }

      if (action === "logs") {
        const limit  = parseInt(url.searchParams.get("limit") ?? "50");
        const offset = parseInt(url.searchParams.get("offset") ?? "0");
        const { data, error, count } = await supabase
          .from("llm_usage_logs")
          .select("*", { count: "exact" })
          .order("created_at", { ascending: false })
          .range(offset, offset + limit - 1);

        if (error) throw new Error(error.message);
        return json({ logs: data ?? [], total: count ?? 0 });
      }

      return json({ error: "Unknown action" }, 400);
    }

    if (req.method === "POST") {
      const body = await req.json() as Record<string, unknown>;
      const action = (body.action as string) ?? "";

      if (action === "call") {
        const request: NormalizedRequest = {
          provider:    (body.provider  as string) ?? "anthropic",
          model:       (body.model     as string) ?? "claude-3-5-sonnet-20241022",
          messages:    (body.messages  as AnthropicMessage[]) ?? [],
          system:      body.system     as string | undefined,
          temperature: body.temperature as number | undefined,
          max_tokens:  body.max_tokens  as number | undefined,
          tools:       body.tools       as NormalizedRequest["tools"] | undefined,
          tool_choice: body.tool_choice,
          agent_id:    body.agent_id    as string | undefined,
          ticket_id:   body.ticket_id   as string | undefined,
        };

        const response = await callModel(supabase, request);
        return json(response);
      }

      if (action === "test") {
        const provider    = (body.provider as string) ?? "anthropic";
        const model       = (body.model    as string) ?? getDefaultModel(provider);
        const userMessage = (body.message  as string) ?? "Hello! Please respond with a brief greeting.";

        const request: NormalizedRequest = {
          provider,
          model,
          messages:    [{ role: "user", content: userMessage }],
          temperature: 0.7,
          max_tokens:  256,
          agent_id:    body.agent_id    as string | undefined,
          ticket_id:   body.ticket_id   as string | undefined,
        };

        const response = await callModel(supabase, request);
        const textContent = response.content.find((b) => b.type === "text") as { type: "text"; text: string } | undefined;
        return json({
          response: textContent?.text ?? "",
          provider: response.provider,
          model:    response.model,
          usage:    response.usage,
          fallback: (response as { fallback?: boolean }).fallback ?? false,
        });
      }

      return json({ error: "Unknown action" }, 400);
    }

    return json({ error: "Method not allowed" }, 405);
  } catch (err) {
    return json({ error: String(err) }, 500);
  }
});
