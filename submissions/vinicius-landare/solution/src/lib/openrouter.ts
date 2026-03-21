/**
 * OpenRouter Client com fallback de modelos
 * Primário: Gemini 3 Flash → Fallback 1: GPT-4o → Fallback 2: Claude Sonnet 4.5
 *
 * Para o pipeline de conteúdo (3-step), cada step usa modelo fixo:
 * - Draft: Gemini 3 Flash (criativo)
 * - Critique: Claude Sonnet 4.5 (analítico)
 * - Refinement: Gemini 3 Flash (formatação)
 */

const FALLBACK_MODELS = [
  "google/gemini-2.0-flash-001",
  "openai/gpt-4o",
  "anthropic/claude-sonnet-4-5",
] as const;

export const CONTENT_MODELS = {
  draft: "google/gemini-2.0-flash-001",
  critique: "anthropic/claude-sonnet-4-5",
  refinement: "google/gemini-2.0-flash-001",
} as const;

interface CallLLMOptions {
  system: string;
  user: string;
  temperature?: number;
  maxTokens?: number;
  model?: string;
}

interface OpenRouterResponse {
  choices: Array<{
    message: {
      content: string;
      role: string;
    };
  }>;
  _model_used?: string;
}

export async function callLLM(opts: CallLLMOptions): Promise<OpenRouterResponse> {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    throw new Error("OPENROUTER_API_KEY not configured");
  }

  const models = opts.model ? [opts.model] : [...FALLBACK_MODELS];

  for (const model of models) {
    try {
      const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${apiKey}`,
          "Content-Type": "application/json",
          "HTTP-Referer": "https://g4-social-metrics.vercel.app",
          "X-Title": "G4 Social Metrics",
        },
        body: JSON.stringify({
          model,
          messages: [
            { role: "system", content: opts.system },
            { role: "user", content: opts.user },
          ],
          temperature: opts.temperature ?? 0.7,
          max_tokens: opts.maxTokens ?? 2000,
          response_format: { type: "json_object" },
        }),
      });

      if (res.ok) {
        const data = await res.json();
        return { ...data, _model_used: model };
      }

      console.warn(`OpenRouter model ${model} failed with status ${res.status}, trying next...`);
    } catch (err) {
      console.warn(`OpenRouter model ${model} threw error:`, err);
      continue;
    }
  }

  throw new Error("All LLM models failed");
}

/**
 * Extrai o conteúdo de texto da resposta do OpenRouter
 */
export function extractContent(response: OpenRouterResponse): string {
  return response.choices?.[0]?.message?.content ?? "";
}

/**
 * Extrai e parseia JSON da resposta do OpenRouter
 */
export function extractJSON<T = unknown>(response: OpenRouterResponse): T {
  const content = extractContent(response);
  // Tenta parsear diretamente
  try {
    return JSON.parse(content);
  } catch {
    // Tenta extrair JSON de markdown code block
    const jsonMatch = content.match(/```json?\s*([\s\S]*?)```/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[1].trim());
    }
    throw new Error(`Failed to parse JSON from LLM response: ${content.substring(0, 200)}`);
  }
}
