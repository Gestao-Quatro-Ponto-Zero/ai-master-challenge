import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

// ── Provider API key env var names ─────────────────────────────────────────────

const PROVIDER_ENV_KEYS: Record<string, string> = {
  openai:    "OPENAI_API_KEY",
  anthropic: "ANTHROPIC_API_KEY",
  google:    "GOOGLE_API_KEY",
  mistral:   "MISTRAL_API_KEY",
};

const FALLBACK_CHAINS: Record<string, string[]> = {
  openai:    ["anthropic", "google"],
  anthropic: ["openai",    "google"],
  google:    ["anthropic", "openai"],
  mistral:   ["openai",    "anthropic"],
};

// ── Normalised internal types ──────────────────────────────────────────────────

interface ContentBlock {
  type: "text" | "tool_use" | "tool_result";
  text?: string;
  id?: string;
  name?: string;
  input?: Record<string, unknown>;
  tool_use_id?: string;
  content?: string;
}

interface Message {
  role: "user" | "assistant";
  content: string | ContentBlock[];
}

interface ModelRow {
  id:                       string;
  name:                     string;
  provider:                 string;
  model_identifier:         string;
  max_tokens:               number | null;
  input_cost_per_1k_tokens:  number | null;
  output_cost_per_1k_tokens: number | null;
}

interface RouteRequest {
  agent_id?:        string;
  organization_id?: string;
  model_id?:        string;
  provider?:        string;
  task_type?:       string;
  prompt?:          string;
  messages?:        Message[];
  system?:          string;
  max_tokens?:      number;
  temperature?:     number;
}

interface NormalisedLLMRequest {
  provider:     string;
  model:        string;
  messages:     Message[];
  system?:      string;
  temperature?: number;
  max_tokens?:  number;
}

interface ProviderResponse {
  content:     ContentBlock[];
  usage:       { input_tokens: number; output_tokens: number };
  model:       string;
  stop_reason: string;
  provider:    string;
}

// ── Text helpers ───────────────────────────────────────────────────────────────

function textOf(content: string | ContentBlock[]): string {
  if (typeof content === "string") return content;
  return content
    .filter((b) => b.type === "text" && b.text)
    .map((b) => b.text!)
    .join("\n");
}

// ── Provider call: Anthropic ───────────────────────────────────────────────────

async function callAnthropic(req: NormalisedLLMRequest, apiKey: string): Promise<ProviderResponse> {
  const body: Record<string, unknown> = {
    model:       req.model,
    messages:    req.messages,
    temperature: req.temperature ?? 0.7,
    max_tokens:  req.max_tokens  ?? 1024,
  };
  if (req.system) body.system = req.system;

  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type":      "application/json",
      "x-api-key":         apiKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Anthropic ${res.status}: ${txt}`);
  }

  const data = await res.json() as {
    content:     ContentBlock[];
    usage:       { input_tokens: number; output_tokens: number };
    model:       string;
    stop_reason: string;
  };

  return { ...data, provider: "anthropic" };
}

// ── Provider call: OpenAI ──────────────────────────────────────────────────────

function toOpenAIMessages(messages: Message[], system?: string): Array<Record<string, unknown>> {
  const out: Array<Record<string, unknown>> = [];
  if (system) out.push({ role: "system", content: system });
  for (const m of messages) {
    if (typeof m.content === "string") {
      out.push({ role: m.role, content: m.content });
      continue;
    }
    const text = textOf(m.content);
    out.push({ role: m.role, content: text });
  }
  return out;
}

async function callOpenAI(req: NormalisedLLMRequest, apiKey: string): Promise<ProviderResponse> {
  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type":  "application/json",
      "Authorization": `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model:       req.model,
      messages:    toOpenAIMessages(req.messages, req.system),
      temperature: req.temperature ?? 0.7,
      max_tokens:  req.max_tokens  ?? 1024,
    }),
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`OpenAI ${res.status}: ${txt}`);
  }

  const data = await res.json() as {
    choices: Array<{ message: { content: string }; finish_reason: string }>;
    usage: { prompt_tokens: number; completion_tokens: number };
    model: string;
  };

  return {
    content:     [{ type: "text", text: data.choices[0]?.message?.content ?? "" }],
    usage:       { input_tokens: data.usage?.prompt_tokens ?? 0, output_tokens: data.usage?.completion_tokens ?? 0 },
    model:       data.model,
    stop_reason: data.choices[0]?.finish_reason === "stop" ? "end_turn" : data.choices[0]?.finish_reason ?? "end_turn",
    provider:    "openai",
  };
}

// ── Provider call: Google ──────────────────────────────────────────────────────

async function callGoogle(req: NormalisedLLMRequest, apiKey: string): Promise<ProviderResponse> {
  const contents: Array<Record<string, unknown>> = [];
  if (req.system) {
    contents.push({ role: "user",  parts: [{ text: `System: ${req.system}` }] });
    contents.push({ role: "model", parts: [{ text: "Understood." }] });
  }
  for (const m of req.messages) {
    contents.push({ role: m.role === "assistant" ? "model" : "user", parts: [{ text: textOf(m.content) }] });
  }

  const url = `https://generativelanguage.googleapis.com/v1beta/models/${req.model}:generateContent?key=${apiKey}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents,
      generationConfig: { temperature: req.temperature ?? 0.7, maxOutputTokens: req.max_tokens ?? 1024 },
    }),
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Google ${res.status}: ${txt}`);
  }

  const data = await res.json() as {
    candidates:    Array<{ content: { parts: Array<{ text: string }> }; finishReason: string }>;
    usageMetadata: { promptTokenCount: number; candidatesTokenCount: number };
  };

  const text = data.candidates?.[0]?.content?.parts?.map((p) => p.text).join("") ?? "";

  return {
    content:     [{ type: "text", text }],
    usage:       { input_tokens: data.usageMetadata?.promptTokenCount ?? 0, output_tokens: data.usageMetadata?.candidatesTokenCount ?? 0 },
    model:       req.model,
    stop_reason: "end_turn",
    provider:    "google",
  };
}

// ── Provider dispatch ──────────────────────────────────────────────────────────

async function callProvider(req: NormalisedLLMRequest): Promise<ProviderResponse> {
  const envKey = PROVIDER_ENV_KEYS[req.provider];
  if (!envKey) throw new Error(`Unknown provider: ${req.provider}`);
  const apiKey = Deno.env.get(envKey) ?? "";
  if (!apiKey) throw new Error(`API key not configured for provider: ${req.provider}`);

  switch (req.provider) {
    case "anthropic": return callAnthropic(req, apiKey);
    case "openai":    return callOpenAI(req, apiKey);
    case "google":    return callGoogle(req, apiKey);
    default:          throw new Error(`Unsupported provider: ${req.provider}`);
  }
}

// ── Cost calc ─────────────────────────────────────────────────────────────────

function calcCost(
  inputTokens:  number,
  outputTokens: number,
  inCostPer1k:  number,
  outCostPer1k: number
) {
  const inputCost  = (inputTokens  / 1000) * inCostPer1k;
  const outputCost = (outputTokens / 1000) * outCostPer1k;
  return { inputCost, outputCost, totalCost: inputCost + outputCost };
}

// ── Model selector ─────────────────────────────────────────────────────────────
// Priority order:
//   1. explicit model_id requested by caller
//   2. active llm_policy for task_type (ordered by priority asc)
//   3. lowest-cost active model (global fallback)

async function selectModel(
  supabase: ReturnType<typeof createClient>,
  preferredModelId?: string,
  preferredProvider?: string,
  taskType?: string
): Promise<ModelRow | null> {
  // 1. Explicit model override
  if (preferredModelId) {
    const { data } = await supabase
      .from("llm_models")
      .select("id,name,provider,model_identifier,max_tokens,input_cost_per_1k_tokens,output_cost_per_1k_tokens")
      .eq("id", preferredModelId)
      .eq("is_active", true)
      .maybeSingle();
    if (data) return data as ModelRow;
  }

  // 2. Policy-driven selection
  if (taskType) {
    const { data: policies } = await supabase
      .from("llm_policies")
      .select(`
        priority,
        model:llm_models!model_id(
          id, name, provider, model_identifier,
          max_tokens, input_cost_per_1k_tokens, output_cost_per_1k_tokens,
          is_active
        )
      `)
      .eq("task_type", taskType)
      .eq("is_active", true)
      .order("priority", { ascending: true });

    if (policies) {
      for (const p of policies) {
        const m = p.model as (ModelRow & { is_active: boolean }) | null;
        if (m?.is_active) return m as ModelRow;
      }
    }
  }

  // 3. Global cost-based fallback
  let query = supabase
    .from("llm_models")
    .select("id,name,provider,model_identifier,max_tokens,input_cost_per_1k_tokens,output_cost_per_1k_tokens")
    .eq("is_active", true)
    .order("input_cost_per_1k_tokens", { ascending: true })
    .limit(1);

  if (preferredProvider) query = query.eq("provider", preferredProvider);

  const { data } = await query;
  return data?.[0] as ModelRow ?? null;
}

// ── Main router execute ────────────────────────────────────────────────────────

async function executeRoute(
  supabase: ReturnType<typeof createClient>,
  body: RouteRequest
): Promise<Record<string, unknown>> {
  // Build message list
  const messages: Message[] = body.messages
    ? body.messages
    : [{ role: "user", content: body.prompt ?? "" }];

  // Select model (policy-aware)
  const modelRow = await selectModel(supabase, body.model_id, body.provider, body.task_type);
  if (!modelRow) throw new Error("No active LLM model available");

  // ── Budget check ─────────────────────────────────────────────────────────
  const orgId = body.organization_id ?? null;
  const { data: budgetExceeded } = await supabase.rpc("check_budget_exceeded", { p_org_id: orgId });
  if (budgetExceeded === true) {
    throw new Error("Budget limit reached: LLM requests are blocked until the budget is reset or increased.");
  }

  // Create llm_requests record
  const { data: reqRow, error: reqErr } = await supabase
    .from("llm_requests")
    .insert({
      agent_id:         body.agent_id ?? null,
      model_id:         modelRow.id,
      provider:         modelRow.provider,
      model_identifier: modelRow.model_identifier,
      status:           "pending",
      metadata:         { task_type: body.task_type ?? "chat" },
    })
    .select("id")
    .single();

  if (reqErr) throw new Error(`Failed to create request log: ${reqErr.message}`);
  const requestId = reqRow.id as string;

  const normReq: NormalisedLLMRequest = {
    provider:    modelRow.provider,
    model:       modelRow.model_identifier,
    messages,
    system:      body.system,
    temperature: body.temperature,
    max_tokens:  body.max_tokens,
  };

  const startMs   = Date.now();
  let response!:   ProviderResponse;
  let usedProvider = modelRow.provider;
  let usedModel    = modelRow.model_identifier;
  let wasFallback  = false;

  try {
    response = await callProvider(normReq);
    usedProvider = response.provider;
    usedModel    = response.model;
  } catch (primaryErr) {
    const chain = FALLBACK_CHAINS[modelRow.provider] ?? [];
    let succeeded = false;

    for (const fallbackProvider of chain) {
      const envKey = PROVIDER_ENV_KEYS[fallbackProvider];
      if (!envKey || !Deno.env.get(envKey)) continue;

      const { data: fbModel } = await supabase
        .from("llm_models")
        .select("model_identifier")
        .eq("provider", fallbackProvider)
        .eq("is_active", true)
        .order("input_cost_per_1k_tokens", { ascending: true })
        .limit(1)
        .maybeSingle();

      if (!fbModel) continue;

      try {
        response = await callProvider({ ...normReq, provider: fallbackProvider, model: fbModel.model_identifier });
        usedProvider = response.provider;
        usedModel    = response.model;
        wasFallback  = true;
        succeeded    = true;
        break;
      } catch {
        // try next
      }
    }

    if (!succeeded) {
      const latency = Date.now() - startMs;
      await supabase.from("llm_requests").update({
        status:        "error",
        error_message: String(primaryErr),
        latency_ms:    latency,
        updated_at:    new Date().toISOString(),
      }).eq("id", requestId);
      throw primaryErr;
    }
  }

  const latency     = Date.now() - startMs;
  const inputTok    = response.usage.input_tokens;
  const outputTok   = response.usage.output_tokens;
  const totalTok    = inputTok + outputTok;

  // Resolve model row for the actually-used provider/model (fallback may differ)
  let resolvedModel = modelRow;
  if (wasFallback) {
    const { data: fbRow } = await supabase
      .from("llm_models")
      .select("id,name,provider,model_identifier,max_tokens,input_cost_per_1k_tokens,output_cost_per_1k_tokens")
      .eq("provider", usedProvider)
      .eq("model_identifier", usedModel)
      .maybeSingle();
    if (fbRow) resolvedModel = fbRow as ModelRow;
  }

  const inCostPer1k  = resolvedModel.input_cost_per_1k_tokens  ?? 0;
  const outCostPer1k = resolvedModel.output_cost_per_1k_tokens ?? 0;
  const { inputCost, outputCost, totalCost } = calcCost(inputTok, outputTok, inCostPer1k, outCostPer1k);

  // Update llm_requests → success
  await supabase.from("llm_requests").update({
    status:             "success",
    model_id:           resolvedModel.id,
    provider:           usedProvider,
    model_identifier:   usedModel,
    prompt_tokens:      inputTok,
    completion_tokens:  outputTok,
    total_tokens:       totalTok,
    latency_ms:         latency,
    updated_at:         new Date().toISOString(),
  }).eq("id", requestId);

  // Record llm_token_usage
  await supabase.from("llm_token_usage").insert({
    request_id:       requestId,
    model_id:         resolvedModel.id,
    agent_id:         body.agent_id ?? null,
    provider:         usedProvider,
    model_identifier: usedModel,
    input_tokens:     inputTok,
    output_tokens:    outputTok,
    total_tokens:     totalTok,
  });

  // Record llm_costs
  await supabase.from("llm_costs").insert({
    request_id:         requestId,
    model_id:           resolvedModel.id,
    agent_id:           body.agent_id ?? null,
    provider:           usedProvider,
    model_identifier:   usedModel,
    input_tokens:       inputTok,
    output_tokens:      outputTok,
    total_tokens:       totalTok,
    input_cost_per_1k:  inCostPer1k,
    output_cost_per_1k: outCostPer1k,
    input_cost:         inputCost,
    output_cost:        outputCost,
    total_cost:         totalCost,
    currency:           "USD",
  });

  // ── Budget usage update (fire-and-forget, non-blocking) ───────────────────
  EdgeRuntime.waitUntil(
    supabase.rpc("increment_budget_usage", {
      p_org_id:  orgId,
      p_cost:    totalCost,
      p_tokens:  totalTok,
    })
  );

  const text = response.content.find((b) => b.type === "text")?.text ?? "";

  return {
    request_id:        requestId,
    response:          text,
    content:           response.content,
    model:             usedModel,
    model_id:          resolvedModel.id,
    provider:          usedProvider,
    stop_reason:       response.stop_reason,
    usage: {
      input_tokens:  inputTok,
      output_tokens: outputTok,
      total_tokens:  totalTok,
    },
    cost: {
      input_cost:  inputCost,
      output_cost: outputCost,
      total_cost:  totalCost,
      currency:    "USD",
    },
    latency_ms: latency,
    fallback:   wasFallback,
  };
}

// ── Deno.serve ────────────────────────────────────────────────────────────────

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  const json = (data: unknown, status = 200) =>
    new Response(JSON.stringify(data), {
      status,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });

  try {
    const url = new URL(req.url);

    // ── GET endpoints ────────────────────────────────────────────────────────

    if (req.method === "GET") {
      const action = url.searchParams.get("action") ?? "status";

      if (action === "status") {
        const available: Record<string, boolean> = {};
        for (const [p, envKey] of Object.entries(PROVIDER_ENV_KEYS)) {
          available[p] = !!(Deno.env.get(envKey));
        }
        return json({ status: "ok", providers: available });
      }

      if (action === "models") {
        const { data, error } = await supabase
          .from("llm_models")
          .select("id,name,provider,model_identifier,max_tokens,input_cost_per_1k_tokens,output_cost_per_1k_tokens,is_active")
          .eq("is_active", true)
          .order("input_cost_per_1k_tokens", { ascending: true });
        if (error) throw new Error(error.message);
        return json({ models: data ?? [] });
      }

      if (action === "logs") {
        const limit  = parseInt(url.searchParams.get("limit")  ?? "50");
        const offset = parseInt(url.searchParams.get("offset") ?? "0");
        const { data, error, count } = await supabase
          .from("llm_requests")
          .select(`
            id, agent_id, model_id, provider, model_identifier,
            prompt_tokens, completion_tokens, total_tokens,
            latency_ms, status, error_message, metadata, created_at,
            agent:agents(id,name),
            model:llm_models(id,name)
          `, { count: "exact" })
          .order("created_at", { ascending: false })
          .range(offset, offset + limit - 1);
        if (error) throw new Error(error.message);
        return json({ logs: data ?? [], total: count ?? 0 });
      }

      return json({ error: "Unknown action" }, 400);
    }

    // ── POST endpoint ────────────────────────────────────────────────────────

    if (req.method === "POST") {
      const body = await req.json() as Record<string, unknown>;
      const action = (body.action as string) ?? "execute";

      if (action === "execute") {
        const result = await executeRoute(supabase, body as RouteRequest);
        return json(result);
      }

      if (action === "test") {
        const prompt = (body.prompt as string) ?? "Respond with exactly: 'Router operational.'";
        const result = await executeRoute(supabase, {
          prompt,
          model_id:  body.model_id  as string | undefined,
          provider:  body.provider  as string | undefined,
          agent_id:  body.agent_id  as string | undefined,
          task_type: "test",
          max_tokens: 128,
        });
        return json(result);
      }

      return json({ error: "Unknown action" }, 400);
    }

    return json({ error: "Method not allowed" }, 405);
  } catch (err) {
    return json({ error: String(err) }, 500);
  }
});
