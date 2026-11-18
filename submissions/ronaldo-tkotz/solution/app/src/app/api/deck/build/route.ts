import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { listSavedInsights } from "@/engine/appdb";
import { buildDeckFromPins, storeDeck } from "@/engine/deck";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));
interface BuildBody { brief?: unknown }

export async function POST(req: Request): Promise<Response> {
  try {
    const user = await requireUser();
    const body = (await req.json().catch(() => ({}))) as BuildBody;
    const brief = typeof body.brief === "string" && body.brief.trim().length > 0 ? body.brief.trim().slice(0, 400) : undefined;
    const pins = listSavedInsights(user.id);
    if (pins.length === 0) return Response.json({ error: "The deck draft is empty — pin at least one grounded answer first." }, { status: 400 });
    const spec = await buildDeckFromPins({ pins, userId: user.id, brief }); // userId: the dataset gate drops pins grounded on another dataset
    spec.status = "draft"; // a fresh pin-deck is editable until the user publishes it
    storeDeck(user.id, spec);
    return Response.json({ id: spec.id, slides: spec.slides.length }, { status: 201 });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}
