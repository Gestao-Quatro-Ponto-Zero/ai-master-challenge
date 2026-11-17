/**
 * Panels of a screen (D46.2, ISC-43): POST {chart, sql} adds a chart made in the chat; DELETE
 * {painel} removes one. A chart's rows stay as the analyst queried them; its SQL travels with it.
 */
import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { adicionarPainel, obterTela, removerPainel } from "@/engine/telasUsuario";
import { isChartType, type ChartSpec } from "@/engine/parts";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));
type Ctx = { params: Promise<{ id: string }> };

function chartValido(c: unknown): c is ChartSpec {
  const s = c as ChartSpec;
  return !!s && isChartType(s.type) && typeof s.x === "string" && Array.isArray(s.y) && s.y.every((y) => typeof y === "string") && Array.isArray(s.data) && s.data.length > 0 && s.data.length <= 500;
}

export async function POST(req: Request, { params }: Ctx): Promise<Response> {
  try {
    const user = await requireUser();
    const { id } = await params;
    if (!obterTela(user.id, id)) return Response.json({ error: "tela não encontrada" }, { status: 404 });
    const body = (await req.json().catch(() => ({}))) as { chart?: unknown; sql?: unknown };
    if (!chartValido(body.chart)) return Response.json({ error: "gráfico inválido" }, { status: 400 });
    const sql = Array.isArray(body.sql) ? body.sql.filter((q): q is string => typeof q === "string" && q.length < 20_000).slice(0, 10) : [];
    if (JSON.stringify(body.chart).length > 500_000) return Response.json({ error: "gráfico grande demais" }, { status: 400 });
    return Response.json({ painel: adicionarPainel(user.id, id, body.chart, sql) }, { status: 201 });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}

export async function DELETE(req: Request, { params }: Ctx): Promise<Response> {
  try {
    const user = await requireUser();
    const { id } = await params;
    const body = (await req.json().catch(() => ({}))) as { painel?: unknown };
    const painel = Number(body.painel);
    if (!Number.isInteger(painel)) return Response.json({ error: "painel inválido" }, { status: 400 });
    return Response.json({ ok: removerPainel(user.id, id, painel) });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}
