import fs from "node:fs";
import path from "node:path";
import Papa from "papaparse";
import type {
  AgentProfile,
  Analytics,
  ClosedDeal,
  DatasetMeta,
  DealStage,
  ManagerSummary,
  RevenueBucket,
  ScoredDeal,
  SectorLossPattern,
  SectorLossRate,
  SectorPerformance,
  Tier,
  WorstAgentBySector,
} from "../lib/types";

const DATA_DIR = path.join(process.cwd(), "data");
const OUT_DIR = path.join(process.cwd(), "lib/data");

const MIN_SAMPLES_FOR_SECTOR = 10;
const MIN_SAMPLES_FOR_PRODUCT = 10;

const SECTOR_PT: Record<string, string> = {
  software: "software",
  technology: "tecnologia",
  technolgy: "tecnologia",
  retail: "varejo",
  medical: "saúde",
  finance: "financeiro",
  marketing: "marketing",
  entertainment: "entretenimento",
  telecommunications: "telecomunicações",
  services: "serviços",
  employment: "recursos humanos",
};

function translateSector(en: string | undefined): string {
  if (!en) return "Desconhecido";
  return SECTOR_PT[en.toLowerCase()] ?? en;
}

type PipelineRow = {
  opportunity_id: string;
  sales_agent: string;
  product: string;
  account: string;
  deal_stage: string;
  engage_date: string;
  close_date: string;
  close_value: string;
};

type AccountRow = {
  account: string;
  sector: string;
  year_established: string;
  revenue: string;
  employees: string;
  office_location: string;
  subsidiary_of: string;
};

type ProductRow = {
  product: string;
  series: string;
  sales_price: string;
};

type TeamRow = {
  sales_agent: string;
  manager: string;
  regional_office: string;
};

function readCsv<T>(name: string): T[] {
  const raw = fs.readFileSync(path.join(DATA_DIR, name), "utf-8");
  const parsed = Papa.parse<T>(raw, {
    header: true,
    skipEmptyLines: true,
    transform: (v) => v.trim(),
  });
  return parsed.data;
}

function percentile(sortedValues: number[], p: number): number {
  if (sortedValues.length === 0) return 0;
  const idx = (p / 100) * (sortedValues.length - 1);
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  if (lo === hi) return sortedValues[lo];
  return sortedValues[lo] + (sortedValues[hi] - sortedValues[lo]) * (idx - lo);
}

function main() {
  const pipeline = readCsv<PipelineRow>("sales_pipeline.csv");
  const accounts = readCsv<AccountRow>("accounts.csv");
  const products = readCsv<ProductRow>("products.csv");
  const teams = readCsv<TeamRow>("sales_teams.csv");

  // --- Fix pipeline product typo: "GTXPro" -> "GTX Pro"
  for (const row of pipeline) {
    if (row.product === "GTXPro") row.product = "GTX Pro";
  }

  // --- Index lookups
  const accountsByName = new Map<string, AccountRow>();
  for (const a of accounts) accountsByName.set(a.account, a);

  const productsByName = new Map<string, ProductRow>();
  for (const p of products) productsByName.set(p.product, p);

  const teamsByAgent = new Map<string, TeamRow>();
  for (const t of teams) teamsByAgent.set(t.sales_agent, t);

  const maxPrice = Math.max(
    ...products.map((p) => Number(p.sales_price) || 0),
  );

  // --- Split closed vs open
  const closed = pipeline.filter(
    (r) => r.deal_stage === "Won" || r.deal_stage === "Lost",
  );
  const open = pipeline.filter(
    (r) => r.deal_stage === "Engaging" || r.deal_stage === "Prospecting",
  );

  // --- Historic aggregates (from closed only)
  type WinCount = { won: number; total: number };
  const add = (map: Map<string, WinCount>, key: string, won: boolean) => {
    const cur = map.get(key) ?? { won: 0, total: 0 };
    cur.total += 1;
    if (won) cur.won += 1;
    map.set(key, cur);
  };
  const wr = (m: Map<string, WinCount>, k: string, min = 0): number | null => {
    const c = m.get(k);
    if (!c || c.total < min) return null;
    return c.won / c.total;
  };

  const agentSectorStats = new Map<string, WinCount>();
  const agentProductStats = new Map<string, WinCount>();
  const agentStats = new Map<string, WinCount>();
  const productStats = new Map<string, WinCount>();
  const monthStats = new Map<string, WinCount>();
  const overallStats: WinCount = { won: 0, total: 0 };

  for (const row of closed) {
    const won = row.deal_stage === "Won";
    const acct = accountsByName.get(row.account);
    const sector = translateSector(acct?.sector);
    const agent = row.sales_agent;

    add(agentSectorStats, `${agent}||${sector}`, won);
    add(agentProductStats, `${agent}||${row.product}`, won);
    add(agentStats, agent, won);
    add(productStats, row.product, won);

    if (row.engage_date) {
      const month = row.engage_date.slice(5, 7);
      add(monthStats, month, won);
    }

    overallStats.total += 1;
    if (won) overallStats.won += 1;
  }

  const overallWr = overallStats.total
    ? overallStats.won / overallStats.total
    : 0;

  // --- Best-sector-per-agent (only sectors with >=10 samples)
  const agentBestSector = new Map<string, SectorPerformance>();
  const agentSectorsList = new Map<string, SectorPerformance[]>();
  const agents = new Set<string>();
  for (const t of teams) agents.add(t.sales_agent);

  for (const agent of agents) {
    const list: SectorPerformance[] = [];
    for (const [key, count] of agentSectorStats) {
      const [a, sector] = key.split("||");
      if (a !== agent) continue;
      if (count.total < MIN_SAMPLES_FOR_SECTOR) continue;
      list.push({ sector, wr: count.won / count.total, deals: count.total });
    }
    list.sort((a, b) => b.wr - a.wr);
    agentSectorsList.set(agent, list);
    if (list.length > 0) agentBestSector.set(agent, list[0]);
  }

  // --- Best agent per sector (highest WR with >=10 samples in that sector)
  const bestAgentPerSector = new Map<
    string,
    { agent: string; wr: number; deals: number }
  >();
  for (const [key, count] of agentSectorStats) {
    if (count.total < MIN_SAMPLES_FOR_SECTOR) continue;
    const [agent, sector] = key.split("||");
    const w = count.won / count.total;
    const cur = bestAgentPerSector.get(sector);
    if (!cur || w > cur.wr) {
      bestAgentPerSector.set(sector, { agent, wr: w, deals: count.total });
    }
  }

  // --- Score each open deal
  const scoredRaw: Array<Omit<ScoredDeal, "tier">> = [];

  for (const row of open) {
    const stage = row.deal_stage as DealStage;
    const acct = accountsByName.get(row.account);
    const prod = productsByName.get(row.product);
    const team = teamsByAgent.get(row.sales_agent);

    const account = row.account ? row.account : "Não identificado";
    const sector = translateSector(acct?.sector);
    const price = prod ? Number(prod.sales_price) || 0 : 0;
    const currentAgent = row.sales_agent;
    const manager = team?.manager ?? "N/A";
    const region = team?.regional_office ?? "N/A";

    // 1) Stage 0-25
    const stageScore = stage === "Engaging" ? 25 : 10;

    // 2) Agent fit 0-25 (WR cascade: agent×sector -> agent×product -> agent overall)
    const currentAgentSectorWr =
      wr(agentSectorStats, `${currentAgent}||${sector}`, MIN_SAMPLES_FOR_SECTOR) ??
      null;
    const currentAgentProductWr =
      wr(
        agentProductStats,
        `${currentAgent}||${row.product}`,
        MIN_SAMPLES_FOR_PRODUCT,
      ) ?? null;
    const currentAgentOverallWr = wr(agentStats, currentAgent) ?? overallWr;

    const currentAgentWr =
      currentAgentSectorWr ?? currentAgentProductWr ?? currentAgentOverallWr;
    const agentFitScore = Math.round(currentAgentWr * 25);

    // 3) Deal value 0-20
    const dealValueScore = maxPrice
      ? Math.round((price / maxPrice) * 20)
      : 0;

    // 4) Product WR 0-15
    const productWr = wr(productStats, row.product) ?? overallWr;
    const productWrScore = Math.round(productWr * 15);

    // 5) Account quality 0-10
    let accountQualityScore = 1;
    if (acct) {
      const revenue = Number(acct.revenue) || 0;
      const employees = Number(acct.employees) || 0;
      if (revenue > 5000 || employees > 10000) accountQualityScore = 10;
      else if (revenue > 1000 || employees > 1000) accountQualityScore = 7;
      else accountQualityScore = 4;
    }

    // 6) Seasonality 0-5
    let seasonalityScore = 3; // neutral fallback for missing engage_date
    let engageDate: string | null = null;
    let daysSinceEngage: number | null = null;
    if (row.engage_date) {
      engageDate = row.engage_date;
      const month = row.engage_date.slice(5, 7);
      const monthWr = wr(monthStats, month) ?? overallWr;
      seasonalityScore = Math.round(monthWr * 5);
      const t = new Date(row.engage_date).getTime();
      if (!Number.isNaN(t)) {
        // Reference date: max close_date in closed deals (dataset "today")
        // Computed once outside; here we just leave engageDate & derive later
      }
    }

    const score =
      stageScore +
      agentFitScore +
      dealValueScore +
      productWrScore +
      accountQualityScore +
      seasonalityScore;

    // Optimal agent: best agent for this sector (min 10 deals)
    const bestForSector = bestAgentPerSector.get(sector);
    const optimalAgent = bestForSector?.agent ?? currentAgent;
    const optimalAgentWr = bestForSector?.wr ?? currentAgentWr;

    const best = agentBestSector.get(currentAgent);
    const bestSector = best?.sector ?? "—";
    const bestSectorWr = best?.wr ?? currentAgentOverallWr;

    scoredRaw.push({
      id: row.opportunity_id,
      account,
      sector,
      product: row.product,
      price,
      stage,
      currentAgent,
      optimalAgent,
      manager,
      region,
      score,
      breakdown: {
        stage: stageScore,
        agentFit: agentFitScore,
        dealValue: dealValueScore,
        productWr: productWrScore,
        accountQuality: accountQualityScore,
        seasonality: seasonalityScore,
      },
      currentAgentWr,
      optimalAgentWr,
      isReallocated: optimalAgent !== currentAgent,
      bestSector,
      bestSectorWr,
      engageDate,
      daysSinceEngage: null,
    });
  }

  // Reference "today" = max close_date in closed deals
  const closeDates = closed
    .map((r) => (r.close_date ? new Date(r.close_date).getTime() : NaN))
    .filter((n) => !Number.isNaN(n));
  const refTs = closeDates.length ? Math.max(...closeDates) : Date.now();

  for (const d of scoredRaw) {
    if (d.engageDate) {
      const t = new Date(d.engageDate).getTime();
      if (!Number.isNaN(t)) {
        d.daysSinceEngage = Math.max(
          0,
          Math.round((refTs - t) / (1000 * 60 * 60 * 24)),
        );
      }
    }
  }

  // --- Tier classification by percentile
  const scores = scoredRaw.map((d) => d.score).sort((a, b) => a - b);
  const p85 = percentile(scores, 85);
  const p50 = percentile(scores, 50);
  const p15 = percentile(scores, 15);

  function classify(score: number): Tier {
    if (score >= p85) return "hot";
    if (score >= p50) return "warm";
    if (score >= p15) return "cold";
    return "at_risk";
  }

  const scored: ScoredDeal[] = scoredRaw.map((d) => ({
    ...d,
    tier: classify(d.score),
  }));

  // --- Agent profiles
  const agentProfiles: AgentProfile[] = [];
  for (const t of teams) {
    const name = t.sales_agent;
    const stats = agentStats.get(name);
    const overall = stats && stats.total > 0 ? stats.won / stats.total : 0;
    const my = scored.filter((d) => d.currentAgent === name);
    const pipeVal = my.reduce((s, d) => s + d.price, 0);
    const sectors = agentSectorsList.get(name) ?? [];
    const best = agentBestSector.get(name);
    agentProfiles.push({
      name,
      manager: t.manager,
      region: t.regional_office,
      overallWr: overall,
      totalClosed: stats?.total ?? 0,
      openDeals: my.length,
      hotDeals: my.filter((d) => d.tier === "hot").length,
      warmDeals: my.filter((d) => d.tier === "warm").length,
      coldDeals: my.filter((d) => d.tier === "cold").length,
      atRiskDeals: my.filter((d) => d.tier === "at_risk").length,
      pipelineValue: pipeVal,
      sectors,
      bestSector: best?.sector ?? "—",
      bestSectorWr: best?.wr ?? 0,
      reallocatedIn: scored.filter((d) => d.optimalAgent === name && d.isReallocated).length,
      reallocatedOut: my.filter((d) => d.isReallocated).length,
    });
  }
  agentProfiles.sort((a, b) => b.overallWr - a.overallWr);

  // --- Manager summaries
  const managerMap = new Map<string, ManagerSummary>();
  for (const p of agentProfiles) {
    const cur = managerMap.get(p.manager) ?? {
      manager: p.manager,
      agents: 0,
      totalDeals: 0,
      hotDeals: 0,
      reallocations: 0,
      pipelineValue: 0,
    };
    cur.agents += 1;
    cur.totalDeals += p.openDeals;
    cur.hotDeals += p.hotDeals;
    cur.reallocations += p.reallocatedOut;
    cur.pipelineValue += p.pipelineValue;
    managerMap.set(p.manager, cur);
  }
  const managers = Array.from(managerMap.values()).sort(
    (a, b) => b.totalDeals - a.totalDeals,
  );

  // --- Closed deals (enriched)
  const closedDeals: ClosedDeal[] = closed.map((r) => {
    const acct = accountsByName.get(r.account);
    const prod = productsByName.get(r.product);
    const team = teamsByAgent.get(r.sales_agent);
    const closeValue = Number(r.close_value) || 0;
    const price = prod ? Number(prod.sales_price) || 0 : 0;
    let daysToClose: number | null = null;
    if (r.engage_date && r.close_date) {
      const t1 = new Date(r.engage_date).getTime();
      const t2 = new Date(r.close_date).getTime();
      if (!Number.isNaN(t1) && !Number.isNaN(t2)) {
        daysToClose = Math.max(
          0,
          Math.round((t2 - t1) / (1000 * 60 * 60 * 24)),
        );
      }
    }
    return {
      id: r.opportunity_id,
      account: r.account || "Não identificado",
      sector: translateSector(acct?.sector),
      product: r.product,
      price,
      stage: r.deal_stage as "Won" | "Lost",
      agent: r.sales_agent,
      manager: team?.manager ?? "N/A",
      region: team?.regional_office ?? "N/A",
      closeValue,
      engageDate: r.engage_date || null,
      closeDate: r.close_date || null,
      daysToClose,
    };
  });

  // --- Analytics: Conversion (Won only)
  const won = closedDeals.filter((d) => d.stage === "Won");
  const lost = closedDeals.filter((d) => d.stage === "Lost");

  function topN(
    items: ClosedDeal[],
    keyFn: (d: ClosedDeal) => string,
    n = 8,
  ): RevenueBucket[] {
    const m = new Map<string, { revenue: number; deals: number }>();
    for (const d of items) {
      const k = keyFn(d);
      const cur = m.get(k) ?? { revenue: 0, deals: 0 };
      cur.revenue += d.closeValue;
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

  const conversion: Analytics["conversion"] = {
    topSectorsByRevenue: topN(won, (d) => d.sector),
    topProductsByRevenue: topN(won, (d) => d.product),
    topAgentsByRevenue: topN(won, (d) => d.agent, 10),
    avgTicketBySector: topN(won, (d) => d.sector, 20).map((b) => ({
      sector: b.key,
      avgTicket: b.avgTicket,
    })),
    avgTicketByProduct: topN(won, (d) => d.product, 20).map((b) => ({
      product: b.key,
      avgTicket: b.avgTicket,
    })),
    totalWonRevenue: won.reduce((s, d) => s + d.closeValue, 0),
    wonDealCount: won.length,
  };

  // --- Analytics: Losses
  // Sector loss rate: lost / (won + lost)
  const sectorClosedMap = new Map<
    string,
    { won: number; lost: number; wonValue: number; lostValue: number }
  >();
  for (const d of closedDeals) {
    const cur = sectorClosedMap.get(d.sector) ?? {
      won: 0,
      lost: 0,
      wonValue: 0,
      lostValue: 0,
    };
    if (d.stage === "Won") {
      cur.won += 1;
      cur.wonValue += d.closeValue;
    } else {
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
    .filter((s) => s.totalClosed >= 30)
    .sort((a, b) => b.lossRate - a.lossRate);

  // Sector×product loss patterns (top overall)
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
    .filter((p) => p.lostDeals >= 20)
    .sort((a, b) => b.lostDeals - a.lostDeals)
    .slice(0, 10);

  // Worst agent per sector (with best replacement)
  const worstAgentBySector: WorstAgentBySector[] = [];
  const worstSet = new Set<string>();
  for (const s of sectorsByLossRate.slice(0, 6)) {
    let worst: { agent: string; wr: number; deals: number } | null = null;
    for (const [key, count] of agentSectorStats) {
      const [agent, sector] = key.split("||");
      if (sector !== s.sector) continue;
      if (count.total < MIN_SAMPLES_FOR_SECTOR) continue;
      const w = count.won / count.total;
      if (!worst || w < worst.wr) {
        worst = { agent, wr: w, deals: count.total };
      }
    }
    const best = bestAgentPerSector.get(s.sector);
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
      worstSet.add(`${worst.agent}||${s.sector}`);
    }
  }

  // Actionable insights
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

  const analytics: Analytics = {
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

  // --- Meta
  const reallocatedCount = scored.filter((d) => d.isReallocated).length;
  const totalPipelineValue = scored.reduce((s, d) => s + d.price, 0);
  const stageCounts = {
    Prospecting: open.filter((r) => r.deal_stage === "Prospecting").length,
    Engaging: open.filter((r) => r.deal_stage === "Engaging").length,
    Won: won.length,
    Lost: lost.length,
  };
  const meta: DatasetMeta = {
    totalOpenDeals: scored.length,
    totalClosedDeals: closed.length,
    overallWinRate: overallWr,
    maxProductPrice: maxPrice,
    tierThresholds: { p85, p50, p15 },
    totalPipelineValue,
    reallocatedCount,
    stageCounts,
    generatedAt: new Date().toISOString(),
  };

  // --- Write
  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.writeFileSync(
    path.join(OUT_DIR, "scored-deals.json"),
    JSON.stringify(scored),
  );
  fs.writeFileSync(
    path.join(OUT_DIR, "closed-deals.json"),
    JSON.stringify(closedDeals),
  );
  fs.writeFileSync(
    path.join(OUT_DIR, "team-data.json"),
    JSON.stringify({ agents: agentProfiles, managers }),
  );
  fs.writeFileSync(
    path.join(OUT_DIR, "analytics.json"),
    JSON.stringify(analytics),
  );
  fs.writeFileSync(path.join(OUT_DIR, "meta.json"), JSON.stringify(meta));

  // --- Report
  const tierCount = (t: Tier) => scored.filter((d) => d.tier === t).length;
  console.log("=== Preparação concluída ===");
  console.log(`Deals abertos: ${scored.length}`);
  console.log(`Deals fechados analisados: ${closed.length}`);
  console.log(`WR geral: ${(overallWr * 100).toFixed(1)}%`);
  console.log(`Limiares: P85=${p85.toFixed(1)}  P50=${p50.toFixed(1)}  P15=${p15.toFixed(1)}`);
  console.log(
    `Tiers: hot=${tierCount("hot")}  warm=${tierCount("warm")}  cold=${tierCount("cold")}  at_risk=${tierCount("at_risk")}`,
  );
  console.log(`Deals com realocação sugerida: ${reallocatedCount} (${((reallocatedCount / scored.length) * 100).toFixed(1)}%)`);
  console.log(`Valor total do pipeline aberto: US$ ${totalPipelineValue.toLocaleString()}`);
  console.log(`Vendedores: ${agentProfiles.length}  Managers: ${managers.length}`);
  console.log(`Won: ${won.length} ($${conversion.totalWonRevenue.toLocaleString()})  Lost: ${lost.length} ($${analytics.losses.totalLostRevenue.toLocaleString()})`);
  console.log(`Setor com pior conversão: ${sectorsByLossRate[0]?.sector ?? "n/a"} (${sectorsByLossRate[0] ? (sectorsByLossRate[0].lossRate * 100).toFixed(0) + "%" : "n/a"} de perda)`);
  console.log(`Insights acionáveis: ${actionableInsights.length}`);
  console.log(`Arquivos gerados em ${OUT_DIR}`);
}

main();
