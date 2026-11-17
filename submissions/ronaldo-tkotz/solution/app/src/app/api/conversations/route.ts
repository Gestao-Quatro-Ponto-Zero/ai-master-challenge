import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { listConversations, createConversation } from "@/engine/appdb";
import { gravando } from "@/engine/estado";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));

export async function GET(): Promise<Response> {
  try {
    const user = await requireUser();
    return Response.json({ conversations: listConversations(user.id) });
  } catch (e) {
    return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 });
  }
}

interface CreateBody { title?: unknown }
async function POST_(req: Request): Promise<Response> {
  try {
    const user = await requireUser();
    const body = (await req.json().catch(() => ({}))) as CreateBody;
    const title = typeof body.title === "string" && body.title.trim() ? body.title.trim() : "New conversation";
    const conversation = createConversation({ title, userId: user.id });
    return Response.json({ conversation }, { status: 201 });
  } catch (e) {
    return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 });
  }
}

// Deploy (D46.4): the remote state is saved before the response.
export const POST = gravando(POST_);
