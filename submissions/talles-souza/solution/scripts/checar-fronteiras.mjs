// Confere as fronteiras dos bounded contexts: um contexto só importa o contrato público
// (index.ts) de outro, e o domínio não faz I/O. Sai com código 1 se achar violação.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const CONTEXTOS = ['pipeline', 'organizacao', 'qualificacao', 'score', 'priorizacao'];
const AREAS = [
  // no domínio, aplicacao e compartilhado também só se usam pelo index
  {
    raiz: 'packages/dominio/src',
    protegidos: [...CONTEXTOS, 'aplicacao', 'compartilhado'],
    semIO: true,
  },
  { raiz: 'apps/api/src', protegidos: CONTEXTOS, semIO: false },
  { raiz: 'apps/web/src', protegidos: CONTEXTOS, semIO: false },
];
const MODULOS_DE_IO = /^(node:|fs$|fs\/|path$|http$|https$|net$|child_process$|os$)/;
const IMPORT =
  /(?:import|export)\s+(?:type\s+)?(?:[^'"]*?\s+from\s+)?['"]([^'"]+)['"]|import\(\s*['"]([^'"]+)['"]\s*\)/g;

function arquivos(pasta) {
  let out = [];
  let itens;
  try {
    itens = readdirSync(pasta);
  } catch {
    return out;
  }
  for (const nome of itens) {
    const p = join(pasta, nome);
    if (statSync(p).isDirectory()) out = out.concat(arquivos(p));
    else if (/\.(ts|tsx)$/.test(nome)) out.push(p);
  }
  return out;
}

const violacoes = [];
for (const area of AREAS) {
  const raizArea = join(RAIZ, area.raiz);
  for (const arq of arquivos(raizArea)) {
    const topo = relative(raizArea, arq).split(sep)[0];
    const ehTeste = /\.(test|spec)\.tsx?$/.test(arq);
    const texto = readFileSync(arq, 'utf8');
    for (const m of texto.matchAll(IMPORT)) {
      const spec = m[1] ?? m[2];
      const onde = relative(RAIZ, arq).split(sep).join('/');
      if (spec.startsWith('@lead-scorer/dominio/') && spec.includes('/src')) {
        violacoes.push(
          onde + ': importa o interno do domínio (' + spec + '); use o ponto de entrada público',
        );
      }
      if (area.semIO && !ehTeste && MODULOS_DE_IO.test(spec)) {
        violacoes.push(onde + ': o domínio não faz I/O (' + spec + ')');
      }
      if (!spec.startsWith('.')) continue;
      const alvo = relative(raizArea, resolve(dirname(arq), spec)).split(sep);
      const alvoTopo = alvo[0];
      if (!area.protegidos.includes(alvoTopo) || alvoTopo === topo) continue;
      const resto = alvo
        .slice(1)
        .join('/')
        .replace(/\.(ts|tsx|js)$/, '');
      if (resto !== '' && resto !== 'index') {
        violacoes.push(
          onde +
            ': importa o interno de "' +
            alvoTopo +
            '" (' +
            spec +
            '); use ' +
            alvoTopo +
            '/index',
        );
      }
    }
  }
}

if (violacoes.length) {
  console.error('Fronteiras violadas (' + violacoes.length + '):\n- ' + violacoes.join('\n- '));
  process.exit(1);
}
console.log('fronteiras ok: nenhum contexto importa o interno de outro; o domínio não faz I/O');
