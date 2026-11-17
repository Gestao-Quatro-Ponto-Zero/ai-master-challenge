/**
 * Screen 1 (B1.1–B1.3) against the RavenStack database. Run: bun run tela1-test
 * (needs WAREHOUSE_PATH). Each check compares the screen's engine with an independent query.
 */
import { b11, b12, b13 } from "../src/engine/tela1";
import { lerFiltros, opcoesFiltro, whereConta } from "../src/engine/filtros";
import { runQuery } from "../src/engine/warehouse";

let failed = 0;
function check(name: string, cond: boolean, detail = ""): void {
  process.stdout.write(`${cond ? "✓" : "✗"} ${name}${detail ? ` — ${detail}` : ""}\n`);
  if (!cond) failed++;
}
const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);
const semFiltro = lerFiltros({});

// B1.1 without filters equals vw_mes month by month (ISC-15e).
const r = b11(semFiltro);
const vw = runQuery(
  `SELECT mes, contas_ativas, churn_contas, churn_eventos, 100.0 * taxa_churn_contas AS t,
          100.0 * taxa_churn_contas_na_base AS tb, churn_contas_fora_da_base AS fora FROM vw_mes ORDER BY mes`,
).rows;
check("B1.1 has 24 months", r.meses.length === 24 && vw.length === 24);
// vw_mes stores rates at 4 decimals; the screen rounds once to 1 decimal (in %), so allow half a step.
const near = (a: unknown, b: number) => Math.abs(Number(a) - b) <= 0.0501;
const same = vw.every(
  (row, i) =>
    row.mes === r.meses[i] &&
    Number(row.contas_ativas) === r.contasAtivas[i] &&
    Number(row.churn_contas) === r.contasComEvento[i] &&
    Number(row.churn_eventos) === r.eventos[i] &&
    near(row.t, r.taxa[i]) &&
    near(row.tb, r.taxaNaBase[i]),
);
check("B1.1 unfiltered = vw_mes, month by month", same);
check("B1.1 events sum to 600", r.totalEventos === 600, String(r.totalEventos));
check("B1.1 rates differ in 14 months", r.mesesQueDiferem === 14, String(r.mesesQueDiferem));
check("B1.1 lost MRR: 352 accounts", r.mrrPerdido.contas === 352, String(r.mrrPerdido.contas));
check("B1.1 lost MRR = 7,990,982", Math.round(r.mrrPerdido.mrr) === 7990982, String(r.mrrPerdido.mrr));

// Sector filter partitions the accounts: per-sector events add up to the total.
const setores = opcoesFiltro().setor;
const porSetor = setores.map((s) => b11(lerFiltros({ setor: s })).totalEventos);
check("B1.1 events by sector add to 600", sum(porSetor) === 600, porSetor.join(" + "));

// B1.2 totals.
const t = b12(semFiltro);
check("B1.2 2,000 tickets with alerts", t.comAlerta.tickets === 2000, String(t.comAlerta.tickets));
check("B1.2 825 without score", t.comAlerta.semNota === 825, String(t.comAlerta.semNota));
check("B1.2 1,077 T08 tickets", t.ticketsT08 === 1077, String(t.ticketsT08));
check("B1.2 without T08 = 2,000 − T08", t.semAlerta.tickets === t.comAlerta.tickets - t.ticketsT08);
check("B1.2 quarters sum to the total", sum([...t.nota3, ...t.nota4, ...t.nota5, ...t.semNota]) === 2000);
const t2 = b12(lerFiltros({ alerta: "sem" }));
check("B1.2 'sem alerta' drops T08", sum([...t2.nota3, ...t2.nota4, ...t2.nota5, ...t2.semNota]) === t.semAlerta.tickets);

// B1.3 totals.
const u = b13(semFiltro);
check("B1.3 25,000 usage records", u.totalCom === 25000, String(u.totalCom));
const t06 = Number(runQuery("SELECT count(*) AS n FROM vw_dq_ocorrencias WHERE check_id = 'T06'").rows[0].n);
check("B1.3 T06 count = vw_dq_ocorrencias", u.registrosT06 === t06, `${u.registrosT06} vs ${t06}`);
check("B1.3 sectors add to the monthly total", sum(u.porSetor.flatMap((s) => s.valores)) === u.totalCom);

// Plan follows the identifier (D27).
const plano = opcoesFiltro().plano[0];
const fp = lerFiltros({ plano });
const contasPlano = Number(runQuery(`SELECT count(*) AS n FROM vw_conta a WHERE churn_rotulo = 1 AND ${whereConta(fp)}`).rows[0].n);
check(`plan ${plano}: lost MRR uses the account's plan`, b11(fp).mrrPerdido.contas === contasPlano);
const usoPlano = Number(runQuery(`SELECT count(*) AS n FROM feature_usage u JOIN subscriptions s USING (subscription_id) WHERE s.plan_tier = '${plano}'`).rows[0].n);
check(`plan ${plano}: usage uses the subscription's plan`, b13(fp).totalCom === usoPlano, `${b13(fp).totalCom} vs ${usoPlano}`);

// Values outside the database never reach SQL.
check("unknown filter value is dropped", lerFiltros({ setor: "x' OR 1=1 --" }).setor === undefined);

process.stdout.write(failed === 0 ? "\nTELA 1 OK\n" : `\n${failed} FAILED\n`);
process.exit(failed === 0 ? 0 : 1);
