import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

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

const CHUNK_TOKEN_LIMIT  = 500;
const CHUNK_OVERLAP_TOKENS = 50;
const CHARS_PER_TOKEN    = 4.2;
const CHUNK_CHAR_LIMIT   = Math.round(CHUNK_TOKEN_LIMIT  * CHARS_PER_TOKEN); // ~2100
const OVERLAP_CHARS      = Math.round(CHUNK_OVERLAP_TOKENS * CHARS_PER_TOKEN); // ~210

function estimateTokens(text: string): number {
  const words = text.split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(words * 1.3));
}

function cleanContent(raw: string): string {
  return raw
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'")
    .replace(/&[a-z]+;/gi, " ")
    .replace(/\r\n/g, "\n").replace(/\r/g, "\n")
    .replace(/\t/g, " ")
    .replace(/[ \t]{2,}/g, " ")
    .replace(/\n{4,}/g, "\n\n\n")
    .replace(/^ +/gm, "").replace(/ +$/gm, "")
    .replace(/^(={3,}|-{3,})$/gm, "")
    .trim();
}

interface Section { title: string; content: string; }

function parseSections(text: string): Section[] {
  const lines    = text.split("\n");
  const sections: Section[] = [];
  let currentTitle   = "";
  let currentLines: string[] = [];

  function flush() {
    const body = currentLines.join("\n").trim();
    if (body.length > 0) {
      sections.push({ title: currentTitle, content: body });
    }
    currentLines = [];
  }

  const HEADING = /^(#{1,6})\s+(.+)$/;

  for (const line of lines) {
    const m = HEADING.exec(line);
    if (m) {
      flush();
      currentTitle = m[2].trim();
    } else {
      currentLines.push(line);
    }
  }
  flush();

  if (sections.length === 0 && text.trim().length > 0) {
    sections.push({ title: "", content: text.trim() });
  }

  return sections;
}

interface Chunk {
  chunkIndex:   number;
  chunkText:    string;
  tokenCount:   number;
  sectionTitle: string;
  strategy:     string;
}

function splitBySentences(text: string): string[] {
  return text
    .replace(/([.!?])\s+/g, "$1\n")
    .split("\n")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

function buildOverlapPrefix(chunks: Chunk[]): string {
  if (chunks.length === 0) return "";
  const prev = chunks[chunks.length - 1].chunkText;
  if (prev.length <= OVERLAP_CHARS) return prev + " ";
  const words = prev.split(" ");
  let result = "";
  for (let i = words.length - 1; i >= 0 && result.length < OVERLAP_CHARS; i--) {
    result = words[i] + " " + result;
  }
  return result.trimStart() + " ";
}

function chunkSection(section: Section, startIndex: number, documentChunks: Chunk[]): Chunk[] {
  const chunks: Chunk[] = [];
  const text = section.content;

  if (text.length <= CHUNK_CHAR_LIMIT) {
    chunks.push({
      chunkIndex:   startIndex,
      chunkText:    text,
      tokenCount:   estimateTokens(text),
      sectionTitle: section.title,
      strategy:     "section_based",
    });
    return chunks;
  }

  const sentences = splitBySentences(text);
  let current     = buildOverlapPrefix(documentChunks);
  let idx         = startIndex;

  for (const sentence of sentences) {
    if (current.length + sentence.length + 1 > CHUNK_CHAR_LIMIT && current.trim().length > 0) {
      const finalText = current.trim();
      chunks.push({
        chunkIndex:   idx++,
        chunkText:    finalText,
        tokenCount:   estimateTokens(finalText),
        sectionTitle: section.title,
        strategy:     "hybrid",
      });
      const words = current.split(" ");
      let overlap = "";
      for (let i = words.length - 1; i >= 0 && overlap.length < OVERLAP_CHARS; i--) {
        overlap = words[i] + " " + overlap;
      }
      current = overlap.trimStart() + sentence + " ";
    } else {
      current += (current.trim() ? " " : "") + sentence;
    }
  }

  if (current.trim().length > 0) {
    const finalText = current.trim();
    chunks.push({
      chunkIndex:   idx,
      chunkText:    finalText,
      tokenCount:   estimateTokens(finalText),
      sectionTitle: section.title,
      strategy:     "hybrid",
    });
  }

  return chunks;
}

function generateChunks(sections: Section[]): Chunk[] {
  const allChunks: Chunk[] = [];
  for (const section of sections) {
    const newChunks = chunkSection(section, allChunks.length, allChunks);
    allChunks.push(...newChunks);
  }
  return allChunks;
}

const STOP_WORDS = new Set([
  "a","an","the","and","or","but","in","on","at","to","for","of","with",
  "by","from","up","down","is","are","was","were","be","been","being",
  "have","has","had","do","does","did","will","would","can","could",
  "should","may","might","it","its","this","that","these","those","i",
  "you","he","she","we","they","them","their","our","your","his","her",
  "as","if","not","no","so","such","than","then","when","where","which",
  "who","how","what","all","any","each","more","most","also","into",
  "about","after","before","between","through",
]);

function extractKeywords(text: string, limit = 8): string[] {
  const freq: Record<string, number> = {};
  const words = text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((w) => w.length >= 4 && !STOP_WORDS.has(w));
  for (const w of words) freq[w] = (freq[w] ?? 0) + 1;
  return Object.entries(freq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([w]) => w);
}

function extractMetadata(
  chunk: Chunk,
  documentTitle: string,
): Record<string, unknown> {
  const keywords = extractKeywords(chunk.chunkText);
  return {
    document_title: documentTitle,
    section:        chunk.sectionTitle || null,
    keywords,
    strategy:       chunk.strategy,
    token_count:    chunk.tokenCount,
  };
}

async function storeChunks(
  supabase: ReturnType<typeof createClient>,
  documentId: string,
  versionId:  string | null,
  chunks:     Chunk[],
  documentTitle: string,
) {
  await supabase.from("knowledge_chunks").delete().eq("document_id", documentId);

  const rows = chunks.map((c) => ({
    document_id:   documentId,
    version_id:    versionId ?? null,
    chunk_index:   c.chunkIndex,
    chunk_text:    c.chunkText,
    token_count:   c.tokenCount,
    section_title: c.sectionTitle,
    metadata:      extractMetadata(c, documentTitle),
  }));

  if (rows.length > 0) {
    const { error } = await supabase.from("knowledge_chunks").insert(rows);
    if (error) throw new Error(error.message);
  }

  await supabase.from("knowledge_documents")
    .update({
      chunk_count:       chunks.length,
      processing_status: "processed",
      status:            "ready",
    })
    .eq("id", documentId);

  return rows.length;
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  const url    = new URL(req.url);
  const parts  = url.pathname.replace(/^\/document-process\/?/, "").split("/").filter(Boolean);
  const method = req.method;

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
  );

  try {
    if (method === "GET" && parts.length === 2 && parts[1] === "chunks") {
      const documentId = parts[0];
      const { data, error } = await supabase
        .from("knowledge_chunks")
        .select("id, chunk_index, chunk_text, token_count, section_title, metadata, created_at")
        .eq("document_id", documentId)
        .order("chunk_index", { ascending: true });
      if (error) return err(error.message, 500);
      return ok({ chunks: data ?? [], count: (data ?? []).length });
    }

    if (method === "POST" && (parts.length === 0 || (parts.length === 1 && parts[0] !== ""))) {
      let documentId: string;
      let versionId:  string | null = null;

      if (parts.length === 1) {
        documentId = parts[0];
      } else {
        const body = await req.json();
        documentId = body.document_id;
        versionId  = body.version_id ?? null;
      }

      if (!documentId) return err("document_id is required");

      const { data: doc, error: docErr } = await supabase
        .from("knowledge_documents")
        .select("id, title, content")
        .eq("id", documentId)
        .maybeSingle();

      if (docErr)  return err(docErr.message, 500);
      if (!doc)    return err("Document not found", 404);

      if (!versionId) {
        const { data: ver } = await supabase
          .from("knowledge_versions")
          .select("id")
          .eq("document_id", documentId)
          .eq("is_current", true)
          .maybeSingle();
        versionId = ver?.id ?? null;
      }

      await supabase.from("knowledge_documents")
        .update({ processing_status: "processing" })
        .eq("id", documentId);

      try {
        const cleaned  = cleanContent(doc.content);
        const sections = parseSections(cleaned);
        const chunks   = generateChunks(sections);
        const count    = await storeChunks(supabase, documentId, versionId, chunks, doc.title);

        return ok({
          document_id:   documentId,
          chunk_count:   count,
          section_count: sections.length,
          total_tokens:  chunks.reduce((s, c) => s + c.tokenCount, 0),
          strategy:      chunks.some((c) => c.strategy === "hybrid") ? "hybrid" : "section_based",
        });
      } catch (e) {
        await supabase.from("knowledge_documents")
          .update({ processing_status: "error" })
          .eq("id", documentId);
        throw e;
      }
    }

    return err("Not found", 404);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Internal error";
    return err(msg, 500);
  }
});
