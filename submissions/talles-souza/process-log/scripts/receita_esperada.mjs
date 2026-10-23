// Receita esperada dos negócios abertos (chance da faixa de idade no replay × preço de tabela),
// o backtest dentro da amostra e quanto dos ganhos do 4º trimestre veio de negócios que entraram depois do corte.
// Uso: node receita_esperada.mjs <solution/data/deals.json>
// Saída bruta: evidencias/receita-esperada.txt. Só lê o deals.json.
import { carregar, dia } from './replay.mjs';
const { d, corte, pop, taxa, grupo } = carregar(process.argv[2]);
const R = {};
for (const x of d.deals.filter((x) => x.aberto)) {
  const k = grupo(x.idade_dias); R[k] ??= { n: 0, tabela: 0, esperada: 0 };
  R[k].n++; R[k].tabela += x.sales_price; if (x.idade_dias !== null) R[k].esperada += x.sales_price * taxa(x.idade_dias);
}
let t = 0; for (const [k, v] of Object.entries(R)) { t += v.esperada; console.log(k, 'n=' + v.n, 'tabela US$', Math.round(v.tabela), 'esperada US$', Math.round(v.esperada)); }
console.log('total esperada US$', Math.round(t));
const won = d.deals.filter((x) => x.deal_stage === 'Won');
console.log('Won:', won.length, 'close_value != sales_price (dif > US$1):', won.filter((x) => Math.abs(x.close_value - x.sales_price) > 1).length, '| razao media close/price:', (won.reduce((s, x) => s + x.close_value / x.sales_price, 0) / won.length).toFixed(3));
let prev = 0, real = 0; for (const p of pop) { prev += p.x.sales_price * p.f.g / p.f.n; if (p.w) real += p.x.close_value; }
console.log('## backtest dentro da amostra: populacao = abertos em 30/09 (engajados ate o corte, sem fechamento ate o corte) n=' + pop.length, '| alvo = close_value dos que ganharam ate 31/12 | previsto US$', Math.round(prev), '| realizado US$', Math.round(real));
const q4 = won.filter((x) => dia(x.close_date) > corte); const novos = q4.filter((x) => dia(x.engage_date) > corte);
console.log('ganhos 01/10-31/12: n=' + q4.length, 'US$', Math.round(q4.reduce((s, x) => s + x.close_value, 0)), '| engajados depois de 30/09: n=' + novos.length, 'US$', Math.round(novos.reduce((s, x) => s + x.close_value, 0)));
// Ordem dentro do Foque: por preço × por receita esperada
const foque = d.deals.filter((x) => x.aberto && grupo(x.idade_dias) === 'foque');
const fmt = (x) => `${x.opportunity_id} ${x.idade_dias}d US$${x.sales_price} esp ${Math.round(x.sales_price * taxa(x.idade_dias))}`;
const porPreco = [...foque].sort((a, b) => b.sales_price - a.sales_price || a.idade_dias - b.idade_dias).slice(0, 5).map(fmt);
const porEsp = [...foque].sort((a, b) => b.sales_price * taxa(b.idade_dias) - a.sales_price * taxa(a.idade_dias) || a.idade_dias - b.idade_dias).slice(0, 5).map(fmt);
console.log('## Foque, top 5 por preço:', porPreco.join(' | '));
console.log('## Foque, top 5 por valor esperado:', porEsp.join(' | '));
