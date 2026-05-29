import { NextRequest } from "next/server";

import { fail, ok, readBody } from "@/lib/api";
import { classifyByVector } from "@/lib/vector-search";
import { getOpenAIClient } from "@/lib/openai";
import type { TicketCategory, TicketPriority } from "@/lib/types";

type Body = { text?: string };

// Dataset 2 categories → internal TicketCategory map
const CATEGORY_MAP: Record<string, TicketCategory> = {
  "Hardware":             "Hardware",
  "HR Support":           "HR",
  "Access":               "Access",
  "Miscellaneous":        "Other",
  "Storage":              "Storage",
  "Purchase":             "Purchase",
  "Internal Project":     "Other",
  "Administrative rights":"Access",
  // GPT-returned categories (fallback path)
  "Software":             "Software",
  "Network":              "Network",
  "Other":                "Other",
};

function mapCategory(raw: string): TicketCategory {
  return CATEGORY_MAP[raw] ?? "Other";
}

function keywordFallback(text: string): { category: TicketCategory; priority: TicketPriority; confidence: number; reasoning: string } {
  const lower = text.toLowerCase();
  let category: TicketCategory = "Other";
  let priority: TicketPriority = "medium";

  if (/senha|login|acesso|password|access/.test(lower))    category = "Access";
  else if (/vpn|rede|internet|network/.test(lower))         category = "Network";
  else if (/arquivo|upload|storage|disk/.test(lower))       category = "Storage";
  else if (/notebook|teclado|hardware|mouse|monitor/.test(lower)) category = "Hardware";
  else if (/compra|pedido|purchase|order/.test(lower))      category = "Purchase";
  else if (/rh|folha|beneficio|hr support/.test(lower))     category = "HR";
  else if (/erro|sistema|app|software/.test(lower))         category = "Software";

  if (/urgente|parado|bloqueado/.test(lower))  priority = "high";
  if (/produção|critico|crítico/.test(lower))  priority = "critical";

  return { category, priority, confidence: 0.55, reasoning: "Classificação por heurística de palavras-chave." };
}

export async function POST(request: NextRequest) {
  const body = await readBody<Body>(request);
  const text = body?.text?.trim();
  if (!text) return fail("Campo text é obrigatório", 400);

  // ── 1. Vector similarity against Dataset 2 (preferred path) ──────────────
  try {
    const vectorResult = await classifyByVector(text);
    if (vectorResult && vectorResult.confidence >= 0.35) {
      const category = mapCategory(vectorResult.category);
      const priority: TicketPriority = /urgente|parado|critico|crítico/i.test(text) ? "critical" : "medium";
      return ok({
        category,
        priority,
        confidence: vectorResult.confidence,
        reasoning: `Classificado por similaridade vetorial com Dataset 2 (top match: ${vectorResult.topMatches[0]?.category ?? category}).`,
        method: "vector",
      });
    }
  } catch {
    // fall through to LLM
  }

  // ── 2. LLM fallback ────────────────────────────────────────────────────────
  const openai = getOpenAIClient();
  if (!openai) return ok(keywordFallback(text));

  try {
    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      response_format: { type: "json_object" },
      messages: [
        {
          role: "system",
          content:
            "Você classifica tickets de suporte de TI. Retorne JSON com: category (Hardware|Software|Access|Storage|HR|Purchase|Network|Other), priority (low|medium|high|critical), confidence (0..1), reasoning (string).",
        },
        { role: "user", content: text },
      ],
    });

    const parsed = JSON.parse(completion.choices[0]?.message?.content ?? "{}") as {
      category?: string; priority?: string; confidence?: number; reasoning?: string;
    };

    return ok({
      category:  mapCategory(parsed.category ?? "Other"),
      priority:  (["low","medium","high","critical"].includes(parsed.priority ?? "") ? parsed.priority : "medium") as TicketPriority,
      confidence: Number((parsed.confidence ?? 0.7).toFixed(2)),
      reasoning:  parsed.reasoning ?? "Classificação pelo modelo.",
      method: "llm",
    });
  } catch {
    return ok({ ...keywordFallback(text), method: "keyword" });
  }
}
