// Score relativo: roda a aplicação do domínio (criarServicos) sobre o deals.json e mede o score
// exibido, que é a posição do negócio na lista aberta do vendedor pelo valor esperado (chance do
// motor × preço; sem data de início, só o preço). Imprime a distribuição por região, a dispersão
// por vendedor (quantos scores distintos, mínimo e máximo), a comparação com o score absoluto
// (chance × 100) e cartões reais de um vendedor de East/West e de um da Central.
// Uso: node score_relativo.mjs <pasta da solution>   (precisa do npm install da solution)
// Saída bruta: evidencias/score-relativo-<data>.txt. Só lê o deals.json.
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
const org = servicos.organizacao();

const itensDe = (filtro) => {
  const f = servicos.fila({ filtro, respostas: [] });
  if (!f.ok) throw new Error(f.erro.mensagem);
  return dom.GRUPOS.flatMap((g) => f.valor.blocos[g]);
};
const rotulo = (s) => (s === null ? 'sem score' : s === 100 ? '100' : Math.floor(s / 10) * 10 + '–' + (Math.floor(s / 10) * 10 + 9));
const ordemRotulo = (r) => (r === 'sem score' ? 1000 : parseInt(r, 10));
const faixas10 = (scores) => {
  const c = new Map();
  for (const s of scores) c.set(rotulo(s), (c.get(rotulo(s)) ?? 0) + 1);
  return [...c.entries()]
    .sort((a, b) => ordemRotulo(a[0]) - ordemRotulo(b[0]))
    .map(([k, n]) => k + ': ' + n)
    .join(' | ');
};

console.log('# saída bruta de process-log/scripts/score_relativo.mjs, ' + new Date().toISOString().slice(0, 16) + 'Z, node ' + process.version + ', sobre solution/data/deals.json (' + p.deals.length + ' negócios, ' + p.abertos.length + ' abertos, referência ' + p.referencia + ')');
console.log('## regra: score = round(100 × (n − k + 1) ÷ n), k = posição na lista aberta do vendedor pelo valor esperado (chance do motor × preço de tabela) desc, empate pelo preço desc; sem data de início, o valor é só o preço');

console.log('## distribuição por região: score exibido (posição) × score absoluto (chance × 100)');
for (const regiao of [undefined, ...org.regioes]) {
  const itens = itensDe(regiao ? { regiao } : {});
  console.log('- ' + (regiao ?? 'todos') + ' (' + itens.length + ' abertos)');
  console.log('    exibido:  ' + faixas10(itens.map((i) => i.indicador.score)));
  console.log('    absoluto: ' + faixas10(itens.map((i) => (i.avaliacao.score ? i.avaliacao.score.score : null))));
}

console.log('## por vendedor: abertos, sem data, scores distintos, mínimo / mediana / máximo');
const resumo = [];
let semScore = 0;
for (const v of org.vendedores) {
  const itens = itensDe({ vendedor: v.nome });
  if (itens.length === 0) {
    console.log('- ' + v.nome + ' (' + v.regiao + '): sem negócio aberto, nada a mostrar');
    continue;
  }
  semScore += itens.filter((i) => i.indicador.score === null).length;
  const s = itens.map((i) => i.indicador.score).sort((a, b) => a - b);
  const semData = itens.filter((i) => i.avaliacao.idadeDias === null).length;
  const distintos = new Set(s).size;
  resumo.push({ v, itens });
  console.log('- ' + v.nome + ' (' + v.regiao + '): ' + itens.length + ' abertos, ' + semData + ' sem data, ' + distintos + ' distintos, ' + s[0] + ' / ' + s[Math.floor(s.length / 2)] + ' / ' + s[s.length - 1]);
}
console.log('## abertos sem score exibido (nos vendedores com lista): ' + semScore);

const cartao = (i) =>
  '    [' + i.bloco + '] ' + i.deal.id + ' · ' + i.indicador.numero + ' · ' + i.indicador.motivo + ' | detalhe: ' + i.indicador.posicaoTexto + '; ' + i.indicador.chanceTexto;
console.log('## cartões reais: o primeiro, o do meio e o último da lista (grupo entre colchetes)');
const maior = (rs) => [...rs].sort((a, b) => b.itens.length - a.itens.length)[0];
for (const r of [maior(resumo.filter((x) => x.v.regiao !== 'Central')), maior(resumo.filter((x) => x.v.regiao === 'Central'))]) {
  const ordem = [...r.itens].sort((a, b) => a.indicador.posicao.k - b.indicador.posicao.k);
  console.log('- ' + r.v.nome + ' (' + r.v.regiao + ', ' + r.itens.length + ' abertos)');
  for (const i of [ordem[0], ordem[Math.floor(ordem.length / 2)], ordem[ordem.length - 1]]) console.log(cartao(i));
}
