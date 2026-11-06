// Auditoria: quanto do volume a IA encaminha sozinha DEPOIS das regras (Retenção, RH, Segurança etc.)?
// Uso: node src/coverage_with_rules.js model.json textos_teste.json
const fs = require("fs");
const { buildIndex, triage } = require("./engine.js");
const model = JSON.parse(fs.readFileSync(process.argv[2])); const ix = buildIndex(model);
const rows = JSON.parse(fs.readFileSync(process.argv[3]));
const count = {}; let auto = 0, autoOk = 0, rev = 0, revIn2 = 0; const prio = { P1: 0, P2: 0, P3: 0 }; let ask = 0;
const examples = {};
for (const r of rows) {
  const t = triage(r.text, model, ix);
  count[t.lane] = (count[t.lane] || 0) + 1; prio[t.priority.level]++; if (t.askImpact) ask++;
  if (t.lane === "auto") { auto++; if (t.top === r.real) autoOk++; }
  if (t.lane === "revisao") { rev++; if (t.top === r.real || t.second === r.real) revIn2++; }
  if (!["auto", "revisao"].includes(t.lane) && (examples[t.lane] || []).length < 3) (examples[t.lane] = examples[t.lane] || []).push(r.text.slice(0, 110));
}
const n = rows.length, pc = (x) => (100 * x / n).toFixed(1) + "%";
console.log(`n=${n}`);
for (const [k, v] of Object.entries(count).sort((a, b) => b[1] - a[1])) console.log(`  ${k.padEnd(11)} ${String(v).padStart(5)}  ${pc(v)}`);
console.log(`IA encaminhou sozinha: ${pc(auto)} com acerto ${(100 * autoOk / auto).toFixed(1)}%`);
console.log(`Atendente escolhe: ${pc(rev)}; categoria certa entre as 2 opções: ${(100 * revIn2 / rev).toFixed(1)}%`);
console.log(`Prioridade: P1 ${pc(prio.P1)} · P2 ${pc(prio.P2)} · P3 ${pc(prio.P3)} · pergunta de impacto ${pc(ask)}`);
console.log("Exemplos desviados pelas regras:", JSON.stringify(examples, null, 1));
