import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

const DEFAULT_TOP_K     = 5;
const DEFAULT_THRESHOLD = 0.25;
const SEMANTIC_WEIGHT   = 0.7;
const KEYWORD_WEIGHT    = 0.3;

type Strategy = "semantic" | "keyword" | "hybrid";

interface SemanticChunk {
  chunk_id:        string;
  document_id:     string;
  chunk_text:      string;
  chunk_index:     number;
  document_title:  string;
  document_source: string;
  similarity:      number;
}

interface KeywordChunk {
  chunk_id:        string;
  document_id:     string;
  chunk_text:      string;
  chunk_index:     number;
  section_title:   string;
  document_title:  string;
  document_source: string;
  keyword_score:   number;
}

export interface RetrievalResult {
  chunk_id:        string;
  document_id:     string;
  chunk_text:      string;
  chunk_index:     number;
  section_title:   string;
  document_title:  string;
  document_source: string;
  score:           number;
  semantic_score:  number;
  keyword_score:   number;
  match_type:      "semantic" | "keyword" | "hybrid";
}

function ok(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

function err(msg: string, status = 400): Response {
  return new Response(JSON.stringify({ error: msg }), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

async function generateEmbedding(text: string): Promise<number[]> {
  const session = new Supabase.ai.Session("gte-small");
  const result  = await session.run(text.slice(0, 2000), {
    mean_pool: true,
    normalize: true,
  });
  return Array.from(result as Float32Array);
}

async function searchSemantic(
  supabase: ReturnType<typeof createClient>,
  query: string,
  topK = DEFAULT_TOP_K,
  threshold = DEFAULT_THRESHOLD,
): Promise<SemanticChunk[]> {
  const vector       = await generateEmbedding(query);
  const embeddingStr = `[${vector.join(",")}]`;

  const { data, error } = await supabase.rpc("match_knowledge_chunks", {
    query_embedding: embeddingStr,
    match_count:     topK,
    match_threshold: threshold,
  });

  if (error) throw new Error(error.message);
  return (data ?? []) as SemanticChunk[];
}

async function searchKeyword(
  supabase: ReturnType<typeof createClient>,
  query: string,
  topK = DEFAULT_TOP_K,
): Promise<KeywordChunk[]> {
  const { data, error } = await supabase.rpc("search_keyword_chunks", {
    query_text:  query,
    match_count: topK,
    min_rank:    0.01,
  });

  if (error) throw new Error(error.message);
  return (data ?? []) as KeywordChunk[];
}

function rerankResults(
  semanticChunks: SemanticChunk[],
  keywordChunks:  KeywordChunk[],
  topK:           number,
): RetrievalResult[] {
  const maxKeyword = keywordChunks.reduce((m, c) => Math.max(m, c.keyword_score), 0) || 1;

  const map = new Map<string, RetrievalResult>();

  for (const c of semanticChunks) {
    map.set(c.chunk_id, {
      chunk_id:        c.chunk_id,
      document_id:     c.document_id,
      chunk_text:      c.chunk_text,
      chunk_index:     c.chunk_index,
      section_title:   "",
      document_title:  c.document_title,
      document_source: c.document_source,
      semantic_score:  c.similarity,
      keyword_score:   0,
      score:           SEMANTIC_WEIGHT * c.similarity,
      match_type:      "semantic",
    });
  }

  for (const c of keywordChunks) {
    const normKw = c.keyword_score / maxKeyword;
    if (map.has(c.chunk_id)) {
      const existing = map.get(c.chunk_id)!;
      existing.keyword_score = normKw;
      existing.score         = SEMANTIC_WEIGHT * existing.semantic_score + KEYWORD_WEIGHT * normKw;
      existing.match_type    = "hybrid";
      existing.section_title = c.section_title;
    } else {
      map.set(c.chunk_id, {
        chunk_id:        c.chunk_id,
        document_id:     c.document_id,
        chunk_text:      c.chunk_text,
        chunk_index:     c.chunk_index,
        section_title:   c.section_title,
        document_title:  c.document_title,
        document_source: c.document_source,
        semantic_score:  0,
        keyword_score:   normKw,
        score:           KEYWORD_WEIGHT * normKw,
        match_type:      "keyword",
      });
    }
  }

  return Array.from(map.values())
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);
}

async function searchHybrid(
  supabase: ReturnType<typeof createClient>,
  query: string,
  topK = DEFAULT_TOP_K,
  threshold = DEFAULT_THRESHOLD,
): Promise<RetrievalResult[]> {
  const [semChunks, kwChunks] = await Promise.all([
    searchSemantic(supabase, query, topK * 2, threshold).catch((): SemanticChunk[] => []),
    searchKeyword(supabase, query, topK * 2).catch((): KeywordChunk[] => []),
  ]);

  return rerankResults(semChunks, kwChunks, topK);
}

function buildContext(
  results: RetrievalResult[],
  query:   string,
  format:  "plain" | "structured" = "structured",
): string {
  if (results.length === 0) {
    return "No relevant knowledge base articles found for this query.";
  }

  if (format === "plain") {
    return results.map((r) => r.chunk_text).join("\n\n");
  }

  const lines = [`Relevant knowledge for: "${query}"\n`];
  results.forEach((r, i) => {
    const score  = Math.round(r.score * 100);
    const source = r.section_title ? `${r.document_title} › ${r.section_title}` : r.document_title;
    lines.push(`${i + 1}. [${source}] (${score}% match)\n${r.chunk_text}`);
  });

  return lines.join("\n\n");
}

async function retrieveKnowledge(
  supabase:  ReturnType<typeof createClient>,
  query:     string,
  topK:      number,
  strategy:  Strategy,
  threshold: number,
): Promise<{ results: RetrievalResult[]; context: string }> {
  let results: RetrievalResult[];

  switch (strategy) {
    case "keyword": {
      const kw = await searchKeyword(supabase, query, topK);
      const mx = kw.reduce((m, c) => Math.max(m, c.keyword_score), 0) || 1;
      results = kw.map((c) => ({
        chunk_id:        c.chunk_id,
        document_id:     c.document_id,
        chunk_text:      c.chunk_text,
        chunk_index:     c.chunk_index,
        section_title:   c.section_title,
        document_title:  c.document_title,
        document_source: c.document_source,
        semantic_score:  0,
        keyword_score:   c.keyword_score / mx,
        score:           c.keyword_score / mx,
        match_type:      "keyword" as const,
      }));
      break;
    }
    case "semantic": {
      const sem = await searchSemantic(supabase, query, topK, threshold);
      results = sem.map((c) => ({
        chunk_id:        c.chunk_id,
        document_id:     c.document_id,
        chunk_text:      c.chunk_text,
        chunk_index:     c.chunk_index,
        section_title:   "",
        document_title:  c.document_title,
        document_source: c.document_source,
        semantic_score:  c.similarity,
        keyword_score:   0,
        score:           c.similarity,
        match_type:      "semantic" as const,
      }));
      break;
    }
    default: {
      results = await searchHybrid(supabase, query, topK, threshold);
    }
  }

  const context = buildContext(results, query);
  return { results, context };
}

async function logRetrieval(
  supabase:     ReturnType<typeof createClient>,
  query:        string,
  strategy:     Strategy,
  resultCount:  number,
  topScore:     number,
  latencyMs:    number,
  agentId?:     string,
): Promise<void> {
  await supabase.from("retrieval_logs").insert({
    query,
    strategy,
    result_count: resultCount,
    top_score:    Math.round(topScore * 10000) / 10000,
    latency_ms:   latencyMs,
    agent_id:     agentId ?? null,
  }).then(() => void 0).catch(() => void 0);
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  const url   = new URL(req.url);
  const parts = url.pathname
    .replace(/^\/retrieval-service\/?/, "")
    .split("/")
    .filter(Boolean);

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
  );

  try {
    if (req.method === "GET") {
      if (parts[0] === "test") {
        const query    = url.searchParams.get("query") ?? "refund policy";
        const strategy = (url.searchParams.get("strategy") ?? "hybrid") as Strategy;
        const topK     = parseInt(url.searchParams.get("top_k") ?? "3", 10);

        const t0    = Date.now();
        const { results, context } = await retrieveKnowledge(supabase, query, topK, strategy, DEFAULT_THRESHOLD);
        const ms    = Date.now() - t0;

        await logRetrieval(supabase, query, strategy, results.length, results[0]?.score ?? 0, ms);

        return ok({
          query,
          strategy,
          results,
          context,
          total:      results.length,
          latency_ms: ms,
        });
      }

      if (parts[0] === "stats") {
        const { data, error } = await supabase.rpc("get_retrieval_stats");
        if (error) throw new Error(error.message);
        return ok(data?.[0] ?? {});
      }

      return err("Not found", 404);
    }

    if (req.method === "POST") {
      const body      = await req.json().catch(() => ({}));
      const query     = ((body as Record<string, unknown>).query as string ?? "").trim();
      const topK      = (body as Record<string, unknown>).top_k as number ?? DEFAULT_TOP_K;
      const threshold = (body as Record<string, unknown>).threshold as number ?? DEFAULT_THRESHOLD;
      const strategy  = ((body as Record<string, unknown>).strategy as Strategy) ?? "hybrid";
      const agentId   = (body as Record<string, unknown>).agent_id as string | undefined;

      if (!query) return err("query is required");

      const route = parts[0];

      if (route === "search" || route === undefined) {
        const t0 = Date.now();
        const { results, context } = await retrieveKnowledge(supabase, query, topK, strategy, threshold);
        const ms = Date.now() - t0;

        await logRetrieval(supabase, query, strategy, results.length, results[0]?.score ?? 0, ms, agentId);

        return ok({
          query,
          strategy,
          results,
          total:      results.length,
          latency_ms: ms,
          context:    (body as Record<string, unknown>).include_context ? context : undefined,
        });
      }

      if (route === "context") {
        const format = ((body as Record<string, unknown>).format as "plain" | "structured") ?? "structured";
        const t0     = Date.now();
        const { results, context } = await retrieveKnowledge(supabase, query, topK, strategy, threshold);
        const ms     = Date.now() - t0;

        await logRetrieval(supabase, query, strategy, results.length, results[0]?.score ?? 0, ms, agentId);

        return ok({
          query,
          strategy,
          context:  buildContext(results, query, format),
          sources:  results.map((r) => ({
            document_title: r.document_title,
            section_title:  r.section_title,
            score:          r.score,
          })),
          total:      results.length,
          latency_ms: ms,
        });
      }

      return err("Unknown route", 404);
    }

    return err("Method not allowed", 405);
  } catch (e) {
    return err(e instanceof Error ? e.message : "Internal error", 500);
  }
});
