/**
 * GET /api/deals
 * Returns active deals (Engaging + Prospecting) with scores, sorted by score desc.
 * Accepts query params: agent, manager, region, stage
 */

import { NextRequest, NextResponse } from "next/server";
import {
  loadDeals,
  getActiveDeals,
  calcAgentWinRates,
  loadPipeline,
} from "@/lib/data";
import { scoreDeals } from "@/lib/scoring";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const agentFilter   = searchParams.get("agent")   ?? "";
  const managerFilter = searchParams.get("manager") ?? "";
  const regionFilter  = searchParams.get("region")  ?? "";
  const stageFilter   = searchParams.get("stage")   ?? "";

  const [allDeals, pipeline] = await Promise.all([loadDeals(), loadPipeline()]);
  const winRates   = calcAgentWinRates(pipeline);
  const activeDeals = getActiveDeals(allDeals);
  const scored     = scoreDeals(activeDeals, winRates);

  let filtered = scored;
  if (agentFilter)   filtered = filtered.filter((d) => d.sales_agent.toLowerCase().includes(agentFilter.toLowerCase()));
  if (managerFilter) filtered = filtered.filter((d) => d.manager.toLowerCase().includes(managerFilter.toLowerCase()));
  if (regionFilter)  filtered = filtered.filter((d) => d.regional_office.toLowerCase().includes(regionFilter.toLowerCase()));
  if (stageFilter)   filtered = filtered.filter((d) => d.deal_stage === stageFilter);

  filtered.sort((a, b) => b.score - a.score);
  return NextResponse.json(filtered);
}
