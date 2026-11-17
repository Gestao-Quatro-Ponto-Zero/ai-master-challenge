import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { listarMarcados, marcar, desmarcar, validarMarcado, ROTA_TELA_USUARIO, type NovoMarcado } from "@/engine/marcados";
import { obterTela } from "@/engine/telasUsuario";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));

/** The user's marked charts (without the images): which panels show as marked. */
export async function GET(): Promise<Response> {
  try {
    const user = await requireUser();
    return Response.json({ marcados: listarMarcados(user.id) });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}

/** Marks a chart with its faithful copy (SVG + PNG made in the browser). */
export async function POST(req: Request): Promise<Response> {
  try {
    const user = await requireUser();
    const body = (await req.json().catch(() => ({}))) as Partial<NovoMarcado>;
    const erro = validarMarcado(body);
    if (erro) return Response.json({ error: erro }, { status: 400 });
    const m = body as NovoMarcado;
    const propria = ROTA_TELA_USUARIO.exec(m.rota);
    if (propria && !obterTela(user.id, propria[1])) return Response.json({ error: "tela não encontrada" }, { status: 404 });
    const marcado = marcar(user.id, { ...m, titulo: m.titulo.trim(), nota: typeof m.nota === "string" ? m.nota : null });
    return Response.json({ marcado }, { status: 201 });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}

export async function DELETE(req: Request): Promise<Response> {
  try {
    const user = await requireUser();
    const body = (await req.json().catch(() => ({}))) as { chave?: unknown };
    if (typeof body.chave !== "string") return Response.json({ error: "chave é obrigatória" }, { status: 400 });
    return Response.json({ ok: true, removido: desmarcar(user.id, body.chave) });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}
