/**
 * Ask the analyst for an analysis on a screen (D46.2): POST {pedido}. The analyst (DeepSeek, the
 * same grounded agent as the chat) sees the screen's earlier requests; its charts become panels.
 */
import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { analisarNaTela } from "@/engine/telasUsuario";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 120;
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));
type Ctx = { params: Promise<{ id: string }> };

export async function POST(req: Request, { params }: Ctx): Promise<Response> {
  try {
    const user = await requireUser();
    const { id } = await params;
    const body = (await req.json().catch(() => ({}))) as { pedido?: unknown };
    if (typeof body.pedido !== "string" || !body.pedido.trim()) return Response.json({ error: "escreva o pedido" }, { status: 400 });
    if (!process.env.LLM_API_KEY) return Response.json({ error: "o analista não está configurado (falta LLM_API_KEY)" }, { status: 503 });
    return Response.json(await analisarNaTela(user.id, id, body.pedido));
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}
