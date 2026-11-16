import { NextResponse } from "next/server";

/**
 * Liveness endpoint for the deploy (spec point 08 / ISC-41). Public — the platform's
 * health check hits it with no cookie, so `proxy` allow-lists `/api/health`. The base
 * 200 stays unconditional (liveness — a cold DB never makes the platform refuse to
 * start); `sha` + `warehouse` make the response PROVE which build is serving and that
 * the warehouse actually reads (Cato 2026-07-04: a bare {ok} proves almost nothing).
 */
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  let warehouse: "ok" | "unavailable" = "unavailable";
  try {
    const { schemaSnapshot } = await import("@/engine/warehouse");
    warehouse = schemaSnapshot().length > 0 ? "ok" : "unavailable";
  } catch {
    warehouse = "unavailable";
  }
  return NextResponse.json({
    status: "ok",
    sha: process.env.RAILWAY_GIT_COMMIT_SHA?.slice(0, 7) ?? null,
    warehouse,
  });
}
