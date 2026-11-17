import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { deleteStoredDeck } from "@/engine/deck";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));
type Ctx = { params: Promise<{ id: string }> };

export async function DELETE(_req: Request, { params }: Ctx): Promise<Response> {
  try {
    const user = await requireUser();
    const { id } = await params;
    if (!id) return Response.json({ error: "A deck id is required." }, { status: 400 });
    const removed = deleteStoredDeck(user.id, id);
    if (!removed) return Response.json({ error: "Deck not found" }, { status: 404 });
    return Response.json({ ok: true, removed });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}
