import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { montarDeck } from "@/engine/deckMarcados";
import { gravando } from "@/engine/estado";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 120;

/** Builds the Minto presentation from the marked charts (D45), steered by the brief, the audience and the analyst context the user picked (D46.3). */
async function POST_(req: Request): Promise<Response> {
  try {
    const user = await requireUser();
    const body = (await req.json().catch(() => ({}))) as { briefing?: unknown; publico?: unknown; conversas?: unknown; telas?: unknown };
    const briefing = typeof body.briefing === "string" ? body.briefing : null;
    const publico = typeof body.publico === "string" ? body.publico : null;
    const ids = (v: unknown) => (Array.isArray(v) ? v.filter((x): x is string => typeof x === "string").slice(0, 8) : []);
    // D46.3: the conversations and screens the user picked as context (ownership checked in the engine).
    const deck = await montarDeck(user.id, { briefing, publico, conversaIds: ids(body.conversas), telaIds: ids(body.telas) });
    return Response.json({ deck }, { status: 201 });
  } catch (e) {
    return authErrorResponse(e) ?? Response.json({ error: e instanceof Error ? e.message : String(e) }, { status: 400 });
  }
}

// Deploy (D46.4): the remote state is saved before the response.
export const POST = gravando(POST_);
