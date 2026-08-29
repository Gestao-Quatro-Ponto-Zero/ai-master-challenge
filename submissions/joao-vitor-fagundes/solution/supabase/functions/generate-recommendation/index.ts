import { createClient } from "npm:@supabase/supabase-js@2";

const PROMPT_VERSION = "power-recommendation-v2";
const PROVIDER = "openai";
const DEFAULT_MODEL = "gpt-5.6-terra";

const DEFAULT_ALLOWED_ORIGINS = [
  "http://127.0.0.1:4173",
  "http://localhost:4173",
  "http://[::1]:4173",
];

const recommendationSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    action_label: {
      type: "string",
      enum: [
        "Contatar",
        "Agendar",
        "Requalificar",
        "Nutrir",
        "Reposicionar",
        "Expandir",
        "Reativar",
        "Encerrar",
      ],
    },
    recommendation: { type: "string" },
  },
  required: ["action_label", "recommendation"],
};

const instructions = `Você é o copiloto comercial do POWER Framework.
Sua resposta aparece diretamente no card aberto pelo vendedor.

Regras:
- Use somente os dados recebidos. Não invente intenção, atividade, stakeholder ou motivo de perda.
- Escolha uma única ação concreta em action_label.
- recommendation deve ter exatamente uma frase, no máximo 24 palavras, começando com um verbo no imperativo.
- Diga o que o vendedor deve fazer agora e conecte a ordem ao sinal mais útil de P, O, W ou E.
- Não escreva introdução, lista, ressalva ou segunda recomendação.
- Não use orientações vagas como "avalie", "considere", "acompanhe", "verifique" ou "analise as informações".
- Interprete Execution Fit baixo como pouca experiência histórica naquele perfil, nunca como incompetência.
- Para Prospecting, use Contatar, Nutrir ou Requalificar.
- Para Engaging, use Agendar, Reposicionar, Nutrir ou Requalificar.
- Para Won, use Expandir.
- Para Lost, use Reativar ou Encerrar.
- Escreva em português do Brasil, de forma firme, simples e prática.`;

function getAllowedOrigins() {
  const configured = Deno.env.get("ALLOWED_ORIGINS");
  return new Set((configured ? configured.split(",") : DEFAULT_ALLOWED_ORIGINS).map((origin) => origin.trim()));
}

function corsHeaders(request: Request) {
  const origin = request.headers.get("Origin");
  return {
    ...(origin && getAllowedOrigins().has(origin) ? { "Access-Control-Allow-Origin": origin } : {}),
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Vary": "Origin",
  };
}

function jsonResponse(request: Request, body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders(request), "Content-Type": "application/json; charset=utf-8" },
  });
}

function positiveIntegerEnvironment(name: string, fallback: number) {
  const value = Number(Deno.env.get(name));
  return Number.isInteger(value) && value > 0 ? value : fallback;
}

function getOutputText(response: Record<string, unknown>): string | null {
  if (typeof response.output_text === "string") return response.output_text;
  const output = Array.isArray(response.output) ? response.output : [];
  for (const item of output as Array<Record<string, unknown>>) {
    const content = Array.isArray(item.content) ? item.content : [];
    for (const part of content as Array<Record<string, unknown>>) {
      if (part.type === "output_text" && typeof part.text === "string") return part.text;
    }
  }
  return null;
}

Deno.serve(async (request) => {
  const origin = request.headers.get("Origin");
  if (origin && !getAllowedOrigins().has(origin)) {
    return jsonResponse(request, { error: "Origin not allowed" }, 403);
  }
  if (request.method === "OPTIONS") return new Response("ok", { headers: corsHeaders(request) });
  if (request.method !== "POST") return jsonResponse(request, { error: "Method not allowed" }, 405);

  const contentLength = Number(request.headers.get("Content-Length") || 0);
  if (contentLength > 1024) return jsonResponse(request, { error: "Request body is too large" }, 413);

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const openAiKey = Deno.env.get("OPENAI_API_KEY");
  if (!supabaseUrl || !serviceRoleKey) return jsonResponse(request, { error: "Service unavailable" }, 500);
  if (!openAiKey) return jsonResponse(request, { error: "Recommendation service unavailable" }, 503);

  let payload: { opportunity_id?: string };
  try {
    payload = await request.json();
  } catch {
    return jsonResponse(request, { error: "Invalid JSON body" }, 400);
  }
  if (!payload.opportunity_id) return jsonResponse(request, { error: "opportunity_id is required" }, 400);
  if (!/^[A-Z0-9]{8}$/.test(payload.opportunity_id)) {
    return jsonResponse(request, { error: "Invalid opportunity_id" }, 400);
  }

  const supabase = createClient(supabaseUrl, serviceRoleKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const { data: profile, error: profileError } = await supabase
    .from("opportunity_power")
    .select("*")
    .eq("opportunity_id", payload.opportunity_id)
    .single();
  if (profileError) {
    if (profileError.code === "PGRST116") {
      return jsonResponse(request, { error: "Opportunity not found" }, 404);
    }
    console.error("Could not load opportunity", profileError.code, profileError.message);
    return jsonResponse(request, { error: "Could not load opportunity" }, 500);
  }
  if (!profile) return jsonResponse(request, { error: "Opportunity not found" }, 404);
  if (!profile.input_hash) return jsonResponse(request, { error: "POWER score is not available" }, 409);

  const { data: cached } = await supabase
    .from("power_recommendations")
    .select("*")
    .eq("opportunity_id", profile.opportunity_id)
    .eq("input_hash", profile.input_hash)
    .eq("prompt_version", PROMPT_VERSION)
    .eq("status", "ready")
    .maybeSingle();
  if (cached) return jsonResponse(request, { status: "ready", cached: true, recommendation: cached });

  const model = Deno.env.get("OPENAI_MODEL") || DEFAULT_MODEL;
  const { data: claimRows, error: claimError } = await supabase.rpc("claim_power_recommendation", {
    p_opportunity_id: profile.opportunity_id,
    p_input_hash: profile.input_hash,
    p_prompt_version: PROMPT_VERSION,
    p_provider: PROVIDER,
    p_model: model,
    p_hourly_limit: positiveIntegerEnvironment("RECOMMENDATION_HOURLY_LIMIT", 500),
    p_daily_limit: positiveIntegerEnvironment("RECOMMENDATION_DAILY_LIMIT", 2000),
  });
  const claim = claimRows?.[0];
  if (claimError || !claim) {
    console.error("Could not reserve recommendation", claimError?.code, claimError?.message);
    return jsonResponse(request, { error: "Could not reserve recommendation" }, 500);
  }

  if (claim.claim_status === "cached") {
    const { data: claimedCache } = await supabase
      .from("power_recommendations")
      .select("*")
      .eq("recommendation_id", claim.recommendation_id)
      .eq("status", "ready")
      .single();
    if (claimedCache) {
      return jsonResponse(request, { status: "ready", cached: true, recommendation: claimedCache });
    }
  }

  if (claim.claim_status === "generating") {
    return jsonResponse(request, { status: "generating", retry_after_ms: 750 }, 202);
  }
  if (claim.claim_status === "rate_limited") {
    return jsonResponse(request, { error: "Demo generation limit reached" }, 429);
  }
  if (claim.claim_status !== "claimed") {
    return jsonResponse(request, { error: "Recommendation is temporarily unavailable" }, 409);
  }

  const modelInput = {
    opportunity: {
      id: profile.opportunity_id,
      stage: profile.deal_stage,
      account: profile.account,
      sector: profile.sector,
      product: profile.product,
      potential_value: profile.potential_value,
      seller: profile.sales_agent,
      manager: profile.manager,
      region: profile.regional_office,
    },
    power: {
      P: { score: profile.propensity_score, evidence: profile.propensity_evidence },
      O: {
        score: profile.opportunity_value_score,
        tier: profile.opportunity_value_tier,
        value: profile.potential_value,
      },
      W: {
        score: profile.warmth_score,
        temperature: profile.warmth_temperature,
        evidence: profile.warmth_evidence,
      },
      E: { score: profile.execution_fit_score, evidence: profile.execution_fit_evidence },
    },
  };

  try {
    const openAiResponse = await fetch("https://api.openai.com/v1/responses", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${openAiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model,
        instructions,
        input: JSON.stringify(modelInput),
        reasoning: { effort: "low" },
        text: {
          verbosity: "low",
          format: {
            type: "json_schema",
            name: "power_recommendation",
            strict: true,
            schema: recommendationSchema,
          },
        },
        max_output_tokens: 250,
        prompt_cache_key: PROMPT_VERSION,
        store: false,
      }),
    });
    const responseBody = await openAiResponse.json();
    if (!openAiResponse.ok) throw new Error(responseBody?.error?.message || "OpenAI request failed");
    const outputText = getOutputText(responseBody);
    if (!outputText) throw new Error("OpenAI returned no output text");
    const result = JSON.parse(outputText);

    const { data: saved, error: saveError } = await supabase
      .from("power_recommendations")
      .update({
        status: "ready",
        action_label: result.action_label,
        recommendation: result.recommendation,
        usage: responseBody.usage || null,
        generated_at: new Date().toISOString(),
        error_message: null,
      })
      .eq("recommendation_id", claim.recommendation_id)
      .select("*")
      .single();
    if (saveError) throw saveError;
    return jsonResponse(request, { status: "ready", cached: false, recommendation: saved });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Recommendation generation failed";
    console.error("Recommendation generation failed", message);
    await supabase
      .from("power_recommendations")
      .update({ status: "error", error_message: message })
      .eq("recommendation_id", claim.recommendation_id);
    return jsonResponse(request, { error: "Recommendation generation failed" }, 502);
  }
});
