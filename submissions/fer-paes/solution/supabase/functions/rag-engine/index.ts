import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

const CHUNK_SIZE = 600;
const CHUNK_OVERLAP = 80;
const DEFAULT_TOP_K = 5;
const DEFAULT_THRESHOLD = 0.25;

function chunkText(text: string): string[] {
  const chunks: string[] = [];
  const sentences = text
    .replace(/([.!?])\s+/g, "$1\n")
    .split("\n")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);

  let currentChunk = "";

  for (const sentence of sentences) {
    if (currentChunk.length + sentence.length + 1 > CHUNK_SIZE && currentChunk.length > 0) {
      chunks.push(currentChunk.trim());
      const words = currentChunk.split(" ");
      const overlapWords = words.slice(Math.max(0, words.length - 15));
      currentChunk = overlapWords.join(" ") + " " + sentence;
    } else {
      currentChunk += (currentChunk ? " " : "") + sentence;
    }
  }

  if (currentChunk.trim().length > 0) {
    chunks.push(currentChunk.trim());
  }

  if (chunks.length === 0 && text.trim().length > 0) {
    for (let i = 0; i < text.length; i += CHUNK_SIZE - CHUNK_OVERLAP) {
      const chunk = text.slice(i, i + CHUNK_SIZE).trim();
      if (chunk.length > 0) chunks.push(chunk);
    }
  }

  return chunks;
}

async function generateEmbedding(text: string): Promise<number[]> {
  const session = new Supabase.ai.Session("gte-small");
  const result = await session.run(text.slice(0, 2000), {
    mean_pool: true,
    normalize: true,
  });
  return Array.from(result as Float32Array);
}

async function addDocument(
  supabase: ReturnType<typeof createClient>,
  title: string,
  source: string,
  content: string
): Promise<{ document_id: string; chunk_count: number }> {
  const { data: doc, error: docErr } = await supabase
    .from("knowledge_documents")
    .insert({ title, source, content, status: "processing" })
    .select("id")
    .single();
  if (docErr) throw new Error(docErr.message);

  const documentId = (doc as { id: string }).id;
  const chunks = chunkText(content);

  const chunkRows = chunks.map((chunk_text, chunk_index) => ({
    document_id: documentId,
    chunk_text,
    chunk_index,
  }));

  const { data: insertedChunks, error: chunkErr } = await supabase
    .from("knowledge_chunks")
    .insert(chunkRows)
    .select("id, chunk_text");
  if (chunkErr) {
    await supabase.from("knowledge_documents").update({ status: "error" }).eq("id", documentId);
    throw new Error(chunkErr.message);
  }

  const embeddingRows: Array<{ chunk_id: string; embedding: string }> = [];
  for (const chunk of (insertedChunks ?? []) as Array<{ id: string; chunk_text: string }>) {
    try {
      const embedding = await generateEmbedding(chunk.chunk_text);
      embeddingRows.push({
        chunk_id: chunk.id,
        embedding: `[${embedding.join(",")}]`,
      });
    } catch {
      // Continue with remaining chunks
    }
  }

  if (embeddingRows.length > 0) {
    const { error: embErr } = await supabase
      .from("knowledge_embeddings")
      .insert(embeddingRows);
    if (embErr) {
      await supabase.from("knowledge_documents").update({ status: "error" }).eq("id", documentId);
      throw new Error(embErr.message);
    }
  }

  await supabase
    .from("knowledge_documents")
    .update({ status: "ready", chunk_count: chunks.length, updated_at: new Date().toISOString() })
    .eq("id", documentId);

  return { document_id: documentId, chunk_count: chunks.length };
}

async function searchKnowledge(
  supabase: ReturnType<typeof createClient>,
  query: string,
  topK = DEFAULT_TOP_K,
  threshold = DEFAULT_THRESHOLD
): Promise<Array<{ chunk_id: string; document_id: string; chunk_text: string; chunk_index: number; document_title: string; document_source: string; similarity: number }>> {
  const embedding = await generateEmbedding(query);
  const embeddingString = `[${embedding.join(",")}]`;

  const { data, error } = await supabase.rpc("match_knowledge_chunks", {
    query_embedding: embeddingString,
    match_count: topK,
    match_threshold: threshold,
  });

  if (error) throw new Error(error.message);
  return (data ?? []) as Array<{ chunk_id: string; document_id: string; chunk_text: string; chunk_index: number; document_title: string; document_source: string; similarity: number }>;
}

function buildContext(results: Array<{ chunk_text: string; document_title: string; similarity: number }>, query: string): string {
  if (results.length === 0) {
    return "No relevant knowledge base articles found for this query.";
  }

  const lines = [`Relevant knowledge for query: "${query}"\n`];
  results.forEach((r, i) => {
    lines.push(`${i + 1}. [${r.document_title}] ${r.chunk_text}`);
  });

  return lines.join("\n");
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  const url = new URL(req.url);

  try {
    if (req.method === "GET") {
      const docId = url.searchParams.get("document_id");

      if (docId) {
        const { data: doc, error } = await supabase
          .from("knowledge_documents")
          .select("*, knowledge_chunks(id, chunk_text, chunk_index)")
          .eq("id", docId)
          .maybeSingle();
        if (error) throw new Error(error.message);
        if (!doc) return new Response(JSON.stringify({ error: "Document not found" }), { status: 404, headers: { ...corsHeaders, "Content-Type": "application/json" } });
        return new Response(JSON.stringify({ document: doc }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }

      const { data: docs, error } = await supabase
        .from("knowledge_documents")
        .select("id, title, source, chunk_count, status, created_at, updated_at")
        .order("created_at", { ascending: false });
      if (error) throw new Error(error.message);

      const { data: stats } = await supabase.rpc("get_knowledge_stats");

      return new Response(
        JSON.stringify({ documents: docs ?? [], stats: stats?.[0] ?? null, total: (docs ?? []).length }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    if (req.method === "DELETE") {
      const docId = url.searchParams.get("document_id") ?? (await req.json().catch(() => ({}))).document_id;
      if (!docId) return new Response(JSON.stringify({ error: "document_id is required" }), { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } });

      const { error } = await supabase.from("knowledge_documents").delete().eq("id", docId);
      if (error) throw new Error(error.message);

      return new Response(JSON.stringify({ success: true, document_id: docId }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    if (req.method === "POST") {
      const body = await req.json();
      const action: string = body.action ?? "";

      if (action === "add_document" || action === "upload") {
        const title: string = body.title?.trim() ?? "";
        const source: string = body.source?.trim() ?? "";
        const content: string = body.content?.trim() ?? "";

        if (!title) return new Response(JSON.stringify({ error: "title is required" }), { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } });
        if (!content || content.length < 10) return new Response(JSON.stringify({ error: "content must be at least 10 characters" }), { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } });

        const result = await addDocument(supabase, title, source, content);
        return new Response(JSON.stringify({ success: true, ...result }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }

      if (action === "search") {
        const query: string = body.query?.trim() ?? "";
        const topK: number = body.top_k ?? body.topK ?? DEFAULT_TOP_K;
        const threshold: number = body.threshold ?? DEFAULT_THRESHOLD;
        const includeContext: boolean = body.include_context ?? false;

        if (!query) return new Response(JSON.stringify({ error: "query is required" }), { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } });

        const results = await searchKnowledge(supabase, query, topK, threshold);
        const context = includeContext ? buildContext(results, query) : undefined;

        return new Response(
          JSON.stringify({ query, results, context, total: results.length }),
          { headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }

      if (action === "delete_document") {
        const docId: string = body.document_id ?? "";
        if (!docId) return new Response(JSON.stringify({ error: "document_id is required" }), { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } });
        const { error } = await supabase.from("knowledge_documents").delete().eq("id", docId);
        if (error) throw new Error(error.message);
        return new Response(JSON.stringify({ success: true, document_id: docId }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }

      if (action === "build_context") {
        const query: string = body.query?.trim() ?? "";
        const topK: number = body.top_k ?? 4;
        const threshold: number = body.threshold ?? DEFAULT_THRESHOLD;
        if (!query) return new Response(JSON.stringify({ error: "query is required" }), { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } });
        const results = await searchKnowledge(supabase, query, topK, threshold);
        const context = buildContext(results, query);
        return new Response(
          JSON.stringify({ query, context, sources: results.map((r) => r.document_title), total: results.length }),
          { headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }

      return new Response(JSON.stringify({ error: `Unknown action: ${action}` }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: String(err) }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
