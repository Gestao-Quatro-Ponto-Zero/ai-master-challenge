import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { getStoredDeck, storeDeck } from "@/engine/deck";
import { parseDeckEditOp, applyDeckEdit } from "@/engine/deckEdit";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));
type Ctx = { params: Promise<{ id: string }> };

/**
 * PATCH /api/deck/{id} — edit a DRAFT pin-deck's prose, order, or lifecycle.
 * The op vocabulary (deckEdit.ts) can only name prose/order/publish — grounded
 * material is copied through from the stored spec, never read from the request.
 * Ownership rides the per-user deck key: a foreign (or unknown) id is a plain
 * 404, indistinguishable from "no such deck". Published/legacy decks 409.
 */
export async function PATCH(req: Request, { params }: Ctx): Promise<Response> {
  try {
    const user = await requireUser();
    const { id } = await params;
    const stored = getStoredDeck(user.id, id); // exec-review ids are never stored → 404
    if (!stored) return Response.json({ error: "Deck not found." }, { status: 404 });
    const op = parseDeckEditOp(await req.json().catch(() => null));
    if (!op) return Response.json({ error: "Unrecognized edit op." }, { status: 400 });
    const result = applyDeckEdit(stored, op);
    if (!result.ok) return Response.json({ error: result.error }, { status: result.status });
    storeDeck(user.id, result.spec);
    return Response.json({ ok: true, spec: result.spec });
  } catch (e) {
    return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 });
  }
}
