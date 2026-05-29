import { NextRequest } from "next/server";
import { fail, ok } from "@/lib/api";
import { isAdmin, getDemoUser } from "@/lib/auth";
import { createSupabaseAdminClient } from "@/lib/supabase/admin";
import { embedText } from "@/lib/vector-search";

async function extractText(file: File): Promise<string> {
  const buffer = Buffer.from(await file.arrayBuffer());
  const name = file.name.toLowerCase();

  if (name.endsWith(".txt") || name.endsWith(".md")) {
    return buffer.toString("utf-8");
  }

  if (name.endsWith(".pdf")) {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const pdfParse = require("pdf-parse") as (buf: Buffer) => Promise<{ text: string }>;
    const result = await pdfParse(buffer);
    return result.text;
  }

  if (name.endsWith(".docx") || name.endsWith(".doc")) {
    const mammoth = await import("mammoth");
    const result = await mammoth.extractRawText({ buffer });
    return result.value;
  }

  throw new Error(`Tipo de arquivo não suportado: ${file.name}`);
}

function splitIntoArticles(text: string): Array<{ description: string; resolution: string }> {
  const normalized = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");

  // Try to detect explicit sections: lines like "## Title" or "PERGUNTA/QUESTION/PROBLEMA" etc.
  const sectionPattern = /\n(?=#{1,3}\s|\*{2}[A-Z]|\bPERGUNTA\b|\bQUESTÃO\b|\bPROBLEMA\b|\bISSUE\b|\bQ[:\.])/gi;
  const sections = normalized.split(sectionPattern).filter((s) => s.trim().length > 50);

  if (sections.length >= 2) {
    return sections.map((section) => {
      const lines = section.trim().split("\n");
      const title = lines[0].replace(/^#+\s*/, "").replace(/\*+/g, "").trim();
      const body = lines.slice(1).join("\n").trim();
      const mid = Math.floor(body.length / 2);
      const splitAt = body.indexOf("\n", mid);
      const cut = splitAt > 0 ? splitAt : mid;
      return {
        description: `${title}\n${body.slice(0, cut)}`.trim(),
        resolution: body.slice(cut).trim() || body,
      };
    });
  }

  // Fall back: split by double newlines into paragraphs and pair them
  const paras = normalized.split(/\n{2,}/).map((p) => p.trim()).filter((p) => p.length > 30);
  if (paras.length === 0) return [{ description: normalized.slice(0, 500), resolution: normalized.slice(500) || normalized }];

  // Group paragraphs into pairs: description + resolution
  const articles: Array<{ description: string; resolution: string }> = [];
  for (let i = 0; i < paras.length; i += 2) {
    articles.push({
      description: paras[i],
      resolution: paras[i + 1] ?? paras[i],
    });
  }
  return articles;
}

export async function POST(request: NextRequest) {
  const user = getDemoUser(request);
  if (!user || !isAdmin(user)) return fail("Acesso negado", 403);

  const formData = await request.formData().catch(() => null);
  if (!formData) return fail("FormData inválido", 400);

  const file = formData.get("file") as File | null;
  if (!file) return fail("Campo 'file' obrigatório", 400);

  const category = (formData.get("category") as string) ?? "Other";
  const priority = (formData.get("priority") as string) ?? "medium";
  const channel = (formData.get("channel") as string) ?? "Web";

  const supabase = createSupabaseAdminClient();
  if (!supabase) return fail("Supabase indisponível", 503);

  let rawText: string;
  try {
    rawText = await extractText(file);
  } catch (err) {
    return fail(err instanceof Error ? err.message : "Erro ao extrair texto", 422);
  }

  if (!rawText.trim()) return fail("Arquivo sem conteúdo de texto", 422);

  const articles = splitIntoArticles(rawText);
  const inserted: unknown[] = [];
  const errors: string[] = [];

  for (const article of articles) {
    if (!article.description.trim() || !article.resolution.trim()) continue;
    try {
      const embedding = await embedText(`${article.description}\n${article.resolution}`);
      const { data, error } = await supabase
        .from("support_tickets_kb")
        .insert({
          description: article.description.slice(0, 1000),
          resolution: article.resolution.slice(0, 2000),
          category,
          priority,
          channel,
          embedding,
        })
        .select("id, description, resolution, category, created_at")
        .single();

      if (error) errors.push(error.message);
      else inserted.push(data);
    } catch (err) {
      errors.push(err instanceof Error ? err.message : "Erro desconhecido");
    }
  }

  return ok(
    {
      inserted: inserted.length,
      articles: inserted,
      errors: errors.length > 0 ? errors : undefined,
    },
    201
  );
}
