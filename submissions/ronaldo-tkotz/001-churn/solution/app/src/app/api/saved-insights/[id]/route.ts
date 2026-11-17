import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { renameSavedInsight, deleteSavedInsight } from "@/engine/appdb";
import { gravando } from "@/engine/estado";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));
type Ctx = { params: Promise<{ id: string }> };
interface PatchBody { title?: unknown }

async function PATCH_(req: Request, { params }: Ctx): Promise<Response> {
  try {
    const user = await requireUser();
    const { id } = await params;
    const nid = Number(id);
    if (!Number.isInteger(nid)) return Response.json({ error: "Invalid id." }, { status: 400 });
    const body = (await req.json().catch(() => ({}))) as PatchBody;
    const title = typeof body.title === "string" ? body.title.trim() : "";
    if (!title) return Response.json({ error: "A non-empty title is required." }, { status: 400 });
    if (!renameSavedInsight(nid, user.id, title)) return Response.json({ error: "Pin not found" }, { status: 404 });
    return Response.json({ ok: true, title });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}

async function DELETE_(_req: Request, { params }: Ctx): Promise<Response> {
  try {
    const user = await requireUser();
    const { id } = await params;
    const nid = Number(id);
    if (!Number.isInteger(nid)) return Response.json({ error: "Invalid id." }, { status: 400 });
    if (!deleteSavedInsight(nid, user.id)) return Response.json({ error: "Pin not found" }, { status: 404 });
    return Response.json({ ok: true });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}

// Deploy (D46.4): the remote state is saved before the response.
export const PATCH = gravando(PATCH_);
export const DELETE = gravando(DELETE_);
