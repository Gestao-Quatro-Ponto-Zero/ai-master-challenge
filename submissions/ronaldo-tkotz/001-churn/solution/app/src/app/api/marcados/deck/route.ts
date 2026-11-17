import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { montarDeck } from "@/engine/deckMarcados";
import { gravando } from "@/engine/estado";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 120;

/** Builds the Minto presentation from the marked charts (D45); the optional brief steers it. */
async function POST_(req: Request): Promise<Response> {
  try {
    const user = await requireUser();
    const body = (await req.json().catch(() => ({}))) as { briefing?: unknown };
    const briefing = typeof body.briefing === "string" ? body.briefing : null;
    const deck = await montarDeck(user.id, { briefing });
    return Response.json({ deck }, { status: 201 });
  } catch (e) {
    return authErrorResponse(e) ?? Response.json({ error: e instanceof Error ? e.message : String(e) }, { status: 400 });
  }
}

// Deploy (D46.4): the remote state is saved before the response.
export const POST = gravando(POST_);
