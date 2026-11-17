import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { removeDataset, activeDatasetId } from "@/engine/datasets";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));
type Ctx = { params: Promise<{ id: string }> };

export async function DELETE(_req: Request, { params }: Ctx): Promise<Response> {
  try {
    const user = await requireUser();
    const { id } = await params;
    const result = removeDataset(user.id, id);
    if (!result.ok) return Response.json({ error: result.error ?? "Delete failed." }, { status: result.error === "No such dataset." ? 404 : 400 });
    return Response.json({ ok: true, activeId: activeDatasetId(user.id) });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}
