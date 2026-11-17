/**
 * Asserts the overview's grounded numbers against the RavenStack database (counts verified
 * in process-log/decisions.md D20–D24). Run under node/tsx (better-sqlite3 native binding).
 */
import { kpis, churnTrend, mrrByPlan } from "../src/engine/dashboard";
import { METRICS } from "../src/engine/metrics";
import { runQuery } from "../src/engine/warehouse";
import { dataClock } from "../src/engine/calendar";

let failed = 0;
function check(name: string, cond: boolean, detail = ""): void {
  process.stdout.write(`${cond ? "✓" : "✗"} ${name}${detail ? ` — ${detail}` : ""}\n`);
  if (!cond) failed++;
}

const clock = dataClock();
check("clock = 2023-01-01 .. 2024-12-31", clock.firstDate === "2023-01-01" && clock.lastDate === "2024-12-31", `${clock.firstDate}..${clock.lastDate}`);

const k = kpis();
const byId = Object.fromEntries(k.map((x) => [x.id, x]));
check("4 KPIs", k.length === 4);
check("contas = 500", byId.contas?.value === 500, String(byId.contas?.value));
check("contas com evento = 352 (600 eventos)", byId.contas_com_evento?.value === 352 && byId.contas_com_evento.sub.startsWith("600"), `${byId.contas_com_evento?.value} · ${byId.contas_com_evento?.sub}`);
check("taxa dez/2024 = 19,2%", byId.taxa_ultimo_mes?.value === 19.2, String(byId.taxa_ultimo_mes?.value));
check("every KPI carries SQL and a 24-month spark", k.every((x) => x.sql.length > 0 && x.spark.length === 24));

const t = churnTrend();
check("trend 2023-01 .. 2024-12", t.categories[0] === "2023-01" && t.categories.at(-1) === "2024-12", `${t.categories[0]}..${t.categories.at(-1)}`);
const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);
check("trend events sum to 600", sum(t.series[1].values) === 600, String(sum(t.series[1].values)));

const s = mrrByPlan();
const base = runQuery(METRICS.base_resumo.sql).rows[0] as { mrr_sem_fim: number };
check("MRR by plan sums to MRR sem fim", Math.round(sum(s.data.map((d) => d.value))) === Math.round(base.mrr_sem_fim), `${sum(s.data.map((d) => d.value))} vs ${base.mrr_sem_fim}`);

for (const m of Object.values(METRICS)) {
  const r = runQuery(m.sql);
  check(`metric ${m.id} returns rows`, r.rowCount > 0, String(r.rowCount));
}

process.stdout.write(failed === 0 ? "\nDASHBOARD OK\n" : `\n${failed} FAILED\n`);
process.exit(failed === 0 ? 0 : 1);
