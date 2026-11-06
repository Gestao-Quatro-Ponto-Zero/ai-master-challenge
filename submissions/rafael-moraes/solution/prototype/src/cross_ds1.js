// Auditoria (cruzamento real): o que o motor faz com os textos do Dataset 1, por tipo de ticket?
// Uso: node src/cross_ds1.js model.json caminho/customer_support_tickets.csv
const fs = require("fs");
const { buildIndex, triage } = require("./engine.js");
const { parseCSV } = require("./health.js");
const model = JSON.parse(fs.readFileSync(process.argv[2])); const ix = buildIndex(model);
const { header, rows } = parseCSV(fs.readFileSync(process.argv[3], "utf8"));
const iType = header.indexOf("Ticket Type"), iSub = header.indexOf("Ticket Subject"), iDesc = header.indexOf("Ticket Description");
const by = {};
for (const r of rows) {
  const t = triage(r[iSub] + ". " + r[iDesc], model, ix);
  const g = (by[r[iType]] = by[r[iType]] || { n: 0, conf: 0, lanes: {}, cats: {} });
  g.n++; g.conf += t.conf; g.lanes[t.lane] = (g.lanes[t.lane] || 0) + 1; g.cats[t.top] = (g.cats[t.top] || 0) + 1;
}
const pc = (x, n) => Math.round(100 * x / n) + "%";
for (const [type, g] of Object.entries(by)) {
  const top = (o) => Object.entries(o).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([k, v]) => `${k} ${pc(v, g.n)}`).join(", ");
  console.log(`${type.padEnd(22)} n=${g.n} conf média ${pc(g.conf, g.n)} | filas: ${top(g.lanes)} | categorias de TI: ${top(g.cats)}`);
}
