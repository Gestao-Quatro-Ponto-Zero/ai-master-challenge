/**
 * GET /api/insights
 * Computes analytical insights from historical Won/Lost data.
 */

import { NextResponse } from "next/server";
import { loadDeals } from "@/lib/data";

export const dynamic = "force-dynamic";

export async function GET() {
  const all = await loadDeals();

  const won  = all.filter((d) => d.deal_stage === "Won"  && d.engage_date && d.close_date);
  const lost = all.filter((d) => d.deal_stage === "Lost" && d.engage_date);

  // ── 1. Closing cycle ───────────────────────────────────────────────────────
  const cycleDays = won
    .map((d) => Math.round((d.close_date!.getTime() - d.engage_date!.getTime()) / (1000 * 60 * 60 * 24)))
    .filter((d) => d >= 0 && d < 1000);

  const avgCycleDays = cycleDays.length > 0
    ? Math.round(cycleDays.reduce((s, d) => s + d, 0) / cycleDays.length)
    : 0;

  const cycleBuckets = [
    { label: "0–30d",  min: 0,   max: 30   },
    { label: "31–60d", min: 31,  max: 60   },
    { label: "61–90d", min: 61,  max: 90   },
    { label: "91–120d",min: 91,  max: 120  },
    { label: "121–180d",min: 121,max: 180  },
    { label: "181d+",  min: 181, max: Infinity },
  ].map((b) => ({ label: b.label, count: cycleDays.filter((d) => d >= b.min && d <= b.max).length }));

  // ── 2. Seasonality ─────────────────────────────────────────────────────────
  const MONTHS = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"];
  const closesByMonth  = Array(12).fill(0);
  const revenueByMonth = Array(12).fill(0);

  won.forEach((d) => {
    const m = d.close_date!.getMonth();
    closesByMonth[m]++;
    revenueByMonth[m] += d.close_value || d.product_price;
  });

  const seasonality = MONTHS.map((month, i) => ({
    month, closes: closesByMonth[i], revenue: Math.round(revenueByMonth[i]),
  }));

  // ── 3. Products ────────────────────────────────────────────────────────────
  const productMap = new Map<string, { won: number; lost: number; revenue: number; price: number }>();
  won.forEach((d) => {
    if (!productMap.has(d.product)) productMap.set(d.product, { won: 0, lost: 0, revenue: 0, price: d.product_price });
    const s = productMap.get(d.product)!;
    s.won++; s.revenue += d.close_value || d.product_price;
  });
  lost.forEach((d) => {
    if (!productMap.has(d.product)) productMap.set(d.product, { won: 0, lost: 0, revenue: 0, price: d.product_price });
    productMap.get(d.product)!.lost++;
  });

  const products = Array.from(productMap.entries())
    .map(([name, s]) => ({ name, won: s.won, lost: s.lost, revenue: s.revenue, price: s.price,
      winRate: s.won + s.lost > 0 ? s.won / (s.won + s.lost) : 0 }))
    .sort((a, b) => b.revenue - a.revenue);

  const top3Products = products.slice(0, 3).map((p) => p.name);
  const productSeasonality = top3Products.map((pName) => {
    const monthly = Array(12).fill(0);
    won.filter((d) => d.product === pName).forEach((d) => { monthly[d.close_date!.getMonth()]++; });
    return { product: pName, monthly: MONTHS.map((m, i) => ({ month: m, closes: monthly[i] })) };
  });

  // ── 4. Agents ──────────────────────────────────────────────────────────────
  const agentMap = new Map<string, { won: number; lost: number }>();
  [...won, ...lost].forEach((d) => {
    if (!agentMap.has(d.sales_agent)) agentMap.set(d.sales_agent, { won: 0, lost: 0 });
    if (d.deal_stage === "Won") agentMap.get(d.sales_agent)!.won++;
    else agentMap.get(d.sales_agent)!.lost++;
  });

  const topAgents = Array.from(agentMap.entries())
    .map(([name, s]) => ({ name, won: s.won, lost: s.lost, total: s.won + s.lost,
      winRate: s.won + s.lost > 0 ? s.won / (s.won + s.lost) : 0 }))
    .filter((a) => a.total >= 10)
    .sort((a, b) => b.winRate - a.winRate)
    .slice(0, 10);

  // ── 5. Regions ─────────────────────────────────────────────────────────────
  const regionMap = new Map<string, { won: number; lost: number; revenue: number }>();
  [...won, ...lost].forEach((d) => {
    const r = d.regional_office || "Unknown";
    if (!regionMap.has(r)) regionMap.set(r, { won: 0, lost: 0, revenue: 0 });
    const s = regionMap.get(r)!;
    if (d.deal_stage === "Won") { s.won++; s.revenue += d.close_value || d.product_price; }
    else s.lost++;
  });

  const regions = Array.from(regionMap.entries())
    .map(([name, s]) => ({ name, won: s.won, lost: s.lost, total: s.won + s.lost,
      revenue: Math.round(s.revenue), winRate: s.won + s.lost > 0 ? s.won / (s.won + s.lost) : 0 }))
    .sort((a, b) => b.revenue - a.revenue);

  const regionSeasonality = regions.map(({ name }) => {
    const monthly = Array(12).fill(0);
    won.filter((d) => (d.regional_office || "Unknown") === name).forEach((d) => { monthly[d.close_date!.getMonth()]++; });
    return { region: name, monthly: MONTHS.map((m, i) => ({ month: m, closes: monthly[i] })) };
  });

  // ── 6. Sectors ─────────────────────────────────────────────────────────────
  const sectorMap = new Map<string, { won: number; lost: number; revenue: number }>();
  [...won, ...lost].forEach((d) => {
    const s = (d.account_sector || "—").trim();
    if (!sectorMap.has(s)) sectorMap.set(s, { won: 0, lost: 0, revenue: 0 });
    const st = sectorMap.get(s)!;
    if (d.deal_stage === "Won") { st.won++; st.revenue += d.close_value || d.product_price; }
    else st.lost++;
  });

  const sectors = Array.from(sectorMap.entries())
    .map(([name, s]) => ({ name, won: s.won, lost: s.lost, total: s.won + s.lost,
      revenue: Math.round(s.revenue), winRate: s.won + s.lost > 0 ? s.won / (s.won + s.lost) : 0 }))
    .filter((s) => s.total >= 5)
    .sort((a, b) => b.total - a.total);

  // ── 7. Countries ───────────────────────────────────────────────────────────
  const countryMap = new Map<string, { won: number; lost: number; revenue: number }>();
  [...won, ...lost].forEach((d) => {
    const c = (d.account_country || "—").trim();
    if (!countryMap.has(c)) countryMap.set(c, { won: 0, lost: 0, revenue: 0 });
    const ct = countryMap.get(c)!;
    if (d.deal_stage === "Won") { ct.won++; ct.revenue += d.close_value || d.product_price; }
    else ct.lost++;
  });

  const countries = Array.from(countryMap.entries())
    .map(([name, s]) => ({ name, won: s.won, lost: s.lost, total: s.won + s.lost,
      revenue: Math.round(s.revenue), winRate: s.won + s.lost > 0 ? s.won / (s.won + s.lost) : 0 }))
    .sort((a, b) => b.total - a.total).slice(0, 12);

  // ── 8. Correlations ────────────────────────────────────────────────────────
  const empBrackets = [
    { label: "<100",    min: 0,    max: 99      },
    { label: "100–499", min: 100,  max: 499     },
    { label: "500–999", min: 500,  max: 999     },
    { label: "1k–4.9k", min: 1000, max: 4999   },
    { label: "5k+",     min: 5000, max: Infinity },
  ];
  const empCorrelation = empBrackets.map((b) => {
    const matches = [...won, ...lost].filter((d) => d.account_employees >= b.min && d.account_employees <= b.max);
    const w = matches.filter((d) => d.deal_stage === "Won").length;
    const l = matches.filter((d) => d.deal_stage === "Lost").length;
    return { label: b.label, won: w, lost: l, total: w + l, winRate: w + l > 0 ? w / (w + l) : 0 };
  });

  const subWon   = won.filter((d) =>  d.account_has_parent).length;
  const subLost  = lost.filter((d) => d.account_has_parent).length;
  const noSubWon = won.filter((d) =>  !d.account_has_parent).length;
  const noSubLost= lost.filter((d) => !d.account_has_parent).length;
  const subsidiaryCorrelation = [
    { label: "Com subsidiária", won: subWon,   lost: subLost,  total: subWon + subLost,   winRate: subWon + subLost > 0   ? subWon   / (subWon + subLost)   : 0 },
    { label: "Sem subsidiária", won: noSubWon, lost: noSubLost,total: noSubWon + noSubLost,winRate: noSubWon + noSubLost > 0? noSubWon / (noSubWon + noSubLost): 0 },
  ];

  return NextResponse.json({
    avgCycleDays, totalWon: won.length, totalLost: lost.length,
    cycleBuckets, seasonality, products, productSeasonality,
    topAgents, regions, regionSeasonality, sectors, countries,
    empCorrelation, subsidiaryCorrelation,
  });
}
