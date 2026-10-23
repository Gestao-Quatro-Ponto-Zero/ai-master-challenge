// Motor de pontos: roda o próprio motor do domínio (packages/dominio/src/score/motor.ts) sobre o
// deals.json e imprime o que ele mediu: os recortes do replay, cada fator (AUC sozinho na
// validação, quanto subiria o AUC, pontos por categoria no treino e na validação), os escolhidos
// e os descartados, o AUC do score × o AUC só da idade, a calibração da receita nas duas
// conversões de pontos em chance e o score dos abertos de hoje.
// Uso: node motor_de_pontos.mjs <pasta da solution>   (precisa do npm install da solution)
// Saída bruta: evidencias/motor-de-pontos-<data>.txt. Só lê o deals.json.
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join, resolve } from 'node:path';

const raiz = resolve(process.argv[2] ?? '.');
const { build } = createRequire(join(raiz, 'package.json'))('esbuild');
const pacote = await build({
  entryPoints: [join(raiz, 'packages/dominio/src/index.ts')],
  bundle: true,
  write: false,
  format: 'esm',
  platform: 'node',
  absWorkingDir: raiz,
});
const dom = await import(
  'data:text/javascript;base64,' + Buffer.from(pacote.outputFiles[0].text).toString('base64')
);
const lido = dom.lerPipeline(JSON.parse(readFileSync(join(raiz, 'data/deals.json'), 'utf8')));
if (!lido.ok) throw new Error(lido.erro.mensagem);
const p = lido.valor;
const faixas = dom.politicaAtiva.chance.faixas;
const config = dom.configMotorPadrao;

const t0 = performance.now();
const { motor, pontuar } = dom.medirMotor(p.deals, p.referencia, faixas, config);
const ms = performance.now() - t0;
const de3 = (x) => (x === null || x === undefined ? '–' : x.toFixed(3));
const de4 = (x) => (x === null || x === undefined ? '–' : (x >= 0 ? '+' : '') + x.toFixed(4));
const us = (x) => 'US$ ' + Math.round(x).toLocaleString('pt-BR');

console.log('# saída bruta de process-log/scripts/motor_de_pontos.mjs, ' + new Date().toISOString().slice(0, 16) + 'Z, node ' + process.version + ', sobre solution/data/deals.json (' + p.deals.length + ' negócios, referência ' + p.referencia + ')');
console.log('## config: ' + JSON.stringify(config));
console.log('## recortes do replay');
for (const [nome, r] of [['treino', motor.treino], ['validação', motor.validacao]])
  console.log('  ' + nome + ': abertos em ' + r.corte + ' n=' + r.n + ' | ganharam até ' + r.ate + ': ' + r.ganhos + ' (' + de3(r.taxa) + ')');
console.log('  taxa base do score (recorte mais recente): ' + de3(motor.taxaBase));
console.log('## fatores (AUC sozinho na validação, medido onde o fator tem dado; ganho = quanto subiria o AUC do score no passo em que entrou ou em que a seleção parou)');
for (const f of motor.fatores) {
  console.log('- ' + f.id + ' [' + f.tipo + '] ' + f.motivo + (f.passo ? ' (passo ' + f.passo + ', AUC do score ' + de3(f.aucAoEntrar) + ')' : '') + ' | AUC sozinho ' + de3(f.aucValidacao) + ' | ganho ' + de4(f.ganhoAuc));
  console.log('    treino:    ' + f.categoriasTreino.map((c) => c.rotulo + ' n=' + c.n + ' g=' + c.ganhos + ' ' + c.pontos + (c.motivo === 'pontua' ? '' : ' [' + c.motivo + ']')).join(' | '));
  if (f.entrou)
    console.log('    pesos finais (validação): ' + f.categorias.map((c) => c.rotulo + ' n=' + c.n + ' taxa=' + de3(c.taxa) + ' ' + c.pontos + (c.motivo === 'pontua' ? '' : ' [' + c.motivo + ']')).join(' | '));
}
console.log('## escolhidos: ' + motor.escolhidos.join(', '));
console.log('## descartados: ' + motor.fatores.filter((f) => !f.entrou).map((f) => f.id + ' (' + f.motivo + ')').join(', '));
console.log('## AUC do score na validação: ' + de3(motor.aucScore) + ' | AUC só da idade: ' + de3(motor.aucIdade));

// calibração: os abertos em C2, pesos finais, receita prevista × realizada até R
const dia = (s) => Date.parse(s + 'T00:00:00Z');
const C2 = dia(motor.validacao.corte);
const R = dia(motor.validacao.ate);
const idade = motor.fatores.find((f) => f.id === 'idade');
const tetos = faixas.filter((f) => f.ateDias !== null).map((f) => f.ateDias);
const logit = (q) => Math.log(q / (1 - q));
const base = motor.taxaBase;
let porLog = 0;
let porRazao = 0;
let realizado = 0;
let n = 0;
for (const d of p.deals) {
  if (d.dataEngajamento === null) continue;
  const fechou = d.dataFechamento === null ? null : dia(d.dataFechamento);
  if (dia(d.dataEngajamento) > C2 || (fechou !== null && fechou <= C2)) continue;
  const dias = Math.round((C2 - dia(d.dataEngajamento)) / 86_400_000);
  const i = tetos.findIndex((t) => dias <= t);
  const cat = idade.categorias.find((c) => c.chave === 'F' + ((i === -1 ? tetos.length : i) + 1));
  const pts = motor.escolhidos.length === 1 && idade.entrou ? (cat?.pontos ?? 0) : NaN;
  n++;
  porLog += d.precoTabela / (1 + Math.exp(-(logit(base) + pts / config.escala)));
  porRazao += d.precoTabela * Math.min(1, base * Math.exp(pts / config.escala));
  if (d.estagio === 'Won' && fechou <= R) realizado += d.valorFechamento ?? 0;
}
console.log('## calibração da receita no recorte mais recente (dentro da amostra; pesos finais; só vale com a idade como único fator)');
console.log('  abertos em ' + motor.validacao.corte + ': ' + n + ' | realizado até ' + motor.validacao.ate + ': ' + us(realizado));
console.log('  conversão log-odds (logit(base) + pontos/10): previsto ' + us(porLog) + ' (' + ((porLog / realizado - 1) * 100).toFixed(1) + '%)');
console.log('  conversão razão (base × e^(pontos/10)): previsto ' + us(porRazao) + ' (' + ((porRazao / realizado - 1) * 100).toFixed(1) + '%)');
console.log('  chance por faixa: ' + idade.categorias.map((c) => c.rotulo + ' taxa ' + de3(c.taxa) + ' → log-odds ' + de3(1 / (1 + Math.exp(-(logit(base) + c.pontos / 10)))) + ' / razão ' + de3(Math.min(1, base * Math.exp(c.pontos / 10)))).join(' | '));

// o score dos abertos de hoje
const scores = p.abertos.map((d) => pontuar(d));
const com = scores.filter((s) => s !== null);
const hist = {};
for (const s of com) {
  const k = Math.min(90, Math.floor(s.score / 10) * 10);
  hist[k] = (hist[k] ?? 0) + 1;
}
console.log('## score dos abertos em ' + p.referencia + ' (conversão em uso: ' + config.conversao + '): ' + com.length + ' com score, ' + (scores.length - com.length) + ' sem data de início (sem score)');
console.log('  por faixa de score: ' + Object.entries(hist).map(([k, v]) => k + '–' + (Number(k) + 9) + ': ' + v).join(' | '));
const receitaHoje = p.abertos.reduce((soma, d, i) => soma + (scores[i] ? scores[i].chance * d.precoTabela : 0), 0);
console.log('  receita esperada dos abertos de hoje (chance da nota × preço de tabela): ' + us(receitaHoje));
const servicos = dom.criarServicos({ pipeline: p, checksum: 'evidencia' });
const fila = servicos.fila({ filtro: {}, respostas: [] }).valor;
const central = servicos.fila({ filtro: { regiao: 'Central' }, respostas: [] }).valor;
console.log('  mesma conta pela fila da aplicação: ' + us(fila.receita.total) + ' | só a Central (todos acima de 60 dias ou sem data): ' + us(central.receita.total));
const de_novo = dom.medirMotor(p.deals, p.referencia, faixas, config);
console.log('## reproduzível: segunda medição igual à primeira = ' + (JSON.stringify(de_novo.motor) === JSON.stringify(motor)) + ' | tempo da medição: ' + Math.round(ms) + ' ms');
