// Score na ordem da tela: roda a aplicação do domínio (criarServicos) sobre o deals.json e confere
// que o score exibido segue a ordem em que a tela mostra os negócios de cada vendedor (o grupo,
// depois o que há a ganhar). Imprime, por vendedor, a faixa de score de cada grupo, quantos
// vizinhos empatam e quantos sobem (tem de ser 0), os 3 primeiros e os 3 últimos de Zane Levy e de
// Darcel Schlecht e a distribuição do score por faixa de 10.
// Uso: node score_na_ordem.mjs <pasta da solution>   (precisa do npm install da solution)
// Saída bruta: evidencias/score-na-ordem-<data>.txt. Só lê o deals.json.
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

const telaDe = (filtro) => {
  const f = servicos.fila({ filtro, respostas: [] });
  if (!f.ok) throw new Error(f.erro.mensagem);
  return dom.GRUPOS.flatMap((g) => f.valor.blocos[g].map((i) => ({ g, i })));
};
const nome = (g) => textos.grupos[g].titulo;

console.log('# saída bruta de process-log/scripts/score_na_ordem.mjs, ' + new Date().toISOString().slice(0, 16) + 'Z, node ' + process.version + ', sobre solution/data/deals.json (' + p.deals.length + ' negócios, ' + p.abertos.length + ' abertos, referência ' + p.referencia + ')');
console.log('## regra: ordem da tela = grupo (' + dom.GRUPOS.map(nome).join(', ') + '; Siga promovido ao Foque quando o Foque do vendedor está vazio), depois valor esperado (chance × preço; sem data, o preço) desc; score = round(100 × (n − k) ÷ (n − 1)), lista de 1 = 100');

console.log('## por vendedor (na ordem da tela): n, score de cada grupo (primeiro..último), vizinhos com o mesmo score, vizinhos em que o score sobe');
const vendedores = [...new Set(p.abertos.map((d) => d.vendedor))].sort();
let sobeTotal = 0;
let foraDaOrdem = 0;
for (const v of vendedores) {
  const tela = telaDe({ vendedor: v });
  let empates = 0;
  let sobe = 0;
  tela.forEach((x, j) => {
    if (x.i.indicador.posicao?.k !== j + 1) foraDaOrdem += 1;
    if (j === 0) return;
    const antes = tela[j - 1].i.indicador.score;
    if (x.i.indicador.score === antes) empates += 1;
    if (x.i.indicador.score > antes) sobe += 1;
  });
  sobeTotal += sobe;
  const grupos = dom.GRUPOS.map((g) => {
    const s = tela.filter((x) => x.g === g).map((x) => x.i.indicador.score);
    return s.length ? nome(g) + ' ' + s.length + ' [' + s[0] + '..' + s[s.length - 1] + ']' : null;
  }).filter(Boolean);
  console.log('- ' + v + ': n=' + tela.length + ' · ' + grupos.join(' · ') + ' · empates ' + empates + ' · sobe ' + sobe);
}
console.log('## vendedores: ' + vendedores.length + '; vizinhos em que o score sobe: ' + sobeTotal + '; negócios fora da posição k = ordem da tela: ' + foraDaOrdem);

const linha = (x) => nome(x.g) + ' ' + x.i.indicador.score + ' (' + x.i.deal.produto + ', US$ ' + x.i.avaliacao.emJogo + ')';
console.log('## os 3 primeiros e os 3 últimos (grupo, score, produto e preço)');
for (const v of ['Zane Levy', 'Darcel Schlecht']) {
  const tela = telaDe({ vendedor: v });
  console.log('- ' + v + ' (' + tela.length + ' abertos)');
  console.log('    primeiros: ' + tela.slice(0, 3).map(linha).join(' | '));
  console.log('    últimos:   ' + tela.slice(-3).map(linha).join(' | '));
}

const zane = telaDe({ vendedor: 'Zane Levy' });
const doGrupo = (g) => zane.filter((x) => x.g === g);
const maisCaro = [...doGrupo('nutricao')].sort((a, b) => b.i.avaliacao.emJogo - a.i.avaliacao.emJogo)[0];
console.log('## Zane Levy: o primeiro e o mais caro da Nutrição contra o Foque agora');
console.log('    1º da Nutrição:     ' + linha(doGrupo('nutricao')[0]) + ' · ' + doGrupo('nutricao')[0].i.indicador.chanceTexto);
console.log('    Nutrição mais cara: ' + linha(maisCaro) + ' · ' + maisCaro.i.indicador.chanceTexto);
for (const x of zane.filter((y) => y.g === 'foque_agora')) console.log('    Foque agora:        ' + linha(x) + ' · ' + x.i.indicador.chanceTexto);

console.log('## distribuição do score exibido, todos os abertos');
const c = new Map();
for (const { i } of telaDe({})) {
  const s = i.indicador.score;
  const k = s === 100 ? '100' : Math.floor(s / 10) * 10 + '–' + (Math.floor(s / 10) * 10 + 9);
  c.set(k, (c.get(k) ?? 0) + 1);
}
console.log('    ' + [...c.entries()].sort((a, b) => parseInt(a[0], 10) - parseInt(b[0], 10)).map(([k, n]) => k + ': ' + n).join(' | '));
