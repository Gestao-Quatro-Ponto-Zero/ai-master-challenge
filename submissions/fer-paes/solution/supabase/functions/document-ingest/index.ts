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

function err(message: string, status = 400) {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

type DocFormat = "text" | "html" | "markdown" | "json";

function detectFormat(filename: string, content: string): DocFormat {
  const ext = filename.split(".").pop()?.toLowerCase() ?? "";
  if (ext === "html" || ext === "htm") return "html";
  if (ext === "md" || ext === "markdown") return "markdown";
  if (ext === "json") return "json";
  if (content.trimStart().startsWith("<")) return "html";
  if (/^#{1,6} /m.test(content)) return "markdown";
  try { JSON.parse(content); return "json"; } catch { /* not json */ }
  return "text";
}

function extractTitleFromHtml(html: string): string {
  const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);
  const h1Match    = html.match(/<h1[^>]*>([^<]*)<\/h1>/i);
  return (titleMatch?.[1] ?? h1Match?.[1] ?? "").trim().replace(/\s+/g, " ");
}

function extractTextFromHtml(html: string): string {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<nav[\s\S]*?<\/nav>/gi, "")
    .replace(/<header[\s\S]*?<\/header>/gi, "")
    .replace(/<footer[\s\S]*?<\/footer>/gi, "")
    .replace(/<aside[\s\S]*?<\/aside>/gi, "")
    .replace(/<noscript[\s\S]*?<\/noscript>/gi, "")
    .replace(/<\/?(p|div|h[1-6]|li|br|tr|td|th|blockquote|section|article)[^>]*>/gi, "\n")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&[a-z]+;/gi, " ");
}

function extractTextFromMarkdown(md: string): string {
  return md
    .replace(/```[\s\S]*?```/g, (m) => m.replace(/```[^\n]*\n?/, "").replace(/\n?```$/, ""))
    .replace(/`([^`]+)`/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/__([^_]+)__/g, "$1")
    .replace(/_([^_]+)_/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, "$1")
    .replace(/^[-*+]\s+/gm, "")
    .replace(/^\d+\.\s+/gm, "")
    .replace(/^>\s*/gm, "")
    .replace(/^\|.*\|$/gm, "")
    .replace(/^---+$/gm, "")
    .replace(/^===+$/gm, "");
}

function extractTextFromJson(json: string): string {
  try {
    const obj = JSON.parse(json);
    function flatten(val: unknown, depth = 0): string {
      if (depth > 5) return "";
      if (typeof val === "string") return val;
      if (typeof val === "number" || typeof val === "boolean") return String(val);
      if (Array.isArray(val)) return val.map((v) => flatten(v, depth + 1)).join("\n");
      if (val && typeof val === "object") {
        return Object.values(val as Record<string, unknown>)
          .map((v) => flatten(v, depth + 1))
          .join("\n");
      }
      return "";
    }
    return flatten(obj);
  } catch {
    return json;
  }
}

function normalizeContent(raw: string): string {
  return raw
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .replace(/\t/g, " ")
    .replace(/[ \t]{2,}/g, " ")
    .replace(/\n{4,}/g, "\n\n\n")
    .replace(/^ +/gm, "")
    .replace(/ +$/gm, "")
    .trim();
}

function extractContent(content: string, format: DocFormat): { text: string; suggestedTitle: string } {
  switch (format) {
    case "html": {
      const suggestedTitle = extractTitleFromHtml(content);
      const text = normalizeContent(extractTextFromHtml(content));
      return { text, suggestedTitle };
    }
    case "markdown": {
      const firstH1 = content.match(/^#{1}\s+(.+)/m)?.[1]?.trim() ?? "";
      const text = normalizeContent(extractTextFromMarkdown(content));
      return { text, suggestedTitle: firstH1 };
    }
    case "json": {
      const text = normalizeContent(extractTextFromJson(content));
      return { text, suggestedTitle: "" };
    }
    default: {
      return { text: normalizeContent(content), suggestedTitle: "" };
    }
  }
}

async function fetchUrl(url: string): Promise<{ html: string; finalUrl: string }> {
  const res = await fetch(url, {
    headers: {
      "User-Agent": "Mozilla/5.0 (compatible; KnowledgeBot/1.0)",
      "Accept": "text/html,application/xhtml+xml,*/*",
    },
    redirect: "follow",
  });
  if (!res.ok) throw new Error(`Failed to fetch URL: ${res.status} ${res.statusText}`);
  const html = await res.text();
  return { html, finalUrl: res.url };
}

async function storeDocument(
  supabase: ReturnType<typeof createClient>,
  params: {
    title: string;
    content: string;
    source?: string;
    source_id?: string;
    category_id?: string;
    document_type?: string;
    tag_ids?: string[];
    user_id?: string;
    format: DocFormat;
  }
) {
  const { data: doc, error: docErr } = await supabase
    .from("knowledge_documents")
    .insert({
      title:          params.title || "Untitled Document",
      content:        params.content,
      source:         params.source ?? "",
      source_id:      params.source_id ?? null,
      category_id:    params.category_id ?? null,
      document_type:  params.document_type ?? "article",
      publish_status: "draft",
      created_by:     params.user_id ?? null,
      version_count:  1,
    })
    .select()
    .single();

  if (docErr) throw new Error(docErr.message);

  await supabase.from("knowledge_versions").insert({
    document_id:    doc.id,
    version_number: 1,
    content:        params.content,
    change_summary: `Ingested via ${params.format} pipeline`,
    created_by:     params.user_id ?? null,
    is_current:     true,
  });

  if (params.tag_ids?.length) {
    await supabase.from("knowledge_document_tags").insert(
      params.tag_ids.map((tid: string) => ({ document_id: doc.id, tag_id: tid }))
    );
  }

  return doc;
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  const url    = new URL(req.url);
  const path   = url.pathname.replace(/^\/document-ingest/, "");
  const method = req.method;

  if (method !== "POST") return err("Method not allowed", 405);

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  const authHeader = req.headers.get("Authorization") ?? "";
  const token = authHeader.replace("Bearer ", "");
  let userId: string | undefined;

  if (token) {
    const { data: userData } = await supabase.auth.getUser(token);
    userId = userData?.user?.id;
  }

  try {
    if (path === "" || path === "/") {
      const body = await req.json();
      const { title, content, format = "text", source_id, category_id, document_type, tag_ids, source } = body;

      if (!content?.trim()) return err("content is required");
      if (!title?.trim())   return err("title is required");

      const fmt = (format as DocFormat) in { text: 1, html: 1, markdown: 1, json: 1 }
        ? (format as DocFormat) : "text";
      const { text } = extractContent(content, fmt);

      const doc = await storeDocument(supabase, {
        title, content: text, source, source_id, category_id, document_type, tag_ids, user_id: userId, format: fmt,
      });

      return ok({ document_id: doc.id, title: doc.title, char_count: text.length, format: fmt });
    }

    if (path === "/url") {
      const body = await req.json();
      const { url: targetUrl, title: providedTitle, source_id, category_id, document_type, tag_ids } = body;

      if (!targetUrl) return err("url is required");

      let parsedUrl: URL;
      try { parsedUrl = new URL(targetUrl); } catch { return err("Invalid URL"); }
      if (!["http:", "https:"].includes(parsedUrl.protocol)) return err("Only http/https URLs allowed");

      const { html, finalUrl } = await fetchUrl(targetUrl);
      const { text, suggestedTitle } = extractContent(html, "html");

      if (!text || text.length < 50) return err("Could not extract meaningful content from the URL");

      const title = providedTitle || suggestedTitle || parsedUrl.hostname + parsedUrl.pathname;

      const doc = await storeDocument(supabase, {
        title, content: text, source: finalUrl, source_id, category_id, document_type, tag_ids, user_id: userId, format: "html",
      });

      return ok({
        document_id:    doc.id,
        title:          doc.title,
        char_count:     text.length,
        source_url:     finalUrl,
        format:         "html",
        suggested_title: suggestedTitle,
      });
    }

    if (path === "/file") {
      const body = await req.json();
      const { filename, content_base64, title: providedTitle, source_id, category_id, document_type, tag_ids, source } = body;

      if (!filename)       return err("filename is required");
      if (!content_base64) return err("content_base64 is required");

      let rawContent: string;
      try {
        const bytes = Uint8Array.from(atob(content_base64), (c) => c.charCodeAt(0));
        rawContent  = new TextDecoder("utf-8", { fatal: false }).decode(bytes);
      } catch { return err("Failed to decode file content"); }

      const fmt    = detectFormat(filename, rawContent);
      const { text, suggestedTitle } = extractContent(rawContent, fmt);

      if (!text || text.length < 10) return err("Could not extract content from file");

      const title = providedTitle || suggestedTitle || filename.replace(/\.[^.]+$/, "");

      const doc = await storeDocument(supabase, {
        title, content: text, source, source_id, category_id, document_type, tag_ids, user_id: userId, format: fmt,
      });

      return ok({
        document_id: doc.id,
        title:       doc.title,
        char_count:  text.length,
        format:      fmt,
        filename,
      });
    }

    return err("Not found", 404);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Internal error";
    return err(msg, 500);
  }
});
