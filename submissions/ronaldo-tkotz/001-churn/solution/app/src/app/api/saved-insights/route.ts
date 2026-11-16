import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { listSavedInsights, createSavedInsight, deleteSavedInsightBySource } from "@/engine/appdb";
import { isChartType, type ChartSpec } from "@/engine/tools";
import { coerceTablePayload, coerceTransform, isPinKind, type StoredChart } from "@/engine/parts";
import { activeDatasetId } from "@/engine/datasets";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));

/** Validate an untrusted chart payload: the grounded spec plus (artifact layer)
 *  the user's displayed transform. Old clients send a flat spec — still valid. */
function coerceChart(v: unknown): StoredChart | null {
  if (!v || typeof v !== "object") return null;
  const c = v as Record<string, unknown>;
  if (!isChartType(c.type)) return null;
  if (typeof c.x !== "string" || !Array.isArray(c.y) || !Array.isArray(c.data)) return null;
  const y = c.y.filter((s): s is string => typeof s === "string");
  if (y.length === 0) return null;
  const data = c.data.filter((r): r is Record<string, unknown> => !!r && typeof r === "object").slice(0, 500);
  const spec: ChartSpec = { type: c.type, title: typeof c.title === "string" ? c.title : "", x: c.x, y, data };
  const transform = coerceTransform(c.transform);
  return transform ? { ...spec, transform } : spec;
}

export async function GET(): Promise<Response> {
  try {
    const user = await requireUser();
    return Response.json({ savedInsights: listSavedInsights(user.id) });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}

interface CreateBody {
  sourceKind?: unknown; sourceId?: unknown; conversationId?: unknown; question?: unknown;
  answer?: unknown; citedSql?: unknown; chart?: unknown; table?: unknown; title?: unknown;
}
const str = (v: unknown): string | null => (typeof v === "string" ? v : null);

export async function POST(req: Request): Promise<Response> {
  try {
    const user = await requireUser();
    const body = (await req.json().catch(() => ({}))) as CreateBody;
    const sourceKind = isPinKind(body.sourceKind) ? body.sourceKind : null;
    const sourceId = str(body.sourceId);
    if (!sourceKind || !sourceId) {
      return Response.json({ error: "sourceKind ('turn'|'finding'|'chart'|'table'|'narrative') and sourceId are required." }, { status: 400 });
    }
    const citedSql = Array.isArray(body.citedSql) ? body.citedSql.filter((s): s is string => typeof s === "string") : [];
    const chart = coerceChart(body.chart);
    const table = coerceTablePayload(body.table);
    const answer = str(body.answer);
    // Per-kind payload gate — a part pin must actually carry its part.
    if (sourceKind === "chart" && !chart) return Response.json({ error: "A 'chart' pin requires a valid chart payload." }, { status: 400 });
    if (sourceKind === "table" && !table) return Response.json({ error: "A 'table' pin requires a valid table payload (columns + rows)." }, { status: 400 });
    if (sourceKind === "narrative" && !answer) return Response.json({ error: "A 'narrative' pin requires the answer text." }, { status: 400 });
    const savedInsight = createSavedInsight({
      sourceKind, sourceId, userId: user.id, conversationId: str(body.conversationId), question: str(body.question),
      answer, citedSql, chart, table,
      datasetId: activeDatasetId(user.id), // provenance: which dataset grounded this pin (deck build gates cross-dataset)
      title: str(body.title),
    });
    return Response.json({ savedInsight }, { status: 201 });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}

interface DeleteBody { sourceKind?: unknown; sourceId?: unknown }
export async function DELETE(req: Request): Promise<Response> {
  try {
    const user = await requireUser();
    const body = (await req.json().catch(() => ({}))) as DeleteBody;
    const sourceKind = isPinKind(body.sourceKind) ? body.sourceKind : null;
    const sourceId = str(body.sourceId);
    if (!sourceKind || !sourceId) {
      return Response.json({ error: "sourceKind ('turn'|'finding'|'chart'|'table'|'narrative') and sourceId are required." }, { status: 400 });
    }
    const removed = deleteSavedInsightBySource(user.id, sourceKind, sourceId);
    return Response.json({ ok: true, removed });
  } catch (e) { return authErrorResponse(e) ?? Response.json({ error: msg(e) }, { status: 500 }); }
}
