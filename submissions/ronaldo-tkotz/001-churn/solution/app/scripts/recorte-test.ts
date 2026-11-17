/** Drill-down engine (ISC-40): totals, breakdowns that add up, path checks, refused values. */
import assert from "node:assert/strict";
import { recorte } from "../src/engine/recorte";
import { lerFiltros } from "../src/engine/filtros";
import { runQuery } from "../src/engine/warehouse";

let n = 0;
const ok = (c: unknown, msg: string) => { assert.ok(c, msg); n++; };
const f = lerFiltros({});

// 1. "Recursos" on the reasons chart
const r = recorte(f, { universo: "evento", caminho: [{ dim: "motivo", valor: "features" }] });
const esperado = Number(runQuery("SELECT count(*) AS n FROM churn_events WHERE reason_code = 'features'").rows[0].n);
ok(r.total === esperado, `total ${r.total} = ${esperado}`);
ok(!r.quebras.some((q) => q.dim === "motivo"), "a dimensão do caminho não se quebra de novo");
for (const q of r.quebras) ok(q.dados.reduce((s, d) => s + d.value, 0) === r.total, `quebra ${q.dim} soma ${r.total}`);
ok(r.caminho[0].rotulo === "Recursos", "rótulo em português");
ok(r.registros.linhas.length > 0 && r.registros.linhas.every((l) => l.motivo === "features"), "registros só do recorte");
ok(r.perfil && r.perfil.linhas[0].recorte === r.contas, "perfil conta as contas do recorte");

// 2. one level deeper
const setor = r.quebras.find((q) => q.dim === "setor")!.dados[0];
const r2 = recorte(f, { universo: "evento", caminho: [{ dim: "motivo", valor: "features" }, { dim: "setor", valor: setor.chave }] });
ok(r2.total === setor.value, "segundo nível = barra clicada");

// 3. injected or unknown values are refused
assert.throws(() => recorte(f, { universo: "evento", caminho: [{ dim: "motivo", valor: "x' OR 1=1 --" }] }));
assert.throws(() => recorte(f, { universo: "evento", caminho: [{ dim: "nao_existe", valor: "a" }] }));
n += 2;

// 4. cross and the other universes
const c = recorte(f, { universo: "evento", caminho: [{ dim: "motivo", valor: "features" }], cruzar: ["setor", "plano_conta"] });
ok(c.cruzamento && c.cruzamento.celulas.flat().reduce((s, v) => s + v, 0) === r.total, "cruzamento soma o recorte");
const conta = recorte(f, { universo: "conta", caminho: [{ dim: "setor", valor: "DevTools" }] });
ok(conta.total === Number(runQuery("SELECT count(*) AS n FROM accounts WHERE industry='DevTools'").rows[0].n), "universo conta");
const ass = recorte(f, { universo: "assinatura", caminho: [{ dim: "cobranca", valor: "Mensal" }] });
ok(ass.total === Number(runQuery("SELECT count(*) AS n FROM subscriptions WHERE billing_frequency='monthly'").rows[0].n), "universo assinatura");

// 5. global filters apply
const fp = lerFiltros({ setor: "FinTech" });
const rf = recorte(fp, { universo: "evento", caminho: [{ dim: "motivo", valor: "features" }] });
ok(rf.total < r.total && rf.quebras.find((q) => q.dim === "setor") === undefined, "filtro global aplicado");

console.log(`RECORTE OK (${n} checagens) · features = ${r.total} eventos, ${r.contas} contas, ${r.quebras.length} quebras`);

// 6. tickets and usage (screen 3)
const tk = recorte(f, { universo: "ticket", caminho: [{ dim: "prioridade", valor: "Urgente" }] });
assert.equal(tk.total, Number(runQuery("SELECT count(*) AS n FROM support_tickets WHERE priority = 'urgent'").rows[0].n));
const uso = recorte(f, { universo: "uso", caminho: [{ dim: "recurso", valor: "feature_12" }] });
assert.equal(uso.total, Number(runQuery("SELECT sum(usage_count) AS n FROM feature_usage WHERE feature_name = 'feature_12'").rows[0].n));
assert.ok(uso.quebras.every((q) => q.dados.reduce((s, d) => s + d.value, 0) === uso.total));
console.log(`RECORTE OK (+3 checagens: tickets ${tk.total}, usos ${uso.total})`);
