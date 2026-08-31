import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const viteEntry = join(dirname(require.resolve('vite')), '..', '..', 'bin', 'vite.js');
const apiPort = String(process.env.API_PORT ?? 3001);
const webPort = String(process.env.WEB_PORT ?? 3000);
const children = [
  spawn(process.execPath, ['server/index.mjs'], { stdio: 'inherit', env: { ...process.env, PORT: apiPort } }),
  spawn(process.execPath, [viteEntry, '--host', '127.0.0.1', '--port', webPort], { stdio: 'inherit', env: { ...process.env, API_PORT: apiPort } }),
];

function shutdown(signal = 'SIGTERM') {
  children.forEach((child) => child.kill(signal));
  process.exit();
}

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));
children.forEach((child) => child.on('exit', (code) => {
  if (code && code !== 0) shutdown();
}));
children.forEach((child) => child.on('error', (error) => {
  console.error(`Não foi possível iniciar a aplicação: ${error.message}`);
  shutdown();
}));
