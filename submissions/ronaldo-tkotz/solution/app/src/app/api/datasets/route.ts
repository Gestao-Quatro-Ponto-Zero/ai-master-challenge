import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { listDatasets, activeDatasetId, registerUpload, setActiveDataset, MAX_UPLOAD_BYTES } from "@/engine/datasets";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));

export async function GET(): Promise<Response> {
  try {
    const user = await requireUser();
    return Response.json({ datasets: listDatasets(user.id), activeId: activeDatasetId(user.id) });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}

export async function POST(req: Request): Promise<Response> {
  try {
    const user = await requireUser();
    const form = await req.formData().catch(() => null);
    const file = form?.get("file");
    if (!(file instanceof File)) return Response.json({ error: "Attach a .sqlite file in the `file` field." }, { status: 400 });
    if (file.size > MAX_UPLOAD_BYTES) return Response.json({ error: `Too large — the limit is ${Math.round(MAX_UPLOAD_BYTES / 1024 / 1024)} MB.` }, { status: 413 });
    const result = registerUpload(user.id, file.name || "upload.sqlite", Buffer.from(await file.arrayBuffer()));
    if (!result.ok || !result.dataset) return Response.json({ error: result.error ?? "Upload failed." }, { status: 400 });
    const dataset = form?.get("activate") === "1" ? setActiveDataset(user.id, result.dataset.id) : result.dataset;
    return Response.json({ dataset, activeId: activeDatasetId(user.id) }, { status: 201 });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}
