// ─── RAG: Semantic KB Search via pgvector ────────────────────────────
// Replaces exact-match KB lookup with cosine similarity search.
// Uses OpenAI text-embedding-3-small (1536 dims) for query embedding.

import { createClient } from "@/lib/supabase/server";

export interface RAGArticle {
  id: string;
  subject: string;
  title: string;
  content: string;
  similarity: number;
}

export interface RAGResult {
  articles: RAGArticle[];
  queryEmbedding: number[];
}

// ─── Generate Embedding ─────────────────────────────────────────────

async function generateEmbedding(text: string): Promise<number[] | null> {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) return null;

  try {
    const res = await fetch("https://api.openai.com/v1/embeddings", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: "text-embedding-3-small",
        input: text,
      }),
    });

    if (!res.ok) return null;

    const data = await res.json();
    return data.data?.[0]?.embedding || null;
  } catch {
    return null;
  }
}

// ─── Semantic KB Search ─────────────────────────────────────────────

export async function searchKB(
  query: string,
  limit = 3
): Promise<RAGResult> {
  const emptyResult: RAGResult = { articles: [], queryEmbedding: [] };

  const queryEmbedding = await generateEmbedding(query);
  if (!queryEmbedding) return emptyResult;

  try {
    const supabase = await createClient();

    // Use raw SQL via rpc for cosine similarity search
    // pgvector <=> operator = cosine distance, so similarity = 1 - distance
    const { data, error } = await supabase.rpc("match_kb_articles", {
      query_embedding: JSON.stringify(queryEmbedding),
      match_count: limit,
    });

    if (error || !data) {
      // Fallback: if the RPC doesn't exist yet, return empty
      console.error("RAG search error:", error?.message);
      return emptyResult;
    }

    const articles: RAGArticle[] = (
      data as Array<{
        id: string;
        subject: string;
        title: string;
        content: string;
        similarity: number;
      }>
    ).map((row) => ({
      id: row.id,
      subject: row.subject,
      title: row.title,
      content: row.content,
      similarity: Math.round(row.similarity * 100) / 100,
    }));

    return { articles, queryEmbedding };
  } catch {
    return emptyResult;
  }
}

// ─── Format Articles for Prompt Context ─────────────────────────────

export function formatArticlesForPrompt(articles: RAGArticle[]): string {
  if (articles.length === 0) return "";

  return articles
    .map((a, i) => {
      const pct = Math.round(a.similarity * 100);
      return `Artigo ${i + 1} (${pct}% relevante): ${a.title}\n${a.content}`;
    })
    .join("\n\n");
}
