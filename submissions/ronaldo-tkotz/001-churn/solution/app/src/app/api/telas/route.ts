/** The user's own screens (D46.2): GET the list, POST {nome} creates one. */
import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { criarTela, listarTelas } from "@/engine/telasUsuario";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));

export async function GET(): Promise<Response> {
  try {
    const user = await requireUser();
    return Response.json({ telas: listarTelas(user.id) });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}

export async function POST(req: Request): Promise<Response> {
  try {
    const user = await requireUser();
    const body = (await req.json().catch(() => ({}))) as { nome?: unknown };
    if (listarTelas(user.id).length >= 50) return Response.json({ error: "limite de 50 telas" }, { status: 400 });
    return Response.json({ tela: criarTela(user.id, typeof body.nome === "string" ? body.nome : "") }, { status: 201 });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}
