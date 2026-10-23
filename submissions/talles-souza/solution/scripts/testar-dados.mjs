// Roda os testes da camada de dados (Python, pytest) pelo uv, se ele existir na máquina.
// Os testes comparam contagens com o CSV do Kaggle: sem CRM_DADOS apontando para a pasta,
// o pytest os marca como pulados. Sem uv, este script avisa e não falha.
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const PASTA_DATA = join(RAIZ, 'data');
const PADRAO = resolve(RAIZ, '../../../../dados/crm-sales-predictive-analytics');
const crm = process.env.CRM_DADOS ?? (existsSync(join(PADRAO, 'sales_pipeline.csv')) ? PADRAO : '');

const uv = spawnSync('uv', ['--version'], {
  encoding: 'utf8',
  shell: process.platform === 'win32',
});
if (uv.status !== 0) {
  console.log('test:dados pulado: uv não encontrado (ver docs/runbook.md)');
  process.exit(0);
}
if (!crm)
  console.log(
    'test:dados: CRM_DADOS não definido; os testes de contagem serão pulados pelo pytest',
  );

const r = spawnSync(
  'uv',
  [
    'run',
    '--no-project',
    '--python',
    '3.12',
    '--with',
    'pandas==3.1.0',
    '--with',
    'pytest==8.4.2',
    'python',
    '-X',
    'utf8',
    '-m',
    'pytest',
    '-q',
    '-p',
    'no:cacheprovider',
    'test_preparar_dados.py',
  ],
  {
    cwd: PASTA_DATA,
    stdio: 'inherit',
    env: { ...process.env, CRM_DADOS: crm },
    shell: process.platform === 'win32',
  },
);
process.exit(r.status ?? 1);
