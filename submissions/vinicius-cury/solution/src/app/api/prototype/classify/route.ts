import { NextRequest, NextResponse } from "next/server";
import { z } from "zod/v4";

import { D2_TO_D1, D2_CATEGORIES, SCENARIO_LABELS } from "@/lib/routing/taxonomy";
import { getScenarioForPair } from "@/lib/routing/engine";

// ─── Input Validation ────────────────────────────────────────────────

const ClassifyInput = z.object({
  text: z.string().min(1, "Texto obrigatório"),
  channel: z.string().min(1, "Canal obrigatório"),
  conversationHistory: z.array(z.string()).optional(),
});

// ─── OpenAI Helpers ──────────────────────────────────────────────────

async function callOpenAI(
  model: string,
  systemPrompt: string,
  userPrompt: string,
  options?: { logprobs?: boolean }
): Promise<{ content: string; avgLogprob?: number } | null> {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) return null;

  try {
    const body: Record<string, unknown> = {
      model,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt },
      ],
      temperature: 0.1,
      max_tokens: 256,
    };

    // Request logprobs for confidence estimation
    if (options?.logprobs) {
      body.logprobs = true;
      body.top_logprobs = 1;
    }

    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) return null;

    const data = await res.json();
    const choice = data.choices?.[0];
    const content = choice?.message?.content?.trim();
    if (!content) return null;

    // Extract average logprob for confidence estimation
    let avgLogprob: number | undefined;
    if (choice?.logprobs?.content) {
      const logprobs = choice.logprobs.content.map(
        (t: { logprob: number }) => t.logprob
      );
      if (logprobs.length > 0) {
        avgLogprob = logprobs.reduce((a: number, b: number) => a + b, 0) / logprobs.length;
      }
    }

    return { content, avgLogprob };
  } catch {
    return null;
  }
}

// ─── Stage 1: D2 Classification (fine-tuned model) ──────────────────

async function classifyD2(
  text: string,
  history?: string[]
): Promise<{ category: string; confidence: number } | null> {
  const modelId = process.env.OPENAI_FINETUNE_MODEL_ID;
  if (!modelId) {
    // Fallback to standard gpt-4o-mini if fine-tuned model not configured
    return classifyD2Fallback(text, history);
  }

  const categories = D2_CATEGORIES.join(", ");
  const systemPrompt = `You are a support ticket classifier. Classify the ticket into exactly one of these categories: ${categories}.

Respond in JSON format: {"category": "<category>", "confidence": <0.0-1.0>}
Only respond with the JSON, nothing else.`;

  const contextBlock = history?.length
    ? `\nPrevious messages:\n${history.map((m) => `- ${m}`).join("\n")}\n\nLatest message:`
    : "";

  const userPrompt = `${contextBlock}\n${text}`;
  const result = await callOpenAI(modelId, systemPrompt, userPrompt, { logprobs: true });
  if (!result) return classifyD2Fallback(text, history);

  const content = result.content;

  // Compute confidence from logprobs (convert avg logprob to probability)
  const logprobConfidence = result.avgLogprob !== undefined
    ? Math.min(Math.exp(result.avgLogprob), 1.0)
    : undefined;

  // Try JSON parse first
  try {
    const parsed = JSON.parse(content);
    const category = parsed.category as string;
    // Use logprob-derived confidence if available, else model's self-reported confidence
    const confidence = logprobConfidence
      ?? (typeof parsed.confidence === "number" ? parsed.confidence : 0.5);

    if (D2_CATEGORIES.includes(category as (typeof D2_CATEGORIES)[number])) {
      return { category, confidence: Math.round(confidence * 100) / 100 };
    }
  } catch {
    // Fine-tuned model might return plain text category name
  }

  // Try matching plain text response against category list
  const normalized = content.toLowerCase().trim();
  for (const cat of D2_CATEGORIES) {
    if (normalized === cat.toLowerCase() || normalized.includes(cat.toLowerCase())) {
      const conf = logprobConfidence ?? 0.85;
      return { category: cat, confidence: Math.round(conf * 100) / 100 };
    }
  }

  // If fine-tuned model returned something unrecognizable, use standard model
  return classifyD2Fallback(text, history);
}

// Fallback classification using standard gpt-4o-mini
async function classifyD2Fallback(
  text: string,
  history?: string[]
): Promise<{ category: string; confidence: number } | null> {
  const categories = D2_CATEGORIES.join(", ");
  const systemPrompt = `You are a support ticket classifier. Given a customer message, classify it into exactly one of these categories: ${categories}.

Consider the FULL conversation context when classifying.

Respond in JSON format: {"category": "<category>", "confidence": <0.0-1.0>}
Only respond with the JSON, nothing else.`;

  const contextBlock = history?.length
    ? `Previous messages from the customer:\n${history.map((m) => `- ${m}`).join("\n")}\n\nLatest message:`
    : "";

  const userPrompt = `${contextBlock}\n${text}`;
  const result = await callOpenAI("gpt-4o-mini", systemPrompt, userPrompt);
  if (!result) return null;

  try {
    // Try JSON parse
    const parsed = JSON.parse(result.content);
    const category = parsed.category as string;
    const confidence = typeof parsed.confidence === "number" ? parsed.confidence : 0.5;

    if (D2_CATEGORIES.includes(category as (typeof D2_CATEGORIES)[number])) {
      return { category, confidence: Math.min(confidence, 0.75) }; // Cap fallback confidence
    }
  } catch {
    // Try plain text match
    const normalized = result.content.toLowerCase().trim();
    for (const cat of D2_CATEGORIES) {
      if (normalized.includes(cat.toLowerCase())) {
        return { category: cat, confidence: 0.6 };
      }
    }
  }

  return null;
}

// ─── Stage 2: D1 Sub-classification (zero-shot) ─────────────────────

async function classifyD1(
  text: string,
  category: string
): Promise<{ subject: string } | null> {
  const options = D2_TO_D1[category];
  if (!options || options.length === 0) return null;

  const optionList = [...options, "Other"].join(", ");
  const systemPrompt = `You are a support ticket sub-classifier. Given a ticket already classified as "${category}", choose the most specific subject from: ${optionList}.

Respond in JSON format: {"subject": "<subject>"}
Only respond with the JSON, nothing else.`;

  const result = await callOpenAI("gpt-4o-mini", systemPrompt, text);
  if (!result) return null;

  try {
    const parsed = JSON.parse(result.content);
    const subject = parsed.subject as string;
    return { subject };
  } catch {
    return null;
  }
}

// ─── KB Lookup (legacy exact-match — replaced by RAG in message route) ──

// ─── Shared classification function (callable from other routes) ────

export interface ClassifyResult {
  category: string;
  subject: string;
  scenario: string;
  confidence: number;
  action: string;
  explanation: string;
  kb_suggestion: null;
  fallback: boolean;
}

export async function classifyTicket(input: {
  text: string;
  channel: string;
  conversationHistory?: string[];
}): Promise<ClassifyResult> {
  const { text, channel, conversationHistory } = input;

  // Stage 1: D2 classification
  const d2Result = await classifyD2(text, conversationHistory);

  if (!d2Result) {
    const fallbackSubjects = Object.values(D2_TO_D1).flat();
    const randomSubject =
      fallbackSubjects[Math.floor(Math.random() * fallbackSubjects.length)];

    return {
      category: "unknown",
      subject: randomSubject,
      scenario: "manter",
      confidence: 0,
      action: "Classificador indisponível. Atribuição aleatória.",
      explanation: "O serviço de classificação está temporariamente indisponível.",
      kb_suggestion: null,
      fallback: true,
    };
  }

  const { category, confidence } = d2Result;

  // Stage 2: D1 sub-classification
  const d1Result = await classifyD1(text, category);
  const subject = d1Result?.subject || D2_TO_D1[category]?.[0] || "Software issue";

  // Stage 3: Routing — get scenario for (channel, subject) pair
  let scenario = "manter";
  let action = "Canal funciona bem. Não alterar.";
  let explanation = "";

  try {
    const pairResult = getScenarioForPair(channel, subject);
    if (pairResult) {
      scenario = pairResult.scenario;
      const scenarioInfo = SCENARIO_LABELS[scenario];
      action = scenarioInfo?.action || action;
      explanation = `r(tempo,CSAT)=${pairResult.rPair ?? "N/A"}, CSAT médio=${pairResult.avgCsat}`;

      if (pairResult.redirectTo) {
        explanation += `, redirecionar para: ${pairResult.redirectTo}`;
      }
    } else {
      explanation = "Par canal/assunto sem dados históricos suficientes.";
    }
  } catch {
    explanation = "Erro ao consultar matriz de roteamento.";
  }

  return {
    category,
    subject,
    scenario,
    confidence,
    action,
    explanation,
    kb_suggestion: null,
    fallback: false,
  };
}

// ─── Main Handler ───────────────────────────────────────────────────

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: "Corpo da requisição inválido" },
      { status: 400 }
    );
  }

  const parsed = ClassifyInput.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Dados inválidos", details: parsed.error.issues },
      { status: 400 }
    );
  }

  const result = await classifyTicket(parsed.data);
  return NextResponse.json(result);
}
