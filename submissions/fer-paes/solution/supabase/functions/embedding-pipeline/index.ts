import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

const PROVIDER    = "supabase-ai";
const MODEL       = "gte-small";
const BATCH_LIMIT = 50;

function ok(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

function err(msg: string, status = 400) {
  return new Response(JSON.stringify({ error: msg }), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

async function generateEmbedding(text: string): Promise<number[]> {
  const session = new Supabase.ai.Session(MODEL);
  const result  = await session.run(text.slice(0, 2000), {
    mean_pool: true,
    normalize: true,
  });
  return Array.from(result as Float32Array);
}

interface ChunkRow {
  id:         string;
  chunk_text: string;
  chunk_index: number;
}

interface EmbeddingStatusResult {
  document_id:      string;
  total_chunks:     number;
  embedded_chunks:  number;
  pending_chunks:   number;
  embedding_status: string;
  provider:         string;
  model:            string;
  is_indexed:       boolean;
}

async function getEmbeddingStatus(
  supabase: ReturnType<typeof createClient>,
  documentId: string,
): Promise<EmbeddingStatusResult> {
  const { data: doc } = await supabase
    .from("knowledge_documents")
    .select("id, chunk_count, embedding_status")
    .eq("id", documentId)
    .maybeSingle();

  if (!doc) throw new Error("Document not found");

  const { count: embeddedCount } = await supabase
    .from("knowledge_embeddings")
    .select("id", { count: "exact", head: true })
    .in(
      "chunk_id",
      (
        await supabase
          .from("knowledge_chunks")
          .select("id")
          .eq("document_id", documentId)
      ).data?.map((c: { id: string }) => c.id) ?? [],
    );

  const totalChunks   = (doc as { chunk_count: number }).chunk_count;
  const embCount      = embeddedCount ?? 0;
  const pendingChunks = Math.max(0, totalChunks - embCount);
  const isIndexed     = embCount > 0 && embCount >= totalChunks;

  return {
    document_id:      documentId,
    total_chunks:     totalChunks,
    embedded_chunks:  embCount,
    pending_chunks:   pendingChunks,
    embedding_status: (doc as { embedding_status: string }).embedding_status,
    provider:         PROVIDER,
    model:            MODEL,
    is_indexed:       isIndexed,
  };
}

async function runEmbeddingPipeline(
  supabase: ReturnType<typeof createClient>,
  documentId: string,
  reindex: boolean,
): Promise<{ embedded: number; skipped: number; errors: number; total: number }> {
  const { data: docData } = await supabase
    .from("knowledge_documents")
    .select("id, title")
    .eq("id", documentId)
    .maybeSingle();

  if (!docData) throw new Error("Document not found");

  if (reindex) {
    const { data: chunkIds } = await supabase
      .from("knowledge_chunks")
      .select("id")
      .eq("document_id", documentId);

    if (chunkIds && chunkIds.length > 0) {
      await supabase
        .from("knowledge_embeddings")
        .delete()
        .in("chunk_id", chunkIds.map((c: { id: string }) => c.id));
    }
  }

  await supabase
    .from("knowledge_documents")
    .update({ embedding_status: "embedding" })
    .eq("id", documentId);

  const { data: allChunks, error: chunksErr } = await supabase
    .from("knowledge_chunks")
    .select("id, chunk_text, chunk_index")
    .eq("document_id", documentId)
    .order("chunk_index", { ascending: true })
    .limit(BATCH_LIMIT);

  if (chunksErr) throw new Error(chunksErr.message);
  const chunks = (allChunks ?? []) as ChunkRow[];

  let existingChunkIds = new Set<string>();

  if (!reindex && chunks.length > 0) {
    const { data: existing } = await supabase
      .from("knowledge_embeddings")
      .select("chunk_id")
      .in("chunk_id", chunks.map((c) => c.id));
    existingChunkIds = new Set((existing ?? []).map((e: { chunk_id: string }) => e.chunk_id));
  }

  let embedded = 0;
  let skipped  = 0;
  let errors   = 0;

  for (const chunk of chunks) {
    if (existingChunkIds.has(chunk.id)) {
      skipped++;
      continue;
    }

    try {
      const vector    = await generateEmbedding(chunk.chunk_text);
      const embedding = `[${vector.join(",")}]`;

      const { error: insertErr } = await supabase
        .from("knowledge_embeddings")
        .upsert(
          { chunk_id: chunk.id, embedding, provider: PROVIDER, model: MODEL },
          { onConflict: "chunk_id" },
        );

      if (insertErr) {
        errors++;
      } else {
        embedded++;
      }
    } catch {
      errors++;
    }
  }

  const allEmbedded = embedded + skipped;
  const total       = chunks.length;
  const newStatus   = errors > 0 && allEmbedded === 0 ? "error" : "embedded";

  await supabase
    .from("knowledge_documents")
    .update({
      embedding_status: newStatus,
      status: newStatus === "embedded" ? "ready" : "error",
    })
    .eq("id", documentId);

  return { embedded, skipped, errors, total };
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  const url    = new URL(req.url);
  const parts  = url.pathname
    .replace(/^\/embedding-pipeline\/?/, "")
    .split("/")
    .filter(Boolean);

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
  );

  try {
    if (req.method === "GET") {
      if (parts.length === 2 && parts[1] === "status") {
        const status = await getEmbeddingStatus(supabase, parts[0]);
        return ok(status);
      }
      return err("Not found", 404);
    }

    if (req.method === "POST") {
      let documentId: string | undefined;
      let reindex = false;

      if (parts.length === 2 && parts[1] === "reindex") {
        documentId = parts[0];
        reindex    = true;
      } else if (parts.length === 2 && parts[1] === "generate") {
        documentId = parts[0];
      } else if (parts.length === 1) {
        documentId = parts[0];
      } else {
        const body  = await req.json().catch(() => ({}));
        documentId  = (body as { document_id?: string }).document_id;
        reindex     = (body as { reindex?: boolean }).reindex ?? false;
      }

      if (!documentId) return err("document_id is required");

      const result = await runEmbeddingPipeline(supabase, documentId, reindex);
      const status = await getEmbeddingStatus(supabase, documentId);

      return ok({
        document_id: documentId,
        ...result,
        ...status,
      });
    }

    return err("Method not allowed", 405);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Internal error";
    return err(msg, 500);
  }
});
