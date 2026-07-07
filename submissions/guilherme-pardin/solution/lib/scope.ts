import {
  agents,
  analytics,
  closedDeals,
  deals,
  managers,
  meta,
} from "./data";
import type {
  AgentProfile,
  Analytics,
  ClosedDeal,
  DatasetMeta,
  ManagerSummary,
  RevenueBucket,
  ScoredDeal,
  SectorLossPattern,
  SectorLossRate,
  WorstAgentBySector,
} from "./types";
import type { AuthUser } from "./hooks/useAuth";

const MIN_SAMPLES_FOR_SECTOR = 10;

// -----------------------------
// Team resolution
// -----------------------------

export function agentsForUser(user: AuthUser): AgentProfile[] {
  if (user.role === "gestor") return agents;
  if (user.role === "manager")
    return agents.filter((a) => a.manager === user.name);
  return agents.filter((a) => a.name === user.name);
}

export function agentNamesForUser(user: AuthUser): Set<string> {
  return new Set(agentsForUser(user).map((a) => a.name));
}

// -----------------------------
// Deal scoping
// -----------------------------

export function scopedOpenDeals(user: AuthUser): ScoredDeal[] {
  if (user.role === "gestor") return deals;
  const team = agentNamesForUser(user);
  return deals.filter((d) => team.has(d.currentAgent));
}

export function scopedClosedDeals(user: AuthUser): ClosedDeal[] {
  if (user.role === "gestor") return closedDeals;
  const team = agentNamesForUser(user);
  return closedDeals.filter((d) => team.has(d.agent));
}

// Deals recommended TO a specific person (only relevant for seller)
export function dealsRecommendedForUser(user: AuthUser): ScoredDeal[] {
  if (user.role !== "seller") return [];
  return deals.filter(
    (d) => d.optimalAgent === user.name && d.currentAgent !== user.name,
  );
}

// -----------------------------
// Manager summaries (for gestor)
// -----------------------------

export function scopedManagers(user: AuthUser): ManagerSummary[] {
  if (user.role === "gestor") return managers;
  if (user.role === "manager")
    return managers.filter((m) => m.manager === user.name);
  return [];
}

// -----------------------------
// Meta (recomputed for team scope)
// -----------------------------

export function scopedMeta(user: AuthUser): DatasetMeta {
  if (user.role === "gestor") return meta;
  const open = scopedOpenDeals(user);
  const reallocated = open.filter((d) => d.isReallocated).length;
  return {
    ...meta,
    totalOpenDeals: open.length,
    totalPipelineValue: open.reduce((s, d) => s + d.price, 0),
    reallocatedCount: reallocated,
  };
}

// -----------------------------
// Analytics (recomputed for manager scope, global for gestor)
// -----------------------------

function topN<T>(
  items: T[],
  keyFn: (d: T) => string,
  valueFn: (d: T) => number,
  n = 8,
): RevenueBucket[] {
  const m = new Map<string, { revenue: number; deals: number }>();
  for (const d of items) {
    const k = keyFn(d);
    const cur = m.get(k) ?? { revenue: 0, deals: 0 };
    cur.revenue += valueFn(d);
    cur.deals += 1;
    m.set(k, cur);
  }
  return Array.from(m.entries())
    .map(([key, v]) => ({
      key,
      revenue: v.revenue,
      deals: v.deals,
      avgTicket: v.deals ? v.revenue / v.deals : 0,
    }))
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, n);
}

export function scopedAnalytics(user: AuthUser): Analytics {
  if (user.role === "gestor") return analytics;
  const closed = scopedClosedDeals(user);
  const won = closed.filter((d) => d.stage === "Won");
  const lost = closed.filter((d) => d.stage === "Lost");

  const conversion: Analytics["conversion"] = {
    topSectorsByRevenue: topN(won, (d) => d.sector, (d) => d.closeValue),
    topProductsByRevenue: topN(won, (d) => d.product, (d) => d.closeValue),
    topAgentsByRevenue: topN(won, (d) => d.agent, (d) => d.closeValue, 10),
    avgTicketBySector: topN(won, (d) => d.sector, (d) => d.closeValue, 20).map(
      (b) => ({ sector: b.key, avgTicket: b.avgTicket }),
    ),
    avgTicketByProduct: topN(
      won,
      (d) => d.product,
      (d) => d.closeValue,
      20,
    ).map((b) => ({ product: b.key, avgTicket: b.avgTicket })),
    totalWonRevenue: won.reduce((s, d) => s + d.closeValue, 0),
    wonDealCount: won.length,
  };

  // Sector loss rates (scoped to team)
  const sectorClosedMap = new Map<
    string,
    { won: number; lost: number; lostValue: number }
  >();
  for (const d of closed) {
    const cur = sectorClosedMap.get(d.sector) ?? {
      won: 0,
      lost: 0,
      lostValue: 0,
    };
    if (d.stage === "Won") cur.won += 1;
    else {
      cur.lost += 1;
      cur.lostValue += d.price;
    }
    sectorClosedMap.set(d.sector, cur);
  }
  const sectorsByLossRate: SectorLossRate[] = Array.from(
    sectorClosedMap.entries(),
  )
    .map(([sector, v]) => {
      const total = v.won + v.lost;
      return {
        sector,
        lossRate: total ? v.lost / total : 0,
        totalClosed: total,
        lostDeals: v.lost,
        lostValue: v.lostValue,
      };
    })
    .filter((s) => s.totalClosed >= 15)
    .sort((a, b) => b.lossRate - a.lossRate);

  // Sector × product patterns
  const sectorProductLossMap = new Map<
    string,
    { lostDeals: number; lostValue: number }
  >();
  const sectorTotalLosses = new Map<string, number>();
  for (const d of lost) {
    const k = `${d.sector}||${d.product}`;
    const cur = sectorProductLossMap.get(k) ?? { lostDeals: 0, lostValue: 0 };
    cur.lostDeals += 1;
    cur.lostValue += d.price;
    sectorProductLossMap.set(k, cur);
    sectorTotalLosses.set(
      d.sector,
      (sectorTotalLosses.get(d.sector) ?? 0) + 1,
    );
  }
  const sectorProductPatterns: SectorLossPattern[] = Array.from(
    sectorProductLossMap.entries(),
  )
    .map(([k, v]) => {
      const [sector, product] = k.split("||");
      const total = sectorTotalLosses.get(sector) ?? 1;
      return {
        sector,
        product,
        lostDeals: v.lostDeals,
        lostValue: v.lostValue,
        shareOfSectorLosses: v.lostDeals / total,
      };
    })
    .filter((p) => p.lostDeals >= 5)
    .sort((a, b) => b.lostDeals - a.lostDeals)
    .slice(0, 10);

  // Worst agent per sector — within team
  const teamAgents = agentNamesForUser(user);
  const teamAgentSectorStats = new Map<
    string,
    { won: number; total: number }
  >();
  const teamBestBySector = new Map<
    string,
    { agent: string; wr: number; deals: number }
  >();
  for (const d of closed) {
    if (!teamAgents.has(d.agent)) continue;
    const k = `${d.agent}||${d.sector}`;
    const cur = teamAgentSectorStats.get(k) ?? { won: 0, total: 0 };
    cur.total += 1;
    if (d.stage === "Won") cur.won += 1;
    teamAgentSectorStats.set(k, cur);
  }
  for (const [k, v] of teamAgentSectorStats) {
    if (v.total < MIN_SAMPLES_FOR_SECTOR) continue;
    const [agent, sector] = k.split("||");
    const wr = v.won / v.total;
    const cur = teamBestBySector.get(sector);
    if (!cur || wr > cur.wr)
      teamBestBySector.set(sector, { agent, wr, deals: v.total });
  }

  const worstAgentBySector: WorstAgentBySector[] = [];
  for (const s of sectorsByLossRate.slice(0, 6)) {
    let worst: { agent: string; wr: number; deals: number } | null = null;
    for (const [k, v] of teamAgentSectorStats) {
      const [agent, sector] = k.split("||");
      if (sector !== s.sector) continue;
      if (v.total < MIN_SAMPLES_FOR_SECTOR) continue;
      const wr = v.won / v.total;
      if (!worst || wr < worst.wr) worst = { agent, wr, deals: v.total };
    }
    const best = teamBestBySector.get(s.sector);
    if (worst && best && worst.agent !== best.agent) {
      worstAgentBySector.push({
        sector: s.sector,
        worstAgent: worst.agent,
        worstWr: worst.wr,
        worstDeals: worst.deals,
        bestAgent: best.agent,
        bestWr: best.wr,
        bestDeals: best.deals,
        deltaPP: best.wr - worst.wr,
      });
    }
  }

  const actionableInsights: string[] = [];
  for (const s of sectorsByLossRate.slice(0, 4)) {
    const topPattern = sectorProductPatterns
      .filter((p) => p.sector === s.sector)
      .sort((a, b) => b.shareOfSectorLosses - a.shareOfSectorLosses)[0];
    const replacement = worstAgentBySector.find(
      (w) => w.sector === s.sector,
    );
    const parts: string[] = [];
    parts.push(
      `O setor ${s.sector} perde ${(s.lossRate * 100).toFixed(0)}% dos deals (${s.lostDeals} de ${s.totalClosed}).`,
    );
    if (topPattern) {
      parts.push(
        `${(topPattern.shareOfSectorLosses * 100).toFixed(0)}% das perdas estão em ${topPattern.product}.`,
      );
    }
    if (replacement && replacement.deltaPP >= 0.15) {
      parts.push(
        `${replacement.worstAgent} tem WR ${(replacement.worstWr * 100).toFixed(0)}% nesse setor — redirecione para ${replacement.bestAgent} (WR ${(replacement.bestWr * 100).toFixed(0)}%).`,
      );
    }
    actionableInsights.push(parts.join(" "));
  }

  return {
    conversion,
    losses: {
      sectorsByLossRate,
      sectorProductPatterns,
      worstAgentBySector,
      actionableInsights,
      totalLostRevenue: lost.reduce((s, d) => s + d.price, 0),
      lostDealCount: lost.length,
    },
  };
}

// -----------------------------
// Manager rankings (only for gestor dashboard)
// -----------------------------

export interface ManagerRanking {
  manager: string;
  agents: number;
  avgTeamWr: number;
  totalRevenue: number;
  hotDeals: number;
  openDeals: number;
  reallocations: number;
  region: string;
}

// -----------------------------
// Sector & product performance (scoped by role)
// -----------------------------

export interface SectorPerformancePoint {
  sector: string;
  wonRevenue: number;
  conversionRate: number;
  wonDeals: number;
  totalClosed: number;
  bestManager?: string;
  bestManagerWr?: number;
}

export interface ProductPerformancePoint {
  product: string;
  wonRevenue: number;
  conversionRate: number;
  wonDeals: number;
  totalClosed: number;
}

export function sectorPerformance(
  user: AuthUser,
  minSamples = 20,
): SectorPerformancePoint[] {
  const closed = scopedClosedDeals(user);
  const map = new Map<
    string,
    { won: number; lost: number; wonRevenue: number }
  >();
  for (const d of closed) {
    const cur = map.get(d.sector) ?? { won: 0, lost: 0, wonRevenue: 0 };
    if (d.stage === "Won") {
      cur.won += 1;
      cur.wonRevenue += d.closeValue;
    } else {
      cur.lost += 1;
    }
    map.set(d.sector, cur);
  }
  const result: SectorPerformancePoint[] = Array.from(map.entries())
    .map(([sector, v]) => {
      const total = v.won + v.lost;
      return {
        sector,
        wonRevenue: v.wonRevenue,
        conversionRate: total ? v.won / total : 0,
        wonDeals: v.won,
        totalClosed: total,
      };
    })
    .filter((s) => s.totalClosed >= minSamples)
    .sort((a, b) => b.wonRevenue - a.wonRevenue);

  if (user.role === "gestor") {
    const bestMgr = bestManagerBySectorMap();
    for (const row of result) {
      const b = bestMgr.get(row.sector);
      if (b) {
        row.bestManager = b.manager;
        row.bestManagerWr = b.wr;
      }
    }
  }

  return result;
}

export function productPerformance(
  user: AuthUser,
  minSamples = 20,
): ProductPerformancePoint[] {
  const closed = scopedClosedDeals(user);
  const map = new Map<
    string,
    { won: number; lost: number; wonRevenue: number }
  >();
  for (const d of closed) {
    const cur = map.get(d.product) ?? { won: 0, lost: 0, wonRevenue: 0 };
    if (d.stage === "Won") {
      cur.won += 1;
      cur.wonRevenue += d.closeValue;
    } else {
      cur.lost += 1;
    }
    map.set(d.product, cur);
  }
  return Array.from(map.entries())
    .map(([product, v]) => {
      const total = v.won + v.lost;
      return {
        product,
        wonRevenue: v.wonRevenue,
        conversionRate: total ? v.won / total : 0,
        wonDeals: v.won,
        totalClosed: total,
      };
    })
    .filter((p) => p.totalClosed >= minSamples)
    .sort((a, b) => b.wonRevenue - a.wonRevenue);
}

function bestManagerBySectorMap(): Map<
  string,
  { manager: string; wr: number; deals: number }
> {
  const perManagerSector = new Map<
    string,
    { won: number; total: number }
  >();
  for (const d of closedDeals) {
    const k = `${d.manager}||${d.sector}`;
    const cur = perManagerSector.get(k) ?? { won: 0, total: 0 };
    cur.total += 1;
    if (d.stage === "Won") cur.won += 1;
    perManagerSector.set(k, cur);
  }
  const best = new Map<
    string,
    { manager: string; wr: number; deals: number }
  >();
  for (const [k, v] of perManagerSector) {
    if (v.total < 30) continue;
    const [manager, sector] = k.split("||");
    const wr = v.won / v.total;
    const cur = best.get(sector);
    if (!cur || wr > cur.wr) best.set(sector, { manager, wr, deals: v.total });
  }
  return best;
}

// -----------------------------
// Team-scoped best fit (for gerente recommendations)
// -----------------------------

export interface TeamBestFit {
  agent: string;
  wr: number;
  deals: number;
}

export function teamBestBySector(user: AuthUser): Map<string, TeamBestFit> {
  const teamNames = agentNamesForUser(user);
  const stats = new Map<string, { won: number; total: number }>();
  for (const d of closedDeals) {
    if (!teamNames.has(d.agent)) continue;
    const k = `${d.agent}||${d.sector}`;
    const cur = stats.get(k) ?? { won: 0, total: 0 };
    cur.total += 1;
    if (d.stage === "Won") cur.won += 1;
    stats.set(k, cur);
  }
  const best = new Map<string, TeamBestFit>();
  for (const [k, v] of stats) {
    if (v.total < MIN_SAMPLES_FOR_SECTOR) continue;
    const [agent, sector] = k.split("||");
    const wr = v.won / v.total;
    const cur = best.get(sector);
    if (!cur || wr > cur.wr) best.set(sector, { agent, wr, deals: v.total });
  }
  return best;
}

// -----------------------------
// Seller specialization map (for gerente table)
// -----------------------------

export interface SellerSpecRow {
  agent: string;
  overallWr: number;
  bestSector: string;
  bestSectorWr: number;
  offSector: number;
  openDeals: number;
}

export function sellerSpecMap(user: AuthUser): SellerSpecRow[] {
  const list = agentsForUser(user);
  return list
    .map((a) => ({
      agent: a.name,
      overallWr: a.overallWr,
      bestSector: a.bestSector,
      bestSectorWr: a.bestSectorWr,
      offSector: a.reallocatedOut,
      openDeals: a.openDeals,
    }))
    .sort((a, b) => b.offSector - a.offSector);
}

// -----------------------------
// Team reallocation plan grouped by seller (for gerente)
// -----------------------------

export interface SellerReallocPlan {
  agent: string;
  bestSector: string;
  bestSectorWr: number;
  overallWr: number;
  suggestions: {
    sector: string;
    count: number;
    value: number;
    targetAgent: string;
    targetWr: number;
    deltaPP: number;
  }[];
  totalDeals: number;
  totalValue: number;
}

export function teamReallocationPlan(user: AuthUser): SellerReallocPlan[] {
  const team = agentsForUser(user);
  const teamNames = agentNamesForUser(user);
  const teamBest = teamBestBySector(user);
  const openTeamDeals = scopedOpenDeals(user);
  const plans: SellerReallocPlan[] = [];
  for (const a of team) {
    const outside = openTeamDeals.filter(
      (d) => d.currentAgent === a.name && d.isReallocated,
    );
    if (outside.length === 0) continue;

    // Group by sector
    const bySector = new Map<
      string,
      { count: number; value: number; deals: typeof outside }
    >();
    for (const d of outside) {
      const cur = bySector.get(d.sector) ?? { count: 0, value: 0, deals: [] };
      cur.count += 1;
      cur.value += d.price;
      cur.deals.push(d);
      bySector.set(d.sector, cur);
    }

    const suggestions: SellerReallocPlan["suggestions"] = [];
    for (const [sector, info] of bySector) {
      const teamBestForSector = teamBest.get(sector);
      const inTeamBest =
        teamBestForSector && teamBestForSector.agent !== a.name
          ? teamBestForSector
          : null;
      const currentWr = a.sectors.find((s) => s.sector === sector)?.wr ?? 0;
      if (inTeamBest) {
        suggestions.push({
          sector,
          count: info.count,
          value: info.value,
          targetAgent: inTeamBest.agent,
          targetWr: inTeamBest.wr,
          deltaPP: inTeamBest.wr - currentWr,
        });
      } else {
        // Fallback: use globally-optimal from any deal in group
        const optimalGlobal = info.deals[0]?.optimalAgent;
        const optimalWr = info.deals[0]?.optimalAgentWr ?? 0;
        if (optimalGlobal && !teamNames.has(optimalGlobal)) {
          suggestions.push({
            sector,
            count: info.count,
            value: info.value,
            targetAgent: `${optimalGlobal} (fora do time)`,
            targetWr: optimalWr,
            deltaPP: optimalWr - currentWr,
          });
        }
      }
    }
    suggestions.sort((a, b) => b.value - a.value);

    plans.push({
      agent: a.name,
      bestSector: a.bestSector,
      bestSectorWr: a.bestSectorWr,
      overallWr: a.overallWr,
      suggestions,
      totalDeals: outside.length,
      totalValue: outside.reduce((s, d) => s + d.price, 0),
    });
  }
  plans.sort((a, b) => b.totalDeals - a.totalDeals);
  return plans;
}

// -----------------------------
// Seller sector-focused helpers (for vendedor page)
// -----------------------------

export function dealsInSector(user: AuthUser, sector: string) {
  if (user.role !== "seller") return [];
  return deals.filter(
    (d) => d.currentAgent === user.name && d.sector === sector,
  );
}

export function managerRankings(): ManagerRanking[] {
  const list: ManagerRanking[] = [];
  for (const m of managers) {
    const teamAgents = agents.filter((a) => a.manager === m.manager);
    const totalClosed = teamAgents.reduce((s, a) => s + a.totalClosed, 0);
    const weightedWon = teamAgents.reduce(
      (s, a) => s + a.overallWr * a.totalClosed,
      0,
    );
    const teamAgentNames = new Set(teamAgents.map((a) => a.name));
    const teamRevenue = closedDeals
      .filter((d) => d.stage === "Won" && teamAgentNames.has(d.agent))
      .reduce((s, d) => s + d.closeValue, 0);
    const regionCount = new Map<string, number>();
    for (const a of teamAgents) {
      regionCount.set(a.region, (regionCount.get(a.region) ?? 0) + 1);
    }
    const region =
      Array.from(regionCount.entries()).sort((a, b) => b[1] - a[1])[0]?.[0] ??
      "—";
    list.push({
      manager: m.manager,
      agents: m.agents,
      avgTeamWr: totalClosed ? weightedWon / totalClosed : 0,
      totalRevenue: teamRevenue,
      hotDeals: m.hotDeals,
      openDeals: m.totalDeals,
      reallocations: m.reallocations,
      region,
    });
  }
  return list.sort((a, b) => b.avgTeamWr - a.avgTeamWr);
}
