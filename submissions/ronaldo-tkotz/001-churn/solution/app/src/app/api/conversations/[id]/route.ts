import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { getConversation, getMessages, renameConversation, deleteConversation } from "@/engine/appdb";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));
function safeParse(json: string): unknown { try { return JSON.parse(json); } catch { return null; } }
type Ctx = { params: Promise<{ id: string }> };

export async function GET(_req: Request, { params }: Ctx): Promise<Response> {
  try {
    const user = await requireUser();
    const { id } = await params;
    const conversation = getConversation(id, user.id);
    if (!conversation) return Response.json({ error: "Conversation not found" }, { status: 404 });
    const messages = getMessages(id, user.id).map((m) => ({ turnId: m.turn_id, seq: m.seq, role: m.role, payload: safeParse(m.payload_json) }));
    return Response.json({ conversation, messages });
  } catch (e) {
    return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 });
  }
}

interface PatchBody { title?: unknown }
export async function PATCH(req: Request, { params }: Ctx): Promise<Response> {
  try {
    const user = await requireUser();
    const { id } = await params;
    const body = (await req.json().catch(() => ({}))) as PatchBody;
    const title = typeof body.title === "string" ? body.title.trim() : "";
    if (!title) return Response.json({ error: "A non-empty title is required." }, { status: 400 });
    if (!renameConversation(id, user.id, title)) return Response.json({ error: "Conversation not found" }, { status: 404 });
    return Response.json({ ok: true, title });
  } catch (e) {
    return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 });
  }
}

export async function DELETE(_req: Request, { params }: Ctx): Promise<Response> {
  try {
    const user = await requireUser();
    const { id } = await params;
    if (!deleteConversation(id, user.id)) return Response.json({ error: "Conversation not found" }, { status: 404 });
    return Response.json({ ok: true });
  } catch (e) {
    return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 });
  }
}
