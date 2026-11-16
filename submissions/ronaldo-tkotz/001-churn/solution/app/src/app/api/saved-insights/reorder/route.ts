import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { reorderSavedInsights } from "@/engine/appdb";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));
interface ReorderBody { ids?: unknown }

export async function POST(req: Request): Promise<Response> {
  try {
    const user = await requireUser();
    const body = (await req.json().catch(() => ({}))) as ReorderBody;
    if (!Array.isArray(body.ids)) return Response.json({ error: "ids (number[]) is required." }, { status: 400 });
    const ids = body.ids.filter((n): n is number => Number.isInteger(n));
    reorderSavedInsights(user.id, ids);
    return Response.json({ ok: true, count: ids.length });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}
