// Monta a saída do deploy A na Vercel (Build Output API v3) a partir do build da web:
//   .vercel/output/static/                 a web construída (apps/web/dist), servida pela CDN
//   .vercel/output/functions/api.func/     a API: index.mjs (um arquivo só, pelo esbuild), o
//                                          deals.json + .sha256 em data/ e o .vc-config.json
//   .vercel/output/config.json             rotas: /api/* e /health → a função; o resto, estático
// As mesmas rotas estão no vercel.json. Rodado por `npm run build`, depois do build da web.
import { build } from 'esbuild';
import { cpSync, existsSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SAIDA = join(RAIZ, '.vercel', 'output');
const FUNCAO = join(SAIDA, 'functions', 'api.func');
const WEB = join(RAIZ, 'apps', 'web', 'dist');

if (!existsSync(join(WEB, 'index.html'))) {
  console.error('falta ' + WEB + ': rode o build da web antes (npm run build faz os dois)');
  process.exit(1);
}

rmSync(SAIDA, { recursive: true, force: true });
mkdirSync(join(FUNCAO, 'data'), { recursive: true });

cpSync(WEB, join(SAIDA, 'static'), { recursive: true });

await build({
  entryPoints: [join(RAIZ, 'apps', 'api', 'src', 'vercel.ts')],
  outfile: join(FUNCAO, 'index.mjs'),
  bundle: true,
  platform: 'node',
  target: 'node22',
  format: 'esm',
  // o pg tem um require opcional do driver nativo, que não usamos
  external: ['pg-native'],
  // dependências em CommonJS (pg) chamam require(): no ESM ele precisa ser criado
  banner: {
    js: "import { createRequire as __criarRequire } from 'node:module'; const require = __criarRequire(import.meta.url);",
  },
  logLevel: 'warning',
});

for (const nome of ['deals.json', 'deals.json.sha256']) {
  cpSync(join(RAIZ, 'data', nome), join(FUNCAO, 'data', nome));
}

writeFileSync(
  join(FUNCAO, '.vc-config.json'),
  JSON.stringify(
    {
      runtime: 'nodejs22.x',
      handler: 'index.mjs',
      launcherType: 'Nodejs',
      shouldAddHelpers: false,
      maxDuration: 10,
    },
    null,
    2,
  ) + '\n',
);

writeFileSync(
  join(SAIDA, 'config.json'),
  JSON.stringify(
    {
      version: 3,
      routes: [
        { src: '^/api(?:/.*)?$', dest: '/api' },
        { src: '^/health$', dest: '/api' },
        { handle: 'filesystem' },
        { src: '^/(.*)$', dest: '/index.html' },
      ],
    },
    null,
    2,
  ) + '\n',
);

console.log('saída da Vercel em ' + SAIDA + ' (estático + função api)');
