/**
 * Vector search utilities.
 * Wraps OpenAI embeddings + Supabase pgvector similarity search.
 *
 * Two stores:
 *  - support_tickets_kb  → RAG / deflection (company knowledge)
 *  - ticket_categories   → ticket routing (Dataset 2 IT tickets)
 */

import { getOpenAIClient } from "@/lib/openai";
import { createSupabaseAdminClient } from "@/lib/supabase/admin";
import type { RagSource } from "@/lib/types";

// ── Embedding ─────────────────────────────────────────────────────────────

export async function embedText(text: string): Promise<number[] | null> {
  const openai = getOpenAIClient();
  if (!openai) return null;

  const res = await openai.embeddings.create({
    model: "text-embedding-3-small",
    input: text.slice(0, 8000), // guard against oversized input
  });
  return res.data[0].embedding;
}

// ── Knowledge-base search (deflection / RAG) ──────────────────────────────

export type KbMatch = {
  id: number;
  description: string;
  resolution: string;
  category: string;
  similarity: number;
};

export async function searchKnowledge(
  text: string,
  opts: { threshold?: number; count?: number } = {},
): Promise<KbMatch[]> {
  const { threshold = 0.65, count = 5 } = opts;

  const embedding = await embedText(text);
  if (!embedding) return [];

  const supabase = createSupabaseAdminClient();
  if (!supabase) return [];

  const { data, error } = await supabase.rpc("match_kb", {
    query_embedding: embedding,
    match_threshold: threshold,
    match_count: count,
  });

  if (error || !data) return [];
  return data as KbMatch[];
}

// ── Ticket classification (routing from Dataset 2) ─────────────────────────

type CategoryMatch = {
  id: number;
  description: string;
  category: string;
  similarity: number;
};

export type ClassifyResult = {
  category: string;
  confidence: number;
  topMatches: CategoryMatch[];
};

export async function classifyByVector(text: string): Promise<ClassifyResult | null> {
  const embedding = await embedText(text);
  if (!embedding) return null;

  const supabase = createSupabaseAdminClient();
  if (!supabase) return null;

  const { data, error } = await supabase.rpc("match_ticket_category", {
    query_embedding: embedding,
    match_count: 7,
  });

  if (error || !data || (data as CategoryMatch[]).length === 0) return null;

  const matches = data as CategoryMatch[];

  // Weighted majority vote: closer matches get higher weight
  const votes: Record<string, number> = {};
  for (const m of matches) {
    votes[m.category] = (votes[m.category] ?? 0) + m.similarity;
  }

  const sorted = Object.entries(votes).sort(([, a], [, b]) => b - a);
  const [topCategory, topScore] = sorted[0];
  const totalScore = sorted.reduce((s, [, v]) => s + v, 0);
  const confidence = Number((topScore / totalScore).toFixed(2));

  return { category: topCategory, confidence, topMatches: matches };
}

// ── Adapter: KbMatch → RagSource (for existing consumers) ─────────────────

export function kbMatchesToRagSources(matches: KbMatch[]): RagSource[] {
  return matches.map((m) => ({
    id: String(m.id),
    description: m.description,
    resolution: m.resolution,
    category: m.category,
    similarity: m.similarity,
  }));
}
