import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import type { Dataset } from "../src/domain/types";
import { backtest } from "../src/lib/scoring/backtest";
import { buildHistory, FACTOR_KEYS } from "../src/lib/scoring/history";
import { MOMENTUM_LABEL, rankPipeline, type Momentum } from "../src/lib/scoring/score";

const ROOT = process.cwd();
const dataset: Dataset = JSON.parse(readFileSync(path.join(ROOT, "data", "generated", "dataset.json"), "utf8"));
const history = buildHistory(dataset.deals);
const ranked = rankPipeline(dataset.deals, history, dataset.referenceDate);

const pct = (x: number, digits = 1) => `${(x * 100).toFixed(digits).replace(".", ",")}%`;
const usd = (x: number) => `US$ ${Math.round(x).toLocaleString("pt-BR")}`;

// 1. Quanto cada fator varia antes e depois de descontar o ruído.
const factorSpread = FACTOR_KEYS.map((key) => {
  const rates = [...history.factors[key].values()];
  const raw = rates.map((r) => r.raw);
  const shrunk = rates.map((r) => r.shrunk);
  return {
    key,
    groups: rates.length,
    rawMin: Math.min(...raw),
    rawMax: Math.max(...raw),
    shrunkMin: Math.min(...shrunk),
    shrunkMax: Math.max(...shrunk),
  };
});

// 1b. Escritório e manager (não entram no score, só para conferência).
const closedDeals = dataset.deals.filter((d) => d.stage === "Won" || d.stage === "Lost");
function rateBy(key: (d: (typeof closedDeals)[number]) => string) {
  const groups = new Map<string, { wins: number; total: number }>();
  for (const d of closedDeals) {
    const g = groups.get(key(d)) ?? { wins: 0, total: 0 };
    g.total += 1;
    if (d.stage === "Won") g.wins += 1;
    groups.set(key(d), g);
  }
  return groups;
}
const spreadOf = (groups: Map<string, { wins: number; total: number }>) => {
  const r = [...groups.values()].map((g) => g.wins / g.total);
  return { min: Math.min(...r), max: Math.max(...r) };
};
const officeSpread = spreadOf(rateBy((d) => d.regionalOffice));
const managerSpread = spreadOf(rateBy((d) => d.manager));

// 1c. O vendedor é sinal ou ruído? Qui-quadrado e estabilidade entre semestres.
const agentGroups = rateBy((d) => d.agent);
const agentChi2 = [...agentGroups.values()].reduce(
  (s, g) => s + ((g.wins / g.total - history.baseRate) ** 2 * g.total) / (history.baseRate * (1 - history.baseRate)),
  0,
);
function splitHalfCorrelation(key: (d: (typeof closedDeals)[number]) => string, minPerHalf: number) {
  const halves = new Map<string, [{ w: number; n: number }, { w: number; n: number }]>();
  for (const d of closedDeals) {
    const h = halves.get(key(d)) ?? [{ w: 0, n: 0 }, { w: 0, n: 0 }];
    const half = h[d.closeDate! < "2017-07-01" ? 0 : 1];
    half.n += 1;
    if (d.stage === "Won") half.w += 1;
    halves.set(key(d), h);
  }
  const pairs = [...halves.values()].filter(([a, b]) => a.n >= minPerHalf && b.n >= minPerHalf).map(([a, b]) => [a.w / a.n, b.w / b.n]);
  const mean = (xs: number[]) => xs.reduce((s, x) => s + x, 0) / xs.length;
  const mx = mean(pairs.map((p) => p[0]));
  const my = mean(pairs.map((p) => p[1]));
  let cov = 0, vx = 0, vy = 0;
  for (const [x, y] of pairs) {
    cov += (x - mx) * (y - my);
    vx += (x - mx) ** 2;
    vy += (y - my) ** 2;
  }
  return { correlation: cov / Math.sqrt(vx * vy), groups: pairs.length };
}
const agentStability = splitHalfCorrelation((d) => d.agent, 30);
const agentProductStability = splitHalfCorrelation((d) => `${d.agent}|${d.product}`, 15);

// 1d. Valor fechado vs. preço de tabela nos ganhos.
const ratios = closedDeals
  .filter((d) => d.stage === "Won")
  .map((d) => d.closeValue! / d.listPrice)
  .sort((a, b) => a - b);
const closeToList = { p10: ratios[Math.floor(ratios.length * 0.1)], p50: ratios[Math.floor(ratios.length * 0.5)], p90: ratios[Math.floor(ratios.length * 0.9)] };

// 2. Curva de sobrevivência: chance de ganhar dado que o deal segue aberto.
const survivalPoints = [0, 7, 14, 30, 60, 90, 120].map((t) => ({ day: t, winRate: history.survival[t] }));

// 3. Efeito fim de trimestre (mês de fechamento).
const closed = dataset.deals.filter((d) => d.stage === "Won" || d.stage === "Lost");
const quarterEnd = (iso: string) => ["03", "06", "09", "12"].includes(iso.slice(5, 7));
const rateWhere = (pred: (iso: string) => boolean) => {
  const group = closed.filter((d) => pred(d.closeDate!));
  return { deals: group.length, winRate: group.filter((d) => d.stage === "Won").length / group.length };
};
const quarter = { quarterEnd: rateWhere(quarterEnd), otherMonths: rateWhere((d) => !quarterEnd(d)) };

// 4. Retrato do pipeline aberto na data de referência.
const momentums: Momentum[] = ["prospecting", "early", "progressing", "closing", "stalled"];
const pipeline = momentums.map((m) => {
  const group = ranked.filter((r) => r.momentum === m);
  return { momentum: m, label: MOMENTUM_LABEL[m], deals: group.length, listValue: group.reduce((s, r) => s + r.deal.listPrice, 0) };
});
const engaging = ranked.filter((r) => r.deal.stage === "Engaging");
const stalledShare = ranked.filter((r) => r.momentum === "stalled").length / engaging.length;
const openValue = pipeline.reduce((s, p) => s + p.listValue, 0);
const stalledValueShare = pipeline.find((p) => p.momentum === "stalled")!.listValue / openValue;
// Se o vendedor só ordenasse por preço, quanto do topo seria deal parado?
const byPrice = [...ranked].sort((a, b) => b.deal.listPrice - a.deal.listPrice);
const top20ByPrice = byPrice.slice(0, Math.round(byPrice.length * 0.2));
const stalledInTopByPrice = top20ByPrice.filter((r) => r.momentum === "stalled").length / top20ByPrice.length;

// 5. Backtest em três datas de corte.
const backtests = ["2017-06-30", "2017-08-31", "2017-09-30"].map((cutoff) => backtest(dataset.deals, cutoff));

const analysis = {
  referenceDate: dataset.referenceDate,
  history: {
    closedDeals: history.closedDeals,
    baseRate: history.baseRate,
    maxCycle: history.maxCycle,
    lostMedianCycle: history.lostMedianCycle,
    wonMedianCycle: history.wonMedianCycle,
    wonP75Cycle: history.wonP75Cycle,
  },
  factorSpread,
  officeSpread,
  managerSpread,
  agentSignal: { chi2: agentChi2, degreesOfFreedom: agentGroups.size - 1, agentStability, agentProductStability },
  closeToList,
  survivalPoints,
  quarter,
  pipeline,
  stalledShareOfEngaging: stalledShare,
  openValue,
  stalledValueShare,
  stalledInTopByPrice,
  backtests,
};
writeFileSync(path.join(ROOT, "data", "generated", "analysis.json"), JSON.stringify(analysis, null, 2));

// Relatório legível, versionado em docs/FINDINGS.md.
const FACTOR_NAME = { agent: "Vendedor", product: "Produto", sector: "Setor", companySize: "Porte da conta" };
const lines: string[] = [
  "# Achados (gerado por `npm run analyze`)",
  "",
  "> Arquivo gerado automaticamente. Não editar à mão.",
  "",
  `Base: ${history.closedDeals.toLocaleString("pt-BR")} deals fechados · taxa de vitória ${pct(history.baseRate)} · data de referência ${dataset.referenceDate}.`,
  "",
  "## 1. Quanto cada fator realmente separa ganhos de perdas",
  "",
  "| Fator | Grupos | Taxa bruta (mín–máx) | Após descontar o ruído |",
  "|---|---|---|---|",
  ...factorSpread.map(
    (f) =>
      `| ${FACTOR_NAME[f.key]} | ${f.groups} | ${pct(f.rawMin)} – ${pct(f.rawMax)} | ${pct(f.shrunkMin)} – ${pct(f.shrunkMax)} |`,
  ),
  "",
  `Escritório: ${pct(officeSpread.min)} – ${pct(officeSpread.max)}. Manager: ${pct(managerSpread.min)} – ${pct(managerSpread.max)}.`,
  "",
  "### O vendedor é sinal ou ruído?",
  "",
  `- Qui-quadrado das taxas por vendedor: ${agentChi2.toFixed(1).replace(".", ",")} com ${agentGroups.size - 1} graus de liberdade (o esperado se todos tivessem a mesma taxa real é ≈ ${agentGroups.size - 1}).`,
  `- Correlação da taxa do vendedor entre 1º e 2º semestre: ${agentStability.correlation.toFixed(2).replace(".", ",")} (${agentStability.groups} vendedores com 30+ deals em cada semestre).`,
  `- Mesma correlação para vendedor × produto: ${agentProductStability.correlation.toFixed(2).replace(".", ",")} (${agentProductStability.groups} pares com 15+ deals em cada semestre).`,
  "",
  `Valor fechado ÷ preço de tabela nos ganhos: p10 ${closeToList.p10.toFixed(2)} · mediana ${closeToList.p50.toFixed(2)} · p90 ${closeToList.p90.toFixed(2)}.`,
  "",
  "## 2. Tempo no pipeline",
  "",
  `Ciclo dos perdidos: mediana de ${history.lostMedianCycle} dias. Ciclo dos ganhos: mediana de ${history.wonMedianCycle} e p75 de ${history.wonP75Cycle} dias. Maior ciclo já observado: ${history.maxCycle} dias.`,
  "",
  "| Deal ainda aberto após | Chance de ganhar |",
  "|---|---|",
  ...survivalPoints.map((p) => `| ${p.day} dias | ${pct(p.winRate)} |`),
  "",
  "## 3. Fim de trimestre",
  "",
  `Deals fechados no último mês do trimestre: ${pct(quarter.quarterEnd.winRate)} de vitória (${quarter.quarterEnd.deals} deals). Nos demais meses: ${pct(quarter.otherMonths.winRate)} (${quarter.otherMonths.deals} deals).`,
  "",
  "## 4. Pipeline aberto em " + dataset.referenceDate,
  "",
  "| Momento | Deals | Valor de tabela |",
  "|---|---|---|",
  ...pipeline.map((p) => `| ${p.label} | ${p.deals} | ${usd(p.listValue)} |`),
  "",
  `${pct(stalledShare, 0)} dos deals em Engaging estão abertos há mais tempo que qualquer deal já fechado. Eles somam ${pct(stalledValueShare, 0)} do valor de tabela do pipeline aberto (${usd(openValue)}).`,
  "",
  `Se o vendedor apenas ordenasse o pipeline por preço, ${pct(stalledInTopByPrice, 0)} do top 20% seriam deals parados.`,
  "",
  "## 5. Backtest",
  "",
  ...backtests.flatMap((b) => [
    `### Corte em ${b.cutoff}`,
    "",
    `Aprendeu com ${b.trainedOn} deals fechados até o corte; avaliou ${b.evaluated} deals abertos no corte (vitória real: ${pct(b.evaluatedWinRate)}).`,
    "",
    "| Estratégia | AUC da chance | Receita no top 20% | % da receita total |",
    "|---|---|---|---|",
    ...b.strategies.map(
      (s) => `| ${s.name} | ${s.auc === null ? "—" : s.auc.toFixed(3)} | ${usd(s.top20Revenue)} | ${pct(s.top20Share)} |`,
    ),
    "",
    b.stalled.count > 0
      ? `Deals que a regra marcaria como **parados** no corte: ${b.stalled.count}, com vitória real de ${pct(b.stalled.winRate ?? 0)}.`
      : "Nenhum deal estaria parado nesse corte.",
    "",
  ]),
];
writeFileSync(path.join(ROOT, "..", "docs", "FINDINGS.md"), lines.join("\n"));
console.log(lines.join("\n"));
