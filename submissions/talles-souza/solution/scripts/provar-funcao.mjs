// Prova a função da Vercel construída por `npm run build`: importa o bundle de
// .vercel/output/functions/api.func/, serve por http local e confere /health, a fila e o 404.
// Uso: npm run build && npm run test:funcao (sem DATABASE_URL: deals.json + memória).
import { existsSync } from 'node:fs';
import { createServer } from 'node:http';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const FUNCAO = join(RAIZ, '.vercel', 'output', 'functions', 'api.func', 'index.mjs');
if (!existsSync(FUNCAO)) {
  console.error('falta ' + FUNCAO + ': rode npm run build antes');
  process.exit(1);
}
const handler = (await import(pathToFileURL(FUNCAO).href)).default;
const servidor = createServer(handler).listen(0, '127.0.0.1');
await new Promise((r) => servidor.once('listening', r));
const base = 'http://127.0.0.1:' + servidor.address().port;
const saude = await (await fetch(base + '/health')).json();
const fila = await fetch(base + '/api/priorizacao/fila', {
  method: 'POST',
  headers: { 'content-type': 'application/json', 'x-real-ip': '10.1.1.1' },
  body: JSON.stringify({ filtro: {} }),
});
const corpo = await fila.json();
const nada = await fetch(base + '/api/nao-existe');
const r = {
  saude: saude.dados,
  fila: fila.status,
  porBloco: corpo.contadores?.porBloco,
  naoExiste: nada.status,
};
console.log(JSON.stringify(r));
const ok =
  saude.dados?.total === 8800 &&
  fila.status === 200 &&
  corpo.contadores?.total === 2089 &&
  nada.status === 404;
servidor.close();
if (!ok) {
  console.error('a função construída não respondeu como o esperado');
  process.exitCode = 1;
} else console.log('função ok');
