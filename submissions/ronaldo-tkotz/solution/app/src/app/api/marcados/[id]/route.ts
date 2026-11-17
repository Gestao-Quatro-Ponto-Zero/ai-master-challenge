import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { arquivoMarcado, removerMarcado, nomeArquivo } from "@/engine/marcados";
import { gravando } from "@/engine/estado";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));
type Ctx = { params: Promise<{ id: string }> };

/** The marked chart as a file: ?formato=png (default) or svg; ?baixar=1 downloads it. */
export async function GET(req: Request, { params }: Ctx): Promise<Response> {
  try {
    const user = await requireUser();
    const id = Number((await params).id);
    if (!Number.isInteger(id)) return Response.json({ error: "id inválido" }, { status: 400 });
    const arq = arquivoMarcado(user.id, id);
    if (!arq) return Response.json({ error: "gráfico não encontrado" }, { status: 404 });
    const url = new URL(req.url);
    const svg = url.searchParams.get("formato") === "svg";
    const corpo = svg ? Buffer.from(arq.svg, "utf8") : Buffer.from(arq.png.slice(arq.png.indexOf(",") + 1), "base64");
    const headers: Record<string, string> = {
      "Content-Type": svg ? "image/svg+xml" : "image/png",
      "Content-Length": String(corpo.byteLength),
      "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
      "Cache-Control": "private, no-cache",
    };
    if (url.searchParams.get("baixar")) headers["Content-Disposition"] = `attachment; filename="${nomeArquivo(arq.titulo)}.${svg ? "svg" : "png"}"`;
    return new Response(new Uint8Array(corpo), { headers });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}

async function DELETE_(_req: Request, { params }: Ctx): Promise<Response> {
  try {
    const user = await requireUser();
    const id = Number((await params).id);
    if (!Number.isInteger(id)) return Response.json({ error: "id inválido" }, { status: 400 });
    return Response.json({ ok: removerMarcado(user.id, id) });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}

// Deploy (D46.4): the remote state is saved before the response.
export const DELETE = gravando(DELETE_);
