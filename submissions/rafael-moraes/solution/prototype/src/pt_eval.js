// Avaliação da camada de português: mesmos 56 tickets de teste em inglês (original) e traduzidos para PT.
const fs = require("fs");
const { buildIndex, predictProba } = require("./engine.js");
const { ptToModelText } = require("./glossary_pt.js");
const [modelPath, srcPath, ptPath] = process.argv.slice(2);
const model = JSON.parse(fs.readFileSync(modelPath)); const index = buildIndex(model);
const src = JSON.parse(fs.readFileSync(srcPath)); const pt = JSON.parse(fs.readFileSync(ptPath));
const top = (t) => { const p = predictProba(t, model, index).probs; const i = p.indexOf(Math.max(...p)); return [model.classes[i], p[i]]; };
let en = 0, raw = 0, gl = 0, glAuto = 0, glAutoOk = 0; const rows = [];
src.forEach((s, i) => {
  const [a] = top(s.text); const [b] = top(pt[i]); const [c, conf] = top(ptToModelText(pt[i]).text);
  en += a === s.y; raw += b === s.y; gl += c === s.y;
  if (conf >= 0.8) { glAuto++; glAutoOk += c === s.y; }
  rows.push({ i, real: s.y, en: a, pt_glossario: c, conf: +conf.toFixed(2) });
});
const n = src.length, pc = (x) => (100 * x / n).toFixed(1) + "%";
console.log(`n=${n} | inglês original ${pc(en)} | português sem glossário ${pc(raw)} | português com glossário ${pc(gl)}`);
console.log(`PT com glossário acima de 80%: ${glAuto} tickets, ${glAutoOk} certos`);
fs.writeFileSync(process.argv[5] || "pt_eval_result.json", JSON.stringify(rows, null, 1));
rows.filter((r) => r.pt_glossario !== r.real).forEach((r) => console.log(`  #${r.i} real ${r.real} → PT ${r.pt_glossario} (${r.conf}) | EN ${r.en}`));
