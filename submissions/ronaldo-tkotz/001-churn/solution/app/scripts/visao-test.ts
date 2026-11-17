/**
 * Executive overview (D28) against the RavenStack database. Run: bun run visao-test.
 * Headline numbers are checked against independent queries; breakdowns must add up.
 */
import {
  indicadores,
  motivosChurn,
  receitaPorSetor,
  receitaPorPlano,
  receitaPorPais,
  churnPorSetor,
  crescimentoMensal,
  receitaNovaVsPerdida,
  contasPagasTrial,
  idadeMedia,
} from "../src/engine/visaoGeral";
import { lerFiltros } from "../src/engine/filtros";
import { runQuery } from "../src/engine/warehouse";

let failed = 0;
function check(name: string, cond: boolean, detail = ""): void {
  process.stdout.write(`${cond ? "✓" : "✗"} ${name}${detail ? ` — ${detail}` : ""}\n`);
  if (!cond) failed++;
}
const one = (sql: string) => Number(Object.values(runQuery(sql).rows[0])[0]);
const sum = (xs: { value: number }[]) => xs.reduce((a, b) => a + b.value, 0);
const f = lerFiltros({});
const k = indicadores(f);

check("contas = 500", k.contas === 500, String(k.contas));
check("accounts.churn_flag = 1 → 110", k.contasFlag === 110, String(k.contasFlag));
check("subscriptions com end_date = 486, em 312 contas", k.assinaturasEncerradas === 486 && k.contasComAssinaturaEncerrada === 312, `${k.assinaturasEncerradas} / ${k.contasComAssinaturaEncerrada}`);
check("assinaturas = 5.000", k.assinaturas === 5000, String(k.assinaturas));
check("assinaturas ativas = sem end_date", k.assinaturasAtivas === one("SELECT count(*) FROM subscriptions WHERE end_date IS NULL"), String(k.assinaturasAtivas));
check("contas com churn = 352", k.contasComChurn === 352, String(k.contasComChurn));
check("eventos = 600", k.eventos === 600, String(k.eventos));
check("churn rate dez/2024 = 19,2%", k.ultimoMes === "2024-12" && k.taxaUltimoMes === 19.2, `${k.ultimoMes} ${k.taxaUltimoMes}`);
const mrr = one("SELECT sum(mrr_amount) FROM subscriptions WHERE end_date IS NULL");
check("MRR ativo = soma das assinaturas sem fim", Math.round(k.mrrAtivo) === Math.round(mrr), `${k.mrrAtivo} vs ${mrr}`);

check("motivos somam 600 eventos", sum(motivosChurn(f).dados) === 600, String(sum(motivosChurn(f).dados)));
for (const [nome, s] of [
  ["indústria", receitaPorSetor(f)],
  ["plano", receitaPorPlano(f)],
  ["país", receitaPorPais(f)],
] as const) {
  check(`receita por ${nome} soma o MRR ativo`, Math.abs(sum(s.dados) - mrr) < s.dados.length, `${sum(s.dados)} vs ${mrr}`);
}
const devtools = churnPorSetor(f).dados.find((d) => d.label === "DevTools");
check("churn DevTools = 31% (churn_flag, D36)", devtools?.value === 31, String(devtools?.value));

// Month-on-month growth (D30): starts once the previous month had 5+ accounts with an event.
const cr = crescimentoMensal(f);
const ult = cr.meses.length - 1;
check("crescimento começa em 2023-04", cr.primeiroMes === "2023-04", cr.primeiroMes);
check("dez/2024: contas +5,3%, churn +60%", cr.contas[ult] === 5.3 && cr.churn[ult] === 60, `${cr.contas[ult]} / ${cr.churn[ult]}`);
check("fev/2024: churn caiu 44,4%", cr.churn[cr.meses.indexOf("2024-02")] === -44.4);

// Linear trend (least squares in SQL) matches an independent fit.
const ajuste = (y: number[]) => { const n = y.length, xs = y.map((_, i) => i + 1); const sx = xs.reduce((a, b) => a + b, 0), sy = y.reduce((a, b) => a + b, 0); const sxx = xs.reduce((a, x) => a + x * x, 0), sxy = xs.reduce((a, x, i) => a + x * y[i], 0); const b = (n * sxy - sx * sy) / (n * sxx - sx * sx); return xs.map((x) => (sy - b * sx) / n + b * x); };
const perto = (a: number[], b: number[]) => a.every((v, i) => Math.abs(v - b[i]) <= 0.051);
check("tendência das contas = regressão linear", perto(cr.tendContas, ajuste(cr.contas)), `${cr.tendContas[0]} → ${cr.tendContas[ult]}`);
check("tendência do churn = regressão linear", perto(cr.tendChurn, ajuste(cr.churn)), `${cr.tendChurn[0]} → ${cr.tendChurn[ult]}`);

// New-account revenue vs revenue lost to cancellations (D31).
const rv = receitaNovaVsPerdida(f);
const reais = (xs: (number | null)[]) => xs.slice(0, rv.inicioProjecao).map((v) => v ?? 0);
const perdida2024 = one("SELECT sum(mrr_amount) FROM subscriptions WHERE end_date >= '2024-01-01' AND end_date < '2025-01-01'");
check("perda 2024 = MRR das assinaturas encerradas em 2024", Math.abs(reais(rv.perdida).reduce((a, b) => a + b, 0) - perdida2024) < 1, String(perdida2024));
const nova2024 = one("SELECT sum(s.mrr_amount) FROM subscriptions s JOIN (SELECT account_id, substr(min(start_date), 1, 7) AS m FROM subscriptions GROUP BY account_id) p ON p.account_id = s.account_id AND p.m = substr(s.start_date, 1, 7) WHERE s.start_date >= '2024-01-01' AND s.start_date < '2025-01-01'");
check("receita nova 2024 = 1ª assinatura das contas novas", Math.abs(reais(rv.nova).reduce((a, b) => a + b, 0) - nova2024) < 1, String(nova2024));
const tn = ajuste(reais(rv.nova)), tp = ajuste(reais(rv.perdida));
check("tendências = regressão linear de 2024", tn.every((v, i) => rv.tendNova[i] === null || Math.abs(v - (rv.tendNova[i] ?? 0)) <= 0.51) && tp.every((v, i) => rv.tendPerdida[i] === null || Math.abs(v - (rv.tendPerdida[i] ?? 0)) <= 0.51));
const xCruz = rv.inicioProjecao + 1 + Math.ceil(((tn[11] - tp[11]) / ((tp[11] - tp[0]) / 11 - (tn[11] - tn[0]) / 11)) - 1);
check("cruzamento em 2026-03, 15 meses após dez/2024", rv.mesCruzamento === "2026-03" && rv.mesesAteCruzamento === 15 && rv.meses[xCruz - 1] === "2026-03", `${rv.mesCruzamento} / ${rv.mesesAteCruzamento} / ${rv.meses[xCruz - 1]}`);

// Paid vs trial accounts (D32): adds up to every account.
const pt = contasPagasTrial(f).dados;
check("contas pagas + trial = 500 (403 / 97)", sum(pt) === 500 && pt.find((d) => d.label === "Trial")?.value === 97, JSON.stringify(pt));

// Filters reach every number.
const fin = indicadores(lerFiltros({ setor: "FinTech" }));
check("FinTech: 112 contas, 76 com churn", fin.contas === 112 && fin.contasComChurn === 76, `${fin.contas} / ${fin.contasComChurn}`);
// D40: average age of the base, month by month.
const idade = idadeMedia(f);
check("idade: 24 meses, de 2023-01 a 2024-12", idade.meses.length === 24 && idade.meses[0] === "2023-01" && idade.meses[23] === "2024-12");
const idadeDez = one("SELECT round(avg(julianday('2024-12-31 23:59:59') - julianday(a.signup_date)) / 30.4375, 2) FROM accounts a WHERE EXISTS (SELECT 1 FROM subscriptions s WHERE s.account_id = a.account_id AND s.start_date <= '2024-12-31 23:59:59' AND (s.end_date IS NULL OR s.end_date >= '2024-12-01 00:00:00'))");
check("idade das contas em dez/2024 = consulta independente (11,16 meses)", idade.contas[23] === idadeDez && idadeDez === 11.16, `${idade.contas[23]} vs ${idadeDez}`);
const assinDez = one("SELECT round(avg(julianday('2024-12-31 23:59:59') - julianday(start_date)) / 30.4375, 2) FROM subscriptions WHERE start_date <= '2024-12-31 23:59:59' AND (end_date IS NULL OR end_date >= '2024-12-01 00:00:00')");
check("idade das assinaturas em dez/2024 = consulta independente (5,44 meses)", idade.assinaturas[23] === assinDez && assinDez === 5.44, `${idade.assinaturas[23]} vs ${assinDez}`);
const idadeFin = idadeMedia(lerFiltros({ setor: "FinTech" }));
check("idade: o filtro de setor chega às duas linhas", idadeFin.contas[23] !== idade.contas[23] && idadeFin.assinaturas[23] !== idade.assinaturas[23]);


process.stdout.write(failed === 0 ? "\nVISÃO GERAL OK\n" : `\n${failed} FAILED\n`);
process.exit(failed === 0 ? 0 : 1);
