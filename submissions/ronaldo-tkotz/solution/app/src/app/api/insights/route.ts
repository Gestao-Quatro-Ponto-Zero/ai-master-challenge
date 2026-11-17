/**
 * Insights endpoint — the discovery-driven proactive feed.
 *   GET  → the findings for the connected dataset (cached, or a fresh LLM pass if cold).
 *   POST → force a fresh discovery pass (the "Re-analyze" control).
 * better-sqlite3 + the LLM loop → node runtime, never prerendered.
 */
import { NextResponse } from "next/server";
import { detectInsights, reanalyzeInsights } from "@/engine/insights";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  try {
    return NextResponse.json({ insights: await detectInsights() });
  } catch (e) {
    return NextResponse.json({ error: e instanceof Error ? e.message : String(e) }, { status: 500 });
  }
}

export async function POST() {
  try {
    return NextResponse.json({ insights: await reanalyzeInsights() });
  } catch (e) {
    return NextResponse.json({ error: e instanceof Error ? e.message : String(e) }, { status: 500 });
  }
}
