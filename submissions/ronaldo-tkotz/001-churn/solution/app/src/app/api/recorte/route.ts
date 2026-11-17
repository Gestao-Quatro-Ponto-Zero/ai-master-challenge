/**
 * Drill-down (ISC-40): POST {universo, caminho, cruzar?, filtros} → the slice. Read-only; every
 * dimension comes from the engine's catalogue and every value is checked against the database.
 */
import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { lerFiltros } from "@/engine/filtros";
import { recorte, isUniverso, type Passo } from "@/engine/recorte";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: Request): Promise<Response> {
  const user = await requireUser().catch((e) => e);
  if (user instanceof Error) return authErrorResponse(user) ?? Response.json({ error: "unauthorized" }, { status: 401 });
  let body: { universo?: unknown; caminho?: unknown; cruzar?: unknown; filtros?: unknown };
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "JSON inválido" }, { status: 400 });
  }
  if (!isUniverso(body.universo)) return Response.json({ error: "universo inválido" }, { status: 400 });
  const caminho = Array.isArray(body.caminho) ? body.caminho : [];
  if (!caminho.every((p): p is Passo => !!p && typeof p.dim === "string" && typeof p.valor === "string" && p.valor.length < 300)) {
    return Response.json({ error: "caminho inválido" }, { status: 400 });
  }
  const cruzar =
    Array.isArray(body.cruzar) && body.cruzar.length === 2 && body.cruzar.every((d) => typeof d === "string") ? (body.cruzar as [string, string]) : undefined;
  const filtros = lerFiltros(Object.fromEntries(new URLSearchParams(typeof body.filtros === "string" ? body.filtros : "")));
  try {
    return Response.json(recorte(filtros, { universo: body.universo, caminho, cruzar }));
  } catch (e) {
    return Response.json({ error: e instanceof Error ? e.message : String(e) }, { status: 400 });
  }
}
