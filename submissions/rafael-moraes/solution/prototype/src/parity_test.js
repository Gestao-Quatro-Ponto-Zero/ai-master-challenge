// Teste de paridade: as probabilidades do navegador batem com as do Python?
const fs = require("fs");
const { buildIndex, predictProba } = require("./engine.js");
const model = JSON.parse(fs.readFileSync(process.argv[2]));
const cases = JSON.parse(fs.readFileSync(process.argv[3]));
const index = buildIndex(model);
let maxDiff = 0, sameTop = 0;
for (const c of cases) {
  const p = predictProba(c.text, model, index).probs;
  maxDiff = Math.max(maxDiff, ...p.map((v, i) => Math.abs(v - c.probs[i])));
  if (p.indexOf(Math.max(...p)) === c.probs.indexOf(Math.max(...c.probs))) sameTop++;
}
console.log(`casos ${cases.length} | mesma categoria ${sameTop}/${cases.length} | maior diferença de probabilidade ${maxDiff.toFixed(4)}`);
