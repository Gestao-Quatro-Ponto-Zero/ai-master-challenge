import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { appendMessage, getConversation } from "@/engine/appdb";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));
interface AppendBody { turnId?: unknown; seq?: unknown; role?: unknown; payload?: unknown }
type Ctx = { params: Promise<{ id: string }> };

export async function POST(req: Request, { params }: Ctx): Promise<Response> {
  try {
    const user = await requireUser();
    const { id } = await params;
    const body = (await req.json().catch(() => ({}))) as AppendBody;
    const turnId = typeof body.turnId === "string" ? body.turnId : "";
    const seq = typeof body.seq === "number" ? body.seq : NaN;
    const role = body.role === "user" || body.role === "assistant" ? body.role : "";
    if (!turnId || !Number.isInteger(seq) || !role || body.payload === undefined) {
      return Response.json({ error: "turnId, integer seq, role, and payload are required." }, { status: 400 });
    }
    if (!getConversation(id, user.id)) return Response.json({ error: "Conversation not found" }, { status: 404 });
    const stored = appendMessage({ conversationId: id, userId: user.id, turnId, seq, role, payload: body.payload });
    return Response.json({ ok: true, turnId: stored.turn_id, seq: stored.seq }, { status: 201 });
  } catch (e) {
    return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 });
  }
}
