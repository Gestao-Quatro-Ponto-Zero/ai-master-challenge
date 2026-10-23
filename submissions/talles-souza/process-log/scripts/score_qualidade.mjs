// Score de qualidade: roda a aplicação do domínio (criarServicos) sobre o deals.json e mede o score
// novo (a qualidade: a chance da faixa de idade ÷ a melhor faixa, × 100, mais as respostas do
// vendedor), separado da ordem da tela (grupo, depois valor esperado) e do preço. Imprime a parte
// do dado por faixa (chances do motor), o score por grupo de cada vendedor sem respostas, as
// checagens do aceite (Nutrição ≤ 15, Siga ≥ Foque, preço não muda o score, ordem pelo valor
// esperado) e os cartões reais de Zane Levy e Darcel Schlecht, com o porquê e o efeito de um "Sim".
// Uso: node score_qualidade.mjs <pasta da solution>   (precisa do npm install da solution)
// Saída bruta: evidencias/score-qualidade-<data>.txt. Só lê o deals.json.
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
const servicos = dom.criarServicos({ pipeline: p, checksum: 'medição' });
const textos = servicos.textos();
const motor = servicos.motor();
const politica = servicos.politica();
const metodo = servicos.metodo();
const nome = (g) => textos.grupos[g].titulo;
const pct = (x) => (100 * x).toFixed(1) + '%';

console.log('# saída bruta de process-log/scripts/score_qualidade.mjs, ' + new Date().toISOString().slice(0, 16) + 'Z, node ' + process.version + ', sobre solution/data/deals.json (' + p.deals.length + ' negócios, ' + p.abertos.length + ' abertos, referência ' + p.referencia + ')');
const cfg = dom.configQualidadePadrao;
console.log('## regra: score = round(100 × chance da faixa de idade ÷ maior chance entre as faixas) (motor, conversão ' + motor.config.conversao + ') + ' + cfg.porSim + ' por "Sim", ' + cfg.porNao + ' por "Não", limite 0–100; sem data: "—" sem resposta, ' + cfg.semDataBase + ' com resposta. O preço não entra. Ordem da tela: grupo, depois valor esperado (sem data: preço).');

const faixas = dom.chancesDaIdade(motor);
const maxima = Math.max(...faixas.map((f) => f.chance));
const replay = servicos.chance();
console.log('## parte do dado por faixa de idade (chance do motor, a maior = ' + pct(maxima) + '; ao lado, o que fechou de fato no replay ' + replay.corte + ' → ' + replay.referencia + ', que é o que a frase mostra)');
for (const f of faixas) {
  const r = replay.faixas.find((x) => x.rotulo === f.rotulo);
  console.log('  ' + f.rotulo.padEnd(18) + ' chance ' + pct(f.chance).padStart(6) + ' → score ' + String(dom.parteDoDado(f.chance, maxima)).padStart(3) + ' · fecharam ' + (r ? r.ganhos + '/' + r.n + ' = ' + pct(r.taxa ?? 0) : 'sem replay'));
}

const telaDe = (filtro, respostas = []) => {
  const f = servicos.fila({ filtro, respostas });
  if (!f.ok) throw new Error(f.erro.mensagem);
  return dom.GRUPOS.flatMap((g) => f.valor.blocos[g].map((i) => ({ g, i })));
};

console.log('## por vendedor, sem respostas: score [mín..máx] de cada grupo da tela');
const vendedores = [...new Set(p.abertos.map((d) => d.vendedor))].sort();
let nutricaoAcima = 0;
let nutricaoTotal = 0;
let sigaAbaixoDeFoque = 0;
let foraDaOrdem = 0;
let semDataComScore = 0;
let semDataTotal = 0;
for (const v of vendedores) {
  const tela = telaDe({ vendedor: v });
  const doGrupo = (g) => tela.filter((x) => x.g === g);
  const faixa = (g) => {
    const s = doGrupo(g).map((x) => x.i.indicador.score).filter((n) => n !== null);
    return s.length ? [Math.min(...s), Math.max(...s)] : null;
  };
  // ordem dentro do grupo: valor esperado (sem data: preço) nunca sobe
  for (const g of dom.GRUPOS) {
    const valores = doGrupo(g).map((x) => x.i.avaliacao.esperado ?? x.i.avaliacao.emJogo);
    valores.forEach((val, j) => {
      if (j > 0 && val > valores[j - 1] + 1e-9) foraDaOrdem += 1;
    });
  }
  for (const x of tela) {
    if (x.i.bloco === 'nutricao') {
      nutricaoTotal += 1;
      if ((x.i.indicador.score ?? 0) > 15) nutricaoAcima += 1;
    }
    if (x.i.bloco === 'sem_inicio') {
      semDataTotal += 1;
      if (x.i.indicador.score !== null) semDataComScore += 1;
    }
  }
  const doBloco = (b) => tela.filter((x) => x.i.bloco === b).map((x) => x.i.indicador.score);
  const sigaMin = Math.min(...doBloco('siga_no_ritmo'));
  const foqueMax = Math.max(...doBloco('foque_agora'));
  if (Number.isFinite(sigaMin) && Number.isFinite(foqueMax) && sigaMin < foqueMax) sigaAbaixoDeFoque += 1;
  const partes = dom.GRUPOS.map((g) => {
    const n = doGrupo(g).length;
    if (!n) return null;
    const fx = faixa(g);
    return nome(g) + ' ' + n + (fx ? ' [' + fx[0] + '..' + fx[1] + ']' : ' [—]');
  }).filter(Boolean);
  console.log('- ' + v + ': n=' + tela.length + ' · ' + partes.join(' · '));
}
console.log('## checagens (sem respostas)');
console.log('  Nutrição com score > 15: ' + nutricaoAcima + ' de ' + nutricaoTotal);
console.log('  vendedores com algum Siga no ritmo abaixo de algum Foque agora (pela idade): ' + sigaAbaixoDeFoque + ' de ' + vendedores.length);
console.log('  sem data com score (devia ser "—"): ' + semDataComScore + ' de ' + semDataTotal);
console.log('  vizinhos em que o valor esperado (sem data: preço) sobe dentro do grupo: ' + foraDaOrdem);

// o preço não entra no score: o mesmo negócio com o preço × 10 tem o mesmo score
let precoMudou = 0;
const amostra = p.abertos.filter((d) => d.idadeDias !== null);
for (const d of amostra) {
  const a = servicos.avaliar({ dealId: d.id });
  if (!a.ok) continue;
  const av = a.valor.avaliacao;
  const base = dom.classificar(d, av, politica, metodo, null);
  const caro = dom.classificar(
    { ...d, precoTabela: d.precoTabela * 10 },
    { ...av, emJogo: av.emJogo * 10, esperado: av.esperado === null ? null : av.esperado * 10 },
    politica,
    metodo,
    null,
  );
  if (base.indicador.score !== caro.indicador.score) precoMudou += 1;
}
console.log('  negócios com data (de ' + amostra.length + ') cujo score muda com o preço × 10: ' + precoMudou);

// a receita esperada (chance do motor × preço; o score não entra nela)
const receita = (filtro) => {
  const f = servicos.fila({ filtro, respostas: [] });
  if (!f.ok) throw new Error(f.erro.mensagem);
  return f.valor.receita;
};
const brl = (v) => 'US$ ' + Math.round(v).toLocaleString('pt-BR');
console.log('## receita esperada dos abertos (chance do motor, conversão ' + motor.config.conversao + ', × preço de tabela; o score não entra)');
console.log('  todos: ' + brl(receita({}).total) + ' (' + receita({}).semEstimativa + ' sem data fora da conta) · Central: ' + brl(receita({ regiao: 'Central' }).total) + ' · Zane Levy: ' + brl(receita({ vendedor: 'Zane Levy' }).total) + ' · Darcel Schlecht: ' + brl(receita({ vendedor: 'Darcel Schlecht' }).total));
const f4150 = faixas.find((f) => f.rotulo === '41 a 50 dias');
if (f4150) console.log('  exemplo: 45 dias (chance ' + f4150.chance.toFixed(4) + ') × US$ 4.821 = ' + brl(f4150.chance * 4821));

// os cartões reais
const cartao = (x) => {
  const ind = x.i.indicador;
  const acao = x.i.bloco === 'nutricao' ? textos.grupos.nutricao.acao : x.i.proximaAcao.texto;
  return [
    '  [' + nome(x.g) + '] ' + x.i.deal.id,
    '    ' + ind.numero,
    '    ' + acao,
    '    ' + ind.emJogo + ' · ' + politica.textos.score.verPorque,
    '    ver por quê:',
    ...ind.porqueScore.map((l) => '      - ' + l),
  ].join('\n');
};
const primeiroDe = (tela, g) => tela.find((x) => x.g === g);
console.log('## cartões reais (o primeiro de cada grupo na tela, sem respostas)');
const zane = telaDe({ vendedor: 'Zane Levy' });
for (const g of ['foque_agora', 'siga_no_ritmo', 'nutricao']) {
  const x = primeiroDe(zane, g);
  console.log('- Zane Levy · ' + nome(g) + (x ? '\n' + cartao(x) : ': vazio'));
}
const darcel = telaDe({ vendedor: 'Darcel Schlecht' });
for (const g of ['sem_inicio', 'nutricao']) {
  const x = primeiroDe(darcel, g);
  console.log('- Darcel Schlecht · ' + nome(g) + (x ? '\n' + cartao(x) : ': vazio'));
}

// responder muda o score; a ordem da tela não muda
console.log('## responder: o score muda, a ordem da tela não');
const agora = '2026-10-23T12:00:00.000Z';
const responderTodas = (dealId, valor) =>
  metodo.perguntas.reduce((r, q) => dom.responder(r, dealId, metodo, q.id, valor, agora).valor, null);
for (const [quem, g] of [['Zane Levy', 'foque_agora'], ['Zane Levy', 'siga_no_ritmo'], ['Darcel Schlecht', 'sem_inicio']]) {
  const tela = telaDe({ vendedor: quem });
  const x = primeiroDe(tela, g);
  if (!x) continue;
  const umSim = dom.responder(null, x.i.deal.id, metodo, 'decisor', 'sim', agora).valor;
  const indicador = (r) => {
    const it = servicos.item({ dealId: x.i.deal.id, respostas: r });
    if (!it.ok) throw new Error(it.erro.mensagem);
    return it.valor.indicador;
  };
  const ordemAntes = tela.map((y) => y.i.deal.id).join(',');
  const ordemDepois = telaDe({ vendedor: quem }, [umSim]).map((y) => y.i.deal.id).join(',');
  console.log('- ' + quem + ' · ' + nome(g) + ' ' + x.i.deal.id + ': sem resposta ' + x.i.indicador.numero + ' → 1 "Sim" (decisor) ' + indicador(umSim).numero + ' → 3 "Sim" ' + indicador(responderTodas(x.i.deal.id, 'sim')).numero + ' → 3 "Não" ' + indicador(responderTodas(x.i.deal.id, 'nao')).numero + ' · ordem da tela igual depois do "Sim": ' + (ordemAntes === ordemDepois));
  console.log('    ver por quê com 1 "Sim": ' + indicador(umSim).porqueScore.join(' | '));
}
