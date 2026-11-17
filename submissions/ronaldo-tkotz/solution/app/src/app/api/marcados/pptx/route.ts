import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { deckAtual, deckDesatualizado, deckDoHistorico, deckParaPptx } from "@/engine/deckMarcados";
import { nomeArquivo } from "@/engine/marcados";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * The built presentation (D45) as a .pptx. The current one must be built again after the marks change;
 * ?id=N downloads an earlier build (D46.3) — slides of charts unmarked since then are left out.
 */
export async function GET(req: Request): Promise<Response> {
  try {
    const user = await requireUser();
    const idHist = Number(new URL(req.url).searchParams.get("id"));
    const historico = Number.isInteger(idHist) && idHist > 0;
    const deck = historico ? deckDoHistorico(user.id, idHist) : deckAtual(user.id);
    if (!deck) return Response.json({ error: "Monte a apresentação primeiro." }, { status: historico ? 404 : 409 });
    if (!historico && deckDesatualizado(user.id, deck)) return Response.json({ error: "Os gráficos marcados mudaram: monte a apresentação de novo." }, { status: 409 });
    const buffer = await deckParaPptx(user.id, deck);
    return new Response(new Uint8Array(buffer), {
      headers: {
        "Content-Type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "Content-Disposition": `attachment; filename="${nomeArquivo(deck.titulo)}.pptx"`,
        "Content-Length": String(buffer.byteLength),
      },
    });
  } catch (e) {
    return authErrorResponse(e) ?? Response.json({ error: e instanceof Error ? e.message : String(e) }, { status: 500 });
  }
}
