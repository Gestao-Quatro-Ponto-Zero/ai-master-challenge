// Replay de 92 dias e grupos por idade, iguais aos da ferramenta
// (packages/dominio/src/score: medirChance; packages/dominio/src/priorizacao/politica.provisoria.config.ts).
// Só lê o deals.json. Usado por receita_esperada.mjs.
import { readFileSync } from 'node:fs';
export const DIA = 864e5;
export const dia = (s) => Date.parse(s + 'T00:00:00Z');
export function carregar(caminho) {
  const d = JSON.parse(readFileSync(caminho, 'utf8'));
  const fim = dia(d.referencia), corte = fim - 92 * DIA;
  const tetos = [10, 20, 30, 40, 50, 60, 90, null]; let de = 0;
  const fx = tetos.map((t) => { const f = { de, ate: t, n: 0, g: 0 }; de = (t ?? de) + 1; return f; });
  const fd = (i) => fx.find((f) => f.ate === null || i <= f.ate);
  const pop = [];
  for (const x of d.deals) {
    if (!x.engage_date) continue;
    const e = dia(x.engage_date), c = x.close_date ? dia(x.close_date) : null;
    if (e > corte || (c !== null && c <= corte)) continue;
    const f = fd(Math.round((corte - e) / DIA)); f.n++;
    const w = x.deal_stage === 'Won' && c !== null && c <= fim; if (w) f.g++;
    pop.push({ x, f, w, idc: Math.round((corte - e) / DIA) });
  }
  const taxa = (i) => { const f = fd(i); return f.n ? f.g / f.n : null; };
  const grupo = (i) => (i === null ? 'ainda_nao_comecou' : i <= 40 ? 'siga' : i <= 60 ? 'foque' : 'nutricao');
  return { d, fim, corte, fx, fd, pop, taxa, grupo };
}
