/** One screen (D46.2): GET with its requests and panels, PATCH {nome}, DELETE. */
import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { apagarTela, listarPaineis, listarPedidos, obterTela, renomearTela } from "@/engine/telasUsuario";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));
type Ctx = { params: Promise<{ id: string }> };

export async function GET(_req: Request, { params }: Ctx): Promise<Response> {
  try {
    const user = await requireUser();
    const { id } = await params;
    const tela = obterTela(user.id, id);
    if (!tela) return Response.json({ error: "tela não encontrada" }, { status: 404 });
    return Response.json({ tela, pedidos: listarPedidos(user.id, id), paineis: listarPaineis(user.id, id) });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}

export async function PATCH(req: Request, { params }: Ctx): Promise<Response> {
  try {
    const user = await requireUser();
    const { id } = await params;
    const body = (await req.json().catch(() => ({}))) as { nome?: unknown };
    if (typeof body.nome !== "string" || !renomearTela(user.id, id, body.nome)) return Response.json({ error: "nome inválido ou tela não encontrada" }, { status: 400 });
    return Response.json({ ok: true });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}

export async function DELETE(_req: Request, { params }: Ctx): Promise<Response> {
  try {
    const user = await requireUser();
    const { id } = await params;
    return Response.json({ ok: apagarTela(user.id, id) });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}
