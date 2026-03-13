/**
 * GET /api/meta
 * Returns filter options: agents, managers, regions, stages
 */

import { NextResponse } from "next/server";
import {
  loadDeals,
  getActiveDeals,
  getUniqueAgents,
  getUniqueManagers,
  getUniqueRegions,
  getUniqueStages,
} from "@/lib/data";

export const dynamic = "force-dynamic";

export async function GET() {
  const allDeals    = await loadDeals();
  const activeDeals = getActiveDeals(allDeals);

  return NextResponse.json({
    agents:   getUniqueAgents(activeDeals),
    managers: getUniqueManagers(activeDeals),
    regions:  getUniqueRegions(activeDeals),
    stages:   getUniqueStages(activeDeals),
  });
}
