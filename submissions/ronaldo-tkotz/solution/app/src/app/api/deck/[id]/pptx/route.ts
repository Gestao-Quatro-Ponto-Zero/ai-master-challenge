import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { buildExecutiveReview, getStoredDeck } from "@/engine/deck";
import { deckToPptx } from "@/engine/pptx";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

export async function GET(_req: Request, { params }: Ctx) {
  try {
    const { id } = await params;
    const user = id.startsWith("exec-review") ? null : await requireUser();
    const spec = id.startsWith("exec-review") ? await buildExecutiveReview() : getStoredDeck(user!.id, id);
    if (!spec) return Response.json({ error: "Deck not found." }, { status: 404 });
    const buffer = await deckToPptx(spec);
    // Human filename from the deck title (a judge downloads several decks —
    // "revenue-concentration-health-q2-2026.pptx" beats a UUID); explicit
    // Content-Length so the browser finalizes the download deterministically.
    const slug = (spec.title || spec.id)
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 64) || spec.id;
    return new Response(new Uint8Array(buffer), {
      headers: {
        "Content-Type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "Content-Disposition": `attachment; filename="${slug}.pptx"`,
        "Content-Length": String(buffer.byteLength),
      },
    });
  } catch (e) {
    return authErrorResponse(e) ?? Response.json({ error: e instanceof Error ? e.message : String(e) }, { status: 500 });
  }
}
