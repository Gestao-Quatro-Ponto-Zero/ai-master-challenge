// Copia data/deals.json e o .sha256 para public/dados/, de onde a web lê no modo local.
import { copyFileSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const WEB = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const ORIGEM = resolve(WEB, '../../data');
const DESTINO = join(WEB, 'public', 'dados');
mkdirSync(DESTINO, { recursive: true });
for (const nome of ['deals.json', 'deals.json.sha256']) {
  const de = join(ORIGEM, nome);
  if (!existsSync(de)) {
    console.error('falta ' + de + ': gere com data/preparar_dados.py (ver docs/runbook.md)');
    process.exit(1);
  }
  copyFileSync(de, join(DESTINO, nome));
}
console.log('dados copiados para ' + DESTINO);
