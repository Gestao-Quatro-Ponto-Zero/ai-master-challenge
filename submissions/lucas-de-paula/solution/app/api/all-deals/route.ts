/**
 * GET /api/all-deals
 * Returns ALL deals (including Won/Lost) with scores, for manager view.
 */

import { NextResponse } from "next/server";
import { loadDeals, calcAgentWinRates, loadPipeline } from "@/lib/data";
import { scoreDeals } from "@/lib/scoring";

export const dynamic = "force-dynamic";

export async function GET() {
  const [allDeals, pipeline] = await Promise.all([loadDeals(), loadPipeline()]);
  const winRates = calcAgentWinRates(pipeline);
  const scored   = scoreDeals(allDeals, winRates);
  return NextResponse.json(scored);
}
