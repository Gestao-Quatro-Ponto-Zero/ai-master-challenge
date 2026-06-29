import type { Dataset, PipelineRow, Priority, ScoreFactor, ScoredDeal } from "./types";
import { OPEN_STAGES } from "./types";
import { buildScoringStrings, fmtUSD as i18nUSD, type Lang } from "./i18n";

const WEIGHTS = {
  stage: 0.2,
  value: 0.2,
  accountFit: 0.2,
  timing: 0.2,
  product: 0.1,
  repSignal: 0.1,
};

const fmtUSD = (n: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n || 0);

function parseDate(s?: string): number | null {
  if (!s) return null;
  const t = Date.parse(s);
  return Number.isNaN(t) ? null : t;
}

function percentileRank(sorted: number[], value: number): number {
  if (sorted.length === 0) return 0.5;
  if (sorted.length === 1) return 0.5;
  let lo = 0;
  let hi = sorted.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (sorted[mid] < value) lo = mid + 1;
    else hi = mid;
  }
  return lo / (sorted.length - 1);
}

function priorityFromScore(score: number): Priority {
  if (score >= 80) return "High";
  if (score >= 60) return "Priority";
  if (score >= 40) return "Watch";
  return "Low";
}

export function priorityRank(p: Priority): number {
  return { High: 3, Priority: 2, Watch: 1, Low: 0 }[p];
}

/** Build lookup indexes and precomputed distributions for the dataset. */
function buildContext(data: Dataset) {
  const accountBy = new Map(data.accounts.map((a) => [a.account, a]));
  const productBy = new Map(data.products.map((p) => [p.product, p]));
  const teamBy = new Map(data.salesTeams.map((t) => [t.sales_agent, t]));

  // Reference "now" = latest date in dataset (datasets are historical).
  let now = 0;
  for (const r of data.pipeline) {
    now = Math.max(now, parseDate(r.engage_date) ?? 0, parseDate(r.close_date) ?? 0);
  }
  if (!now) now = Date.now();

  // Win-rate signal from closed deals.
  const tally = (key: string) => {
    const m = new Map<string, { won: number; total: number }>();
    return {
      add: (k: string, won: boolean) => {
        const e = m.get(k) ?? { won: 0, total: 0 };
        e.total += 1;
        if (won) e.won += 1;
        m.set(k, e);
      },
      rate: (k: string, min = 3) => {
        const e = m.get(k);
        if (!e || e.total < min) return null;
        return e.won / e.total;
      },
      _: m,
    };
  };
  const agentWin = tally("agent");
  const managerWin = tally("manager");
  const regionWin = tally("region");
  let globalWon = 0;
  let globalClosed = 0;
  for (const r of data.pipeline) {
    const stage = r.deal_stage;
    if (stage !== "Won" && stage !== "Lost") continue;
    const won = stage === "Won";
    globalClosed += 1;
    if (won) globalWon += 1;
    agentWin.add(r.sales_agent, won);
    const t = teamBy.get(r.sales_agent);
    if (t?.manager) managerWin.add(t.manager, won);
    if (t?.regional_office) regionWin.add(t.regional_office, won);
  }
  const globalRate = globalClosed ? globalWon / globalClosed : 0.2;

  // Distributions for normalization (open deals only for value).
  const openValues: number[] = [];
  const expectedValue = (r: PipelineRow) => {
    if (typeof r.close_value === "number" && r.close_value > 0) {
      return { value: r.close_value, estimated: false };
    }
    const p = productBy.get(r.product);
    return { value: p?.sales_price ?? 0, estimated: true };
  };
  for (const r of data.pipeline) {
    if (OPEN_STAGES.includes(r.deal_stage)) {
      openValues.push(expectedValue(r).value);
    }
  }
  const sortedValues = [...openValues].sort((a, b) => a - b);

  const revenues = data.accounts
    .map((a) => a.revenue)
    .filter((v): v is number => typeof v === "number")
    .sort((a, b) => a - b);
  const employeesArr = data.accounts
    .map((a) => a.employees)
    .filter((v): v is number => typeof v === "number")
    .sort((a, b) => a - b);
  const prices = data.products
    .map((p) => p.sales_price)
    .filter((v): v is number => typeof v === "number")
    .sort((a, b) => a - b);

  return {
    accountBy,
    productBy,
    teamBy,
    now,
    agentWin,
    managerWin,
    regionWin,
    globalRate,
    sortedValues,
    revenues,
    employeesArr,
    prices,
    expectedValue,
  };
}

export interface ScoreResult {
  deals: ScoredDeal[];
  meta: {
    globalWinRate: number;
    referenceDate: string;
  };
}

export function scoreDataset(data: Dataset, lang: Lang = "pt"): ScoreResult {
  const ctx = buildContext(data);
  const S = buildScoringStrings(lang);
  const usd = (n: number) => i18nUSD(n, lang);
  const deals: ScoredDeal[] = [];

  for (const r of data.pipeline) {
    if (!OPEN_STAGES.includes(r.deal_stage)) continue;

    const account = ctx.accountBy.get(r.account);
    const product = ctx.productBy.get(r.product);
    const team = ctx.teamBy.get(r.sales_agent);
    const positives: ScoreFactor[] = [];
    const risks: ScoreFactor[] = [];
    const dataUsed: string[] = [];
    const limitations: string[] = [];

    // ---- Stage (20%) ----
    const isEngaging = r.deal_stage === "Engaging";
    const stage0 = isEngaging ? 1 : 0.45;
    dataUsed.push(S.dataUsed.stage(r.deal_stage));

    // ---- Value (20%) ----
    const { value: expectedValue, estimated } = ctx.expectedValue(r);
    const value0 = percentileRank(ctx.sortedValues, expectedValue);
    dataUsed.push(S.dataUsed.value(usd(expectedValue), estimated));
    if (estimated) limitations.push(S.lim.noCloseValue);

    // ---- Account fit (20%) ----
    const fitParts: number[] = [];
    if (account?.revenue != null) {
      fitParts.push(percentileRank(ctx.revenues, account.revenue));
      dataUsed.push(S.dataUsed.revenue(account.revenue));
    }
    if (account?.employees != null) {
      fitParts.push(percentileRank(ctx.employeesArr, account.employees));
      dataUsed.push(S.dataUsed.employees(account.employees.toLocaleString()));
    }
    const accountFit0 = fitParts.length
      ? fitParts.reduce((a, b) => a + b, 0) / fitParts.length
      : 0.5;
    if (!r.account) limitations.push(S.lim.noAccount);
    else if (!fitParts.length) limitations.push(S.lim.accountNotFound);
    if (account?.sector) dataUsed.push(S.dataUsed.sector(account.sector));

    // ---- Timing / risk (20%) ----
    const engageTs = parseDate(r.engage_date);
    let ageDays: number | null = null;
    let timing0 = 0.5;
    let stale = false;
    if (engageTs != null) {
      ageDays = Math.max(0, Math.round((ctx.now - engageTs) / 86_400_000));
      // Fresh deals carry momentum; aging open deals cool off.
      if (ageDays <= 14) timing0 = 1;
      else if (ageDays >= 120) timing0 = 0.1;
      else timing0 = 1 - (ageDays - 14) / (120 - 14);
      const staleLimit = isEngaging ? 60 : 45;
      stale = ageDays > staleLimit;
      dataUsed.push(S.dataUsed.open(ageDays));
    } else {
      limitations.push(S.lim.noEngageDate);
    }

    // ---- Product / segment (10%) ----
    const product0 =
      product?.sales_price != null ? percentileRank(ctx.prices, product.sales_price) : 0.5;
    if (product?.series) dataUsed.push(S.dataUsed.line(product.series));
    if (product?.sales_price == null) limitations.push(S.lim.noProductPrice);

    // ---- Rep / manager / region signal (10%) ----
    let repRate = ctx.agentWin.rate(r.sales_agent);
    let repBasis = S.repBasis.rep;
    if (repRate == null && team?.manager) {
      repRate = ctx.managerWin.rate(team.manager);
      repBasis = S.repBasis.manager;
    }
    if (repRate == null && team?.regional_office) {
      repRate = ctx.regionWin.rate(team.regional_office);
      repBasis = S.repBasis.region;
    }
    let repUsedTeamAvg = false;
    if (repRate == null) {
      repRate = ctx.globalRate;
      repBasis = S.repBasis.team;
      repUsedTeamAvg = true;
      limitations.push(S.lim.notEnoughClosed);
    }
    const repSignal0 = Math.min(1, repRate / Math.max(0.15, ctx.globalRate * 1.6));

    // ---- Weighted total ----
    const breakdown = [
      {
        name: translateWeightName("Stage", lang),
        weight: WEIGHTS.stage,
        score0to1: stage0,
        weighted: stage0 * WEIGHTS.stage * 100,
      },
      {
        name: translateWeightName("Value", lang),
        weight: WEIGHTS.value,
        score0to1: value0,
        weighted: value0 * WEIGHTS.value * 100,
      },
      {
        name: translateWeightName("Account fit", lang),
        weight: WEIGHTS.accountFit,
        score0to1: accountFit0,
        weighted: accountFit0 * WEIGHTS.accountFit * 100,
      },
      {
        name: translateWeightName("Timing", lang),
        weight: WEIGHTS.timing,
        score0to1: timing0,
        weighted: timing0 * WEIGHTS.timing * 100,
      },
      {
        name: translateWeightName("Product", lang),
        weight: WEIGHTS.product,
        score0to1: product0,
        weighted: product0 * WEIGHTS.product * 100,
      },
      {
        name: translateWeightName("Rep signal", lang),
        weight: WEIGHTS.repSignal,
        score0to1: repSignal0,
        weighted: repSignal0 * WEIGHTS.repSignal * 100,
      },
    ];
    const score = Math.round(breakdown.reduce((s, b) => s + b.weighted, 0));
    const priority = priorityFromScore(score);

    // ---- Human-readable factors ----
    if (isEngaging)
      positives.push({
        code: "active_engagement",
        ...S.factor.activeEngagement,
        points: stage0 * WEIGHTS.stage * 100,
        tone: "positive",
      });
    else
      risks.push({
        code: "early_stage",
        ...S.factor.earlyStage,
        points: stage0 * WEIGHTS.stage * 100,
        tone: "risk",
      });

    if (value0 >= 0.66)
      positives.push({
        code: "high_value",
        ...S.factor.highValue(usd(expectedValue)),
        points: value0 * WEIGHTS.value * 100,
        tone: "positive",
      });
    else if (value0 <= 0.33)
      risks.push({
        code: "smaller_deal",
        ...S.factor.smallerDeal(usd(expectedValue)),
        points: value0 * WEIGHTS.value * 100,
        tone: "risk",
      });

    if (accountFit0 >= 0.66)
      positives.push({
        code: "strong_fit",
        ...S.factor.strongFit(account?.sector ?? (lang === "pt" ? "Conta" : "Account")),
        points: accountFit0 * WEIGHTS.accountFit * 100,
        tone: "positive",
      });
    else if (accountFit0 <= 0.33 && fitParts.length)
      risks.push({
        code: "smaller_account",
        ...S.factor.smallerAccount,
        points: accountFit0 * WEIGHTS.accountFit * 100,
        tone: "risk",
      });

    if (stale)
      risks.push({
        code: "cooling_risk",
        ...S.factor.coolingRisk(ageDays),
        points: timing0 * WEIGHTS.timing * 100,
        tone: "risk",
      });
    else if (timing0 >= 0.7)
      positives.push({
        code: "fresh_momentum",
        ...S.factor.freshMomentum(ageDays),
        points: timing0 * WEIGHTS.timing * 100,
        tone: "positive",
      });

    if (product0 >= 0.66)
      positives.push({
        code: "premium_product",
        ...S.factor.premiumProduct(
          product?.series ?? product?.product ?? (lang === "pt" ? "Produto" : "Product"),
        ),
        points: product0 * WEIGHTS.product * 100,
        tone: "positive",
      });

    const repPct = Math.round((repRate ?? 0) * 100);
    if (repSignal0 >= 0.6)
      positives.push({
        code: "reliable_closer",
        ...S.factor.reliableCloser(repPct, repBasis),
        points: repSignal0 * WEIGHTS.repSignal * 100,
        tone: "positive",
      });
    else if (repSignal0 <= 0.4)
      risks.push({
        code: "below_average",
        ...S.factor.belowAverage(repPct, repBasis),
        points: repSignal0 * WEIGHTS.repSignal * 100,
        tone: "risk",
      });

    // ---- Generated text ----
    const phrase = S.valuePhrase(usd(expectedValue), r.product, r.account, r.opportunity_id);
    const whyThisScore = S.why(priority, { phrase, isEngaging, pct: repPct, stale });
    const riskText = S.risk({
      stale,
      days: ageDays,
      isEngaging,
      repLow: repSignal0 <= 0.4,
      pct: repPct,
      estimated,
    });

    let nextActionCode: import("./types").NextActionCode;
    if (stale && priority !== "High" && priority !== "Priority") nextActionCode = "revive";
    else if (priority === "High") nextActionCode = isEngaging ? "callToday" : "engageBuyer";
    else if (priority === "Priority") nextActionCode = isEngaging ? "followUp" : "qualify";
    else if (repSignal0 <= 0.4 && value0 >= 0.66) nextActionCode = "managerReview";
    else if (priority === "Watch") nextActionCode = "monitor";
    else nextActionCode = "deprioritize";
    const nextBestAction = S.nextAction(nextActionCode);

    if (!team) limitations.push(S.lim.agentNotFound);

    // ---- Confidence / data quality ----
    const lowFlag = !team || engageTs == null || !fitParts.length;
    const medFlag = estimated || repUsedTeamAvg;
    const confidence: import("./types").Confidence = lowFlag ? "Low" : medFlag ? "Medium" : "High";

    deals.push({
      opportunity_id: r.opportunity_id,
      account: r.account,
      sector: account?.sector,
      product: r.product,
      series: product?.series,
      salesAgent: r.sales_agent,
      manager: team?.manager,
      region: team?.regional_office,
      stage: r.deal_stage,
      expectedValue,
      valueIsEstimated: estimated,
      ageDays,
      score,
      priority,
      confidence,
      positives: positives.sort((a, b) => b.points - a.points),
      risks: risks.sort((a, b) => b.points - a.points),
      breakdown,
      whyThisScore,
      risk: riskText,
      nextBestAction,
      nextActionCode,
      dataUsed,
      limitations,
    });
  }

  deals.sort((a, b) => b.score - a.score || b.expectedValue - a.expectedValue);

  return {
    deals,
    meta: {
      globalWinRate: ctx.globalRate,
      referenceDate: new Date(ctx.now).toISOString().slice(0, 10),
    },
  };
}

/** Localized name for a breakdown factor (display only; logic unaffected). */
function translateWeightName(name: string, lang: Lang): string {
  if (lang === "en") return name;
  const map: Record<string, string> = {
    Stage: "Estágio",
    Value: "Valor",
    "Account fit": "Aderência da conta",
    Timing: "Tempo",
    Product: "Produto",
    "Rep signal": "Sinal do vendedor",
  };
  return map[name] ?? name;
}

export const formatUSD = fmtUSD;
export const formatCompactUSD = (n: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(n || 0);
