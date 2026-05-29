import { getOpenAIClient } from "@/lib/openai";
import { searchKnowledge, kbMatchesToRagSources } from "@/lib/vector-search";
import { findTopKbMatches } from "@/lib/mock-db";
import type { RagSource } from "@/lib/types";

const LEGACY_KB_PATTERNS = [
  "não consigo acessar o sistema após reset de senha",
  "notebook corporativo sem conexão com vpn",
  "erro ao anexar arquivo grande no portal",
  "sistema lento ao abrir chamados",
  "solicitação de compra sem aprovação",
];

function isLegacyKbSource(source: RagSource) {
  const description = source.description.toLowerCase();
  return LEGACY_KB_PATTERNS.some((pattern) => description.includes(pattern));
}

function normalizeSources(text: string, initialSources: RagSource[]) {
  const filtered = initialSources.filter((source) => !isLegacyKbSource(source));
  if (filtered.length >= 3) return filtered;

  const fallback = findTopKbMatches(text, 5).filter((source) => !isLegacyKbSource(source));
  const merged = [...filtered];

  for (const candidate of fallback) {
    if (!merged.some((source) => source.description === candidate.description)) {
      merged.push(candidate);
    }
    if (merged.length >= 5) break;
  }

  return merged;
}

export async function buildRagSuggestion(text: string): Promise<{
  suggestion: string;
  confidence: number;
  sources: RagSource[];
}> {
  // Try real vector search; fall back to keyword mock if Supabase is unavailable
  const kbMatches = await searchKnowledge(text, { threshold: 0.60, count: 5 }).catch(() => []);
  const rawSources: RagSource[] = kbMatches.length > 0
    ? kbMatchesToRagSources(kbMatches)
    : findTopKbMatches(text, 5);
  const sources = normalizeSources(text, rawSources);

  const openai = getOpenAIClient();

  if (!openai) {
    return {
      suggestion:
        "Com base em casos similares, tente: verificar credenciais, reiniciar sessão e repetir a ação. Se persistir, siga com abertura de ticket para priorização.",
      confidence: Number((sources[0]?.similarity ?? 0.5).toFixed(2)),
      sources,
    };
  }

  try {
    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      response_format: { type: "json_object" },
      messages: [
        {
          role: "system",
          content:
            "Você é um assistente de suporte técnico. Use apenas as fontes enviadas para responder. Retorne JSON com suggestion (string), confidence (0..1) e used_sources (array de ids).",
        },
        {
          role: "user",
          content: JSON.stringify({ ticket_text: text, sources }),
        },
      ],
    });

    const raw = completion.choices[0]?.message?.content;
    if (!raw) throw new Error("Resposta vazia do modelo");

    const parsed = JSON.parse(raw) as {
      suggestion?: string;
      confidence?: number;
      used_sources?: string[];
    };

    return {
      suggestion: parsed.suggestion ?? "Não tenho confiança para responder com precisão.",
      confidence: Number((parsed.confidence ?? 0.4).toFixed(2)),
      sources,
    };
  } catch {
    return {
      suggestion:
        "Não tenho confiança para responder com precisão neste momento. Recomendo abrir ticket para análise humana.",
      confidence: 0.35,
      sources,
    };
  }
}
