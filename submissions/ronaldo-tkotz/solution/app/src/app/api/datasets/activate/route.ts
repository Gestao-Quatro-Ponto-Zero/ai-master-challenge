import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { setActiveDataset, activeDatasetId } from "@/engine/datasets";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));
interface Body { id?: unknown }

export async function POST(req: Request): Promise<Response> {
  try {
    const user = await requireUser();
    const body = (await req.json().catch(() => ({}))) as Body;
    const id = typeof body.id === "string" ? body.id : "";
    if (!id) return Response.json({ error: "A dataset `id` is required." }, { status: 400 });
    const dataset = setActiveDataset(user.id, id);
    return Response.json({ dataset, activeId: activeDatasetId(user.id) });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 400 }); }
}
