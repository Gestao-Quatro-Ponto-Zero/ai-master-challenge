/**
 * Screen 2 (D34) against the RavenStack database. Run: bun run tela2-test.
 * Each churn breakdown must match an independent count; filters must reach every chart.
 */
import { churnPorSetor, churnPorOrigem, churnPorPais, motivosChurn } from "../src/engine/visaoGeral";
import { composicaoPlano, composicaoCobranca, composicaoTrial } from "../src/engine/tela2";
import { lerFiltros } from "../src/engine/filtros";
import { runQuery } from "../src/engine/warehouse";

let failed = 0;
function check(name: string, cond: boolean, detail = ""): void {
  process.stdout.write(`${cond ? "✓" : "✗"} ${name}${detail ? ` — ${detail}` : ""}\n`);
  if (!cond) failed++;
}
const one = (sql: string) => Number(Object.values(runQuery(sql).rows[0])[0]);
const val = (s: { dados: { label: string; value: number }[] }, label: string) => s.dados.find((d) => d.label === label)?.value;
const f = lerFiltros({});

// Account breakdowns: % of accounts with churn_flag = 1 (D36), against accounts directly.
const pctContas = (where: string) =>
  Math.round((1000 * one(`SELECT sum(churn_flag) FROM accounts a WHERE ${where}`)) / one(`SELECT count(*) FROM accounts a WHERE ${where}`)) / 10;
check("indústria: 5 barras", churnPorSetor(f).dados.length === 5);
check("origem: 5 barras", churnPorOrigem(f).dados.length === 5);
check("indústria DevTools = 31% e FinTech = 22,3% (churn_flag)", churnPorSetor(f).dados.find((d) => d.label === "DevTools")?.value === 31 && churnPorSetor(f).dados.find((d) => d.label === "FinTech")?.value === 22.3);
const pais = churnPorPais(f);
check("país: 7 barras", pais.dados.length === 7);
check("país UK = consulta independente (19%)", val(pais, "UK") === pctContas("a.country = 'UK'") && val(pais, "UK") === 19, String(val(pais, "UK")));
check("país DE = consulta independente (32%)", val(pais, "DE") === pctContas("a.country = 'DE'"), String(val(pais, "DE")));
check("motivos somam 600 eventos", motivosChurn(f).dados.reduce((a, b) => a + b.value, 0) === 600);

// Bottom row: how the churn splits (D37). Plan and trial over the 110 accounts with churn_flag;
// billing over the subscriptions with churn_flag.
const soma = (s: { dados: { value: number }[] }) => s.dados.reduce((a, b) => a + b.value, 0);
const plano = composicaoPlano(f);
check("plano: soma 110 contas com churn", soma(plano) === 110, String(soma(plano)));
check("plano: Basic 37, Enterprise 34, Pro 39", val(plano, "Basic") === 37 && val(plano, "Enterprise") === 34 && val(plano, "Pro") === 39);
const trial = composicaoTrial(f);
check("trial × pagas: 25 + 85 = 110", val(trial, "Trial") === 25 && val(trial, "Pagas") === 85);
const cob = composicaoCobranca(f);
const assinChurn = one("SELECT count(*) FROM subscriptions WHERE churn_flag = 1");
check("cobrança: soma as assinaturas com churn_flag", soma(cob) === assinChurn, `${soma(cob)} / ${assinChurn}`);
check("cobrança: anual 247, mensal 239", val(cob, "Anual") === 247 && val(cob, "Mensal") === 239);

// Filters reach every chart.
const fin = lerFiltros({ setor: "FinTech" });
check("FinTech: país filtrado", JSON.stringify(churnPorPais(fin).dados) !== JSON.stringify(pais.dados));
check("FinTech: plano soma as 25 contas com churn", soma(composicaoPlano(fin)) === one("SELECT sum(churn_flag) FROM accounts WHERE industry = 'FinTech'"));
const finCob = one("SELECT count(*) FROM subscriptions WHERE churn_flag = 1 AND account_id IN (SELECT account_id FROM accounts WHERE industry = 'FinTech')");
check("FinTech: cobrança soma as assinaturas com churn do setor", soma(composicaoCobranca(fin)) === finCob, `${soma(composicaoCobranca(fin))} / ${finCob}`);
const pro = lerFiltros({ plano: "Pro" });
check("plano Pro: cobrança usa o plano da assinatura", soma(composicaoCobranca(pro)) === one("SELECT count(*) FROM subscriptions WHERE churn_flag = 1 AND plan_tier = 'Pro'"));

process.stdout.write(failed === 0 ? "\nTELA 2 OK\n" : `\n${failed} FAILED\n`);
process.exit(failed === 0 ? 0 : 1);
